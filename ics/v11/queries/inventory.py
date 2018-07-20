from ics.models import *
from django.db.models.functions import Coalesce
from django.db.models import Sum
from ics.constants import BEGINNING_OF_TIME, END_OF_TIME
from sku_mappings_to_integrations import stitch_sku_mappings_by_team
import csv


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


def get_stitch_adjustment_explanation(square_name, order_number):
	return 'This adjustment was made from a csv upload of sales of "%s" on Stitch for order number %s.' % (square_name, order_number)


def get_sku_info(row, team_skus):
	sku_id = row.get('Line Item ID', False)
	if not sku_id:
		return False
	return team_skus.get(sku_id, False)


def adjust_inventory_from_stitch_csv(polymer_team_id, file_name):
	team_info = stitch_sku_mappings_by_team[polymer_team_id]
	polymer_userprofile_id = team_info['polymer_userprofile_id']
	team_skus = team_info['team_skus']

	adjustment_requests = []
	csv_list = ['Line Item Quantity,Line Item Name,Line Item SKU,Line Item ID,Line Item Total,Order Number',
	            '5,"Books (No Monkeys, No Chocolate)",710,1,42.40,189334',
	            '11,"Packaged Nibs (Kokoa Kamili-Tanzania, 2016, 350 g)",903,2,96.24,189334',
	            '60,"Sample Bars Unfoiled (Camino Verde, Ecuador, 85%)",110-USMPL,3,150.00,189334',
	            '333,[Polymer doesnt track me],333,333,333,189334']
	reader = csv.DictReader(csv_list)
	for row in reader:
		sku_info = get_sku_info(row, team_skus)
		if not sku_info:  # reject blank lines or products which aren't tracked in Polymer
			continue
		adjustment_requests.append({
			'userprofile': polymer_userprofile_id,
			'process_type': sku_info['polymer_process_id'],
			'product_type': sku_info['polymer_product_id'],
			'amount': float(row['Line Item Total']),
			'explanation': get_stitch_adjustment_explanation(row['Line Item Name'], row['Order Number']),
		})

	print(adjustment_requests)
	create_adjustments(adjustment_requests, polymer_team_id)


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
