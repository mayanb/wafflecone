import urllib
from functools import reduce
import dateutil.parser
from make_request import make_request


# Obtains all of the business's location IDs. Each location has its own collection of inventory, payments, etc.
def get_payments_from_each_location(request_headers, time_range):
	# Get a list of all location ids (only one GET request, but use same helper for consistency)
	locations_url = 'https://connect.squareup.com/v1/me/locations'
	locations = make_request(locations_url, request_headers)

	# Format a payments urls to fetch payment data from each location
	payments_from_each_location = []
	parameters = urllib.urlencode(time_range)
	for location in locations:
		inventory_path = 'https://connect.squareup.com/v1/' + location['id'] + '/payments?' + parameters
		location_data = make_request(inventory_path, headers=request_headers)
		payments_from_each_location.append(location_data)
	return payments_from_each_location


def get_datetime_object(payment):
	return dateutil.parser.parse(payment['created_at'])


# Remove potential duplicate values from the list of payments, and sorts old-new
# The official Square sample script does this with API data, so we do, too.
def get_sorted_unique_payments(all_location_payments):
	seen_payment_ids = set()
	unique_payments = []
	print("Number of unfiltered payments from each location (note Square throttles after 200):")
	for payments in all_location_payments:
		print(str(len(payments)))
	payments = reduce(lambda sum, payments: sum + payments, all_location_payments, [])
	print('Total payments (all locations):  ' + str(len(payments)))

	for payment in payments:
		# Filter duplicates or anything without a date
		if payment['id'] in seen_payment_ids or payment.get('created_at', None) is None:
			continue
		seen_payment_ids.add(payment['id'])
		unique_payments.append(payment)
	print('Unique payments (all locations): ' + str(len(unique_payments)))
	return sorted(unique_payments, key=get_datetime_object)


# Returns a dict {item_id -> [payment_object], ...} for all ids specified in team_skus which have payments
def get_payments_by_item_id(time_range, request_headers, team_skus):
	item_id_to_payments_map = {}

	# Download all payment from each location in parallel batches, get unique ones
	all_location_payments = get_payments_from_each_location(request_headers, time_range)
	sorted_unique_payments = get_sorted_unique_payments(all_location_payments)

	# Parse all payments and group relevant group by item_id (product type)
	for payment in sorted_unique_payments:
		created_at = payment['created_at']  # store to use for finding most recent item
		for item_detail in payment.get('itemizations', []):
			item_id = item_detail['item_detail'].get('item_id', False)
			# Some payments did not specify a product (item), and we want only the subset specified in team_skus
			if item_id and team_skus.get(item_id, False):
				item_detail['created_at'] = created_at
				if item_id_to_payments_map.get(item_id, False):
					item_id_to_payments_map[item_id].append(item_detail)
				else:
					item_id_to_payments_map[item_id] = [item_detail]
	return item_id_to_payments_map


def get_most_recent_payment(payments_array):
	return max(payments_array, key=get_datetime_object)


def get_adjustment_explanation(square_name, last_synced_with_square_at):
	date_display_str = dateutil.parser.parse(last_synced_with_square_at).strftime('%c')
	return 'This adjustment was made automatically based on sales of "%s" on Square on or before %s.' % (square_name, date_display_str)


def get_square_changes(begin_time, end_time, access_token, team_skus, polymer_team_id):
	# Reads'Request (up to 200) payments made from begin_time (inclusive) to end_time (exclusive), sorted chronologically'
	time_range = {'begin_time': begin_time, 'end_time': end_time, 'order': 'ASC', 'limit': 200}  # 200 is max allowed
	request_headers = {
		'Authorization': 'Bearer ' + access_token,
		'Accept': 'application/json',
		'Content-Type': 'application/json'
	}
	payments_by_item_id = get_payments_by_item_id(time_range, request_headers, team_skus)

	adjustments = []
	for item_id, payments_array in payments_by_item_id.iteritems():
		for payment in payments_array:  # SANITY CHECK
			print(str(payment['name']) + ': ' + str(payment['quantity']) + ', ' + str(payment['created_at']))

		total_amount_for_item = reduce(lambda sum, payment: sum + float(payment['quantity']), payments_array, 0)
		info = team_skus[item_id]
		adjustments.append({
			'userprofile': 1,
			'process_type': info['polymer_process_id'],
			'product_type': info['polymer_product_id'],
			'amount': total_amount_for_item,
			'explanation': get_adjustment_explanation(info['square_name'], end_time),
		})
	return {
		'adjustment_requests': adjustments,
		'team_id': polymer_team_id,
	}
