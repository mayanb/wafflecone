from ics.models import *
from zappa.async import task
from django.db.models import F, Sum, Q
from datetime import datetime, timedelta
from ics.utilities import last_week_range, last_month_range

# Use simplejson to handle serializing Decimal objects
import simplejson as json
import os

from ics.v10.calculated_fields_serializers import FlatTaskSerializer
from ics.v10.serializers import BasicGoalSerializer, AlertInputSerializer


def create_alerts(team, objects, serializer, alert_type):
	if len(objects) == 0:
		return

	serialized_objects = map(lambda t: serializer(t).data, objects)
	alerts = []
	for userprofile in UserProfile.objects.filter(team=team).all():
		alert = Alert(
			alert_type=alert_type,
			variable_content=json.dumps(serialized_objects),
			userprofile=userprofile,
			is_displayed=True,
		)
		alerts.append(alert)
	Alert.objects.bulk_create(alerts)


def is_local():
	return 'WAFFLE_ENVIRONMENT' not in os.environ or os.environ['WAFFLE_ENVIRONMENT'] not in ['staging', 'production']


def is_dandelion(team):
	return team.id in [1, 2]


@task
def check_flagged_tasks_alerts(task):
	if is_local():
		return

	if not task.was_flag_changed:
		return

	team = task.process_type.team_created_by

	end_date = datetime.today() + timedelta(days=1)
	start_date = datetime.today() - timedelta(days=2)
	recently_changed = Task.objects.filter(
		process_type__team_created_by=team.id,
		flag_update_time__date__range=(start_date, end_date),
	) \
		.select_related('process_type', 'product_type') \
		.prefetch_related('items')

	create_alerts(team, recently_changed.filter(is_flagged=True), FlatTaskSerializer, 'ft')
	create_alerts(team, recently_changed.filter(is_flagged=False), FlatTaskSerializer, 'ut')


@task
def check_goals_alerts(task):
	if is_local():
		return

	team = task.process_type.team_created_by
	queryset = Goal.objects.filter(userprofile__team=team)

	if queryset.filter(
			process_type=task.process_type.id,
			product_types__id=task.product_type.id,
			is_trashed=False,
	).count() == 0:
		return

	complete_goals = []
	incomplete_goals = []

	for goal in queryset:
		start, end = last_week_range() if goal.timerange == 'w' else last_month_range()

		if (goal.is_trashed and goal.trashed_time < end) or goal.created_at > start:
			continue

		product_types = ProductType.objects.filter(goal_product_types__goal=goal)
		amount = Item.objects.filter(
			creating_task__process_type=goal.process_type,
			creating_task__product_type__in=product_types,
			creating_task__is_trashed=False,
			creating_task__created_at__range=(start, end),
		).aggregate(amount_sum=Sum('amount'))['amount_sum']

		if amount >= goal.goal:
			complete_goals.append(goal)
		else:
			incomplete_goals.append(goal)

	create_alerts(team, complete_goals, BasicGoalSerializer, 'cg')
	create_alerts(team, incomplete_goals, BasicGoalSerializer, 'ig')


@task
def check_anomalous_inputs_alerts(input):
	if is_local():
		return

	team = input.task.process_type.team_created_by

	if not is_dandelion(team):
		return

	if input.task.product_type == input.input_item.creating_task.product_type:
		return

	# for each input, if any of the items' creating tasks have a different product type from the input task
	end_date = datetime.today() + timedelta(days=1)
	start_date = datetime.today() - timedelta(days=5)
	queryset = Input.objects.filter(
		task__process_type__team_created_by=team,
		task__is_trashed=False,
		input_item__creating_task__is_trashed=False,
		task__created_at__date__range=(start_date, end_date)
	) \
		.exclude(Q(input_item__creating_task__product_type__id=F('task__product_type__id'))) \
		.select_related('task', 'task__process_type', 'task__process_type', 'input_item', 'input_item__creating_task')
	create_alerts(team, queryset.all(), AlertInputSerializer, 'ai')
