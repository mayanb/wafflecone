from ics.models import *
from django.db.models.functions import Coalesce
from django.db.models import Sum
import datetime

BEGINNING_OF_TIME = timezone.make_aware(datetime.datetime(1, 1, 1), timezone.utc)
END_OF_TIME = timezone.make_aware(datetime.datetime(3000, 1, 1), timezone.utc)

def inventory_amounts(process_type, product_type, team, start, end):
	if start is None:
		start = BEGINNING_OF_TIME

	if end is None:
		end = END_OF_TIME

	created_amount = Item.active_objects.filter(
		creating_task__process_type=process_type,
		creating_task__product_type=product_type,
		team_inventory=team,
		created_at__range=(start, end)
	) \
		.aggregate(amount=Coalesce(Sum('amount'), 0))['amount']

	used_amount = TaskIngredient.objects \
		.filter(ingredient__process_type=process_type,
	            ingredient__product_type=product_type,
	            team_inventory=team,
	            task__created_at__range=(start, end)
	            ) \
		.aggregate(amount=Coalesce(Sum('actual_amount'), 0))['amount']

	return {
		'created_amount': created_amount,
		'used_amount': used_amount,
	}
