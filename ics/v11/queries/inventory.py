from ics.models import *
from django.db.models.functions import Coalesce
from django.db.models import Sum
from ics.constants import BEGINNING_OF_TIME, END_OF_TIME


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

def get_adjusted_amount(process_type, product_type):
	start_time = None
	starting_amount = 0
	#print('process_type={}, product_type={}'.format(process_type, product_type))
	latest_adjustment = Adjustment.objects \
		.filter(process_type=process_type, product_type=product_type) \
		.order_by('-created_at').first()

	if latest_adjustment:
		start_time = latest_adjustment.created_at
		starting_amount = latest_adjustment.amount

	data = inventory_amounts(process_type, product_type, start_time, None)
	return starting_amount + data['created_amount'] - data['used_amount']

def get_adjusted_cost(process_type, product_type):
	cost = 0
	amount_remaining = get_adjusted_amount(process_type, product_type)
	items = Item.objects \
		.filter(
			creating_task__is_trashed=False,
			creating_task__process_type=process_type,
			creating_task__product_type=product_type,
		).annotate(
			cost=F('creating_task__cost')
		).order_by('-created_at')

	for item in items:
		#print('Item: amount={}, cost={}, created_at={}'.format(item.amount, item.cost, item.created_at))
		if amount_remaining > 0:
			if amount_remaining - item.amount >= 0:
				cost += item.cost
				amount_remaining -= item.amount
			else: 
				ratio = item.cost / item.amount
				cost += ratio * amount_remaining
				amount_remaining = 0
		else:
			break
	return cost
	