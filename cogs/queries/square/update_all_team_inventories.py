from cogs.queries.sku_mappings_to_integrations import sku_mappings_by_team
from cogs.queries.square.get_square_changes import get_square_changes
from cogs.queries.integration_adjustments import create_adjustments

# Runs a square fetch of payment data for the time period specified for each Polymer team specified.
# Makes necessary adjustments to Polymer's database, then saves (exclusive) end_time for use as begin_time (inclusive)
# for the next time a Square sync is run.
# If any exception thrown, stores team and error, and continues on to the remaining teams.


def iso_format(timezone_object):
	return str(timezone_object).replace(' ', 'T')


def update_all_team_inventories(last_square_sync_times, end_time):
	failed_teams = []
	for polymer_team_id, team_data in sku_mappings_by_team.iteritems():
		polymer_team = team_data['polymer_team_name']
		try:
			update_team_inventory(end_time, polymer_team, team_data, last_square_sync_times)
		except Exception as e:
			error_string = '%s (%s)' % (polymer_team, e)
			failed_teams.append(error_string)
			print('Updating inventory based on Square transactions terminated due to an exception:')
			print(e)
	return failed_teams


def update_team_inventory(end_time, polymer_team, team_data, last_square_sync_times):
	begin_time = iso_format(last_square_sync_times[team_data['polymer_team_id']])
	print('Begin time: ' + begin_time)
	print('end time:' + end_time)

	print('Requesting inventory data from Square for %s__________________________' % polymer_team)
	inventory_changes = get_square_changes(begin_time, end_time, team_data['square_access_token'], team_data['square'], team_data['polymer_team_id'])
	print(inventory_changes)

	print('\nRequesting Polymer inventory adjustments for %s__________________________' % polymer_team)
	create_adjustments(inventory_changes['adjustment_requests'], inventory_changes['team_id'])
	print('\n')
