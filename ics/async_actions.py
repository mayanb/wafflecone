from ics.models import *
from cost_update_helpers import *
from zappa.async import task
from django.db.models import F, Count, Sum
from update_costs_for_entire_graph import update_costs_for_entire_graph, get_task_neighbor_ids


@task
def update_task_search_vector(**kwargs):
	tasks = Task.objects.with_documents().filter(**kwargs).distinct()
	for task in tasks:
		task.search = task.document
		task.save(update_fields=['search'])


@task
def update_task_descendents_flag_number(**kwargs):
	# all our signals are getting triggered twice for some reason so the num_flagged_ancestors is incremented and decremented by 2
	tasks = Task.objects.filter(**kwargs).distinct()
	for task in tasks:
		if (task.was_flag_changed):
			desc = task.descendants(breakIfCycle=False)
			if desc != None:
				if (task.is_flagged):
					desc.update(num_flagged_ancestors=F('num_flagged_ancestors') + 1)
				else:
					desc.update(num_flagged_ancestors=F('num_flagged_ancestors') - 1)


# this gets called from a signal that only is triggered once so it's incrementing by 2 to keep pace
@task
def unflag_task_descendants(**kwargs):
	tasks = Task.objects.filter(**kwargs).distinct()
	for task in tasks:
		desc = task.descendants(breakIfCycle=False)
		if desc != None:
			desc.update(num_flagged_ancestors=F('num_flagged_ancestors') - 2)


@task
def input_update(task_id):
	update_costs_for_entire_graph(task_id)


@task
def ingredient_amount_update(task_id, task_ing_id):
	# This boolean helps us track whether the change was made by a user, or internally as a part of a different update
	TaskIngredient.objects.filter(pk=task_id).update(was_amount_changed=False)
	update_costs_for_entire_graph(task_id)


@task
def batch_size_update(task_id):
	update_costs_for_entire_graph(task_id)


@task
def task_cost_update(updated_task_id):
	update_costs_for_entire_graph(updated_task_id)


@task
def task_deleted_update_cost(deleted_task_id):
	former_neighbor_ids = get_task_neighbor_ids(deleted_task_id)  # deleted_task still has its edges, so get neighbors
	delete_inputs_and_outputs_and_zero_cost_for_deleted_task(deleted_task_id)
	if former_neighbor_ids:
		arbitrary_node_in_deleted_task_graph = former_neighbor_ids[0]
		update_costs_for_entire_graph(arbitrary_node_in_deleted_task_graph)


# HELPER FUNCTIONS

def delete_inputs_and_outputs_and_zero_cost_for_deleted_task(deleted_task_id):
	Input.objects.filter(input_item__creating_task=deleted_task_id).delete()  # delete direct children
	Input.objects.filter(task=deleted_task_id).delete()  # delete direct parents
	Task.objects.filter(pk=deleted_task_id).update(cost=0, remaining_worth=0)  # zero cost
