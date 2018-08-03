from ics.models import *
from basic.v11.queries.inventory import inventory_amounts
from sku_mappings_to_integrations import get_sku_mappings_for
import csv
import codecs


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


def get_sku_info(row, team_stitch_skus):
	sku_id = row.get('LineItemID', False)
	if not sku_id:
		return False
	return team_stitch_skus.get(sku_id, False)


def extract_csv_reader(request):
	csvfile = request.FILES['file_binary']
	dialect = csv.Sniffer().sniff(codecs.EncodedFile(csvfile, "utf-8").read(1024))
	csvfile.open()
	return csv.DictReader(codecs.EncodedFile(csvfile, "utf-8"), delimiter=',', dialect=dialect)


def adjust_inventory_using_stitch_csv(polymer_team_id, request):
	team_info = get_sku_mappings_for(polymer_team_id)
	if not team_info:
		return None

	polymer_userprofile_id = team_info['polymer_userprofile_id']
	team_stitch_skus = team_info['stitch']

	# Format Adjustment request objects
	adjustment_requests = []
	for row in extract_csv_reader(request):
		sku_info = get_sku_info(row, team_stitch_skus)
		if not sku_info:  # reject blank lines or products which aren't tracked in Polymer
			continue
		adjustment_requests.append({
			'userprofile': polymer_userprofile_id,
			'process_type': sku_info['polymer_process_id'],
			'product_type': sku_info['polymer_product_id'],
			'amount': float(row['LineItemTotal']),
			'explanation': get_stitch_adjustment_explanation(row['LineItemName'], row['OrderNumber']),
		})

	return create_adjustments(adjustment_requests, polymer_team_id)


def create_adjustments(adjustment_requests, team_id):
	new_adjustments = []
	for adjustment_request in adjustment_requests:
		amount_sold = float(adjustment_request['amount'])  # Note: amount here represents change, not new inventory amount
		userprofile = adjustment_request['userprofile']
		process_type = adjustment_request['process_type']
		product_type = adjustment_request['product_type']
		explanation = adjustment_request['explanation']
		current_inventory = float(calculate_adjusted_amount(process_type, product_type, team_id))
		new_inventory_amount = current_inventory - amount_sold

		adjustment = Adjustment.objects.create(
			userprofile=UserProfile.objects.get(pk=userprofile),
			process_type=ProcessType.objects.get(pk=process_type),
			product_type=ProductType.objects.get(pk=product_type),
			amount=new_inventory_amount,
			explanation=explanation,
		)
		new_adjustments.append(adjustment)
	return new_adjustments
