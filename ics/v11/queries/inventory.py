from ics.models import *
from django.db.models.functions import Coalesce
from django.db.models import Sum
from ics.constants import BEGINNING_OF_TIME, END_OF_TIME


def calculate_adjusted_amount(process_type, product_type, team_id):
	start_time = None
	starting_amount = 0

	latest_adjustment = Adjustment.objects \
		.filter(process_type=process_type, product_type=product_type, userprofile__team=team_id) \
		.order_by('-created_at').first()

	if latest_adjustment:
		start_time = latest_adjustment.created_at
		starting_amount = latest_adjustment.amount

	data = inventory_amounts(process_type, product_type, start_time, None)
	return starting_amount + data['created_amount'] - data['used_amount']


def create_adjustments(adjustment_requests, team_id):
	for adjustment_request in adjustment_requests:
		amount_sold_via_square = float(adjustment_request['amount'])
		userprofile = adjustment_request['userprofile']
		process_type = adjustment_request['process_type']
		product_type = adjustment_request['product_type']
		explanation = adjustment_request['explanation']
		current_inventory = float(calculate_adjusted_amount(process_type, product_type, team_id))
		new_inventory_amount = current_inventory - amount_sold_via_square

		Adjustment.objects.create(
			userprofile=UserProfile.objects.get(pk=userprofile),
			process_type=ProcessType.objects.get(pk=process_type),
			product_type=ProductType.objects.get(pk=product_type),
			amount=new_inventory_amount,
			explanation=explanation,
		)


def inventory_amounts(process_type, product_type, start, end):
	if start is None:
		start = BEGINNING_OF_TIME

	if end is None:
		end = END_OF_TIME

	created_amount = Item.active_objects.filter(
		creating_task__process_type=process_type,
		creating_task__product_type=product_type,
		created_at__range=(start, end),
		creating_task__is_trashed=False
	) \
		.aggregate(amount=Coalesce(Sum('amount'), 0))['amount']

	used_amount = TaskIngredient.objects \
		.filter(ingredient__process_type=process_type,
	            ingredient__product_type=product_type,
	            task__created_at__range=(start, end),
	            task__is_trashed=False
	            ) \
		.aggregate(amount=Coalesce(Sum('actual_amount'), 0))['amount']

	return {
		'created_amount': created_amount,
		'used_amount': used_amount,
	}

def old_inventory_created_amount(items_query):
	return items_query.aggregate(amount=Sum('amount'))['amount'] or 0

def old_inventory_used_amount(items_query):
	fully_used_amount = (items_query.filter(inputs__isnull=False, inputs__amount__isnull=True).distinct().aggregate(amount=Sum('amount'))['amount'] or 0)
	partially_used_amount = (items_query.filter(inputs__isnull=False, inputs__amount__isnull=False).aggregate(amount=Sum('inputs__amount'))['amount'] or 0)
	return fully_used_amount + partially_used_amount
