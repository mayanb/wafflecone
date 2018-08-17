from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models.functions import Coalesce

from ics.models import *
from cost_update_helpers import *
from zappa.async import task
from django.db.models import F, Count, Sum


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
			if (task.is_flagged):
				task.descendants().update(num_flagged_ancestors=F('num_flagged_ancestors') + 1)
			else:
				task.descendants().update(num_flagged_ancestors=F('num_flagged_ancestors') - 1)


# this gets called from a signal that only is triggered once so it's incrementing by 2 to keep pace
@task
def unflag_task_descendants(**kwargs):
	tasks = Task.objects.filter(**kwargs).distinct()
	for task in tasks:
		task.descendants().update(num_flagged_ancestors=F('num_flagged_ancestors') - 2)


# calculate cost of current task and propagate changes when inputs added/deleted
@task
def input_update(**kwargs):
	recipe = kwargs['recipe']
	updated_task_id = kwargs['taskID']
	updated_task_with_parents = Task.objects.filter(is_trashed=False, pk=updated_task_id).annotate(
		task_parent_ids=ArrayAgg('inputs__input_item__creating_task__id'))[0]

	if not recipe:
		handle_input_change_with_no_recipe(kwargs, updated_task_with_parents, updated_task_id)

	# RECIPE EXISTS
	else:
		input_item__creating_task__product_type = kwargs['input_item__creating_task__product_type']
		input_item__creating_task__process_type = kwargs['input_item__creating_task__process_type']
		input_creating_task = kwargs['creatingTaskID']
		input_added = kwargs['added']
		# check number of similar inputs
		similar_inputs = Input.objects.filter(task=updated_task_id, \
										  input_item__creating_task__product_type=input_item__creating_task__product_type, \
										  input_item__creating_task__process_type=input_item__creating_task__process_type).count()
		ingredient_id = Ingredient.objects.get(process_type_id=input_item__creating_task__process_type,
											   product_type_id=input_item__creating_task__product_type)
		task_ingredient = TaskIngredient.objects.get(task_id=updated_task_id, ingredient_id=ingredient_id)
		scaled_amount = task_ingredient.scaled_amount
		actual_amount = task_ingredient.actual_amount
		# fetch task which created the input
		input_parent = Task.objects.filter(is_trashed=False, pk=input_creating_task).annotate(
			batch_size=Coalesce(Sum('items__amount'), 0))[0]

		#***************#
		updated_task = Task.objects.filter(is_trashed=False, pk=updated_task_id).annotate(
			task_parent_ids=ArrayAgg('inputs__input_item__creating_task__id'))[0]
		parents_contributing_ingredient = get_parents_contributing_ingredient(updated_task.task_parent_ids, ingredient_id.id)

		if input_added:
			if similar_inputs < 2:
				parent_unit_cost = input_parent.cost/input_parent.batch_size
				parent_contribution = min(parent_unit_cost * scaled_amount, input_parent.reamaining_worth)
				parent_remaining_worth = input_parent.reamaining_worth - parent_contribution
				new_updated_task_cost = updated_task_with_parents.cost + parent_contribution
				new_updated_task_remaining_worth = updated_task_with_parents.remaining_worth + parent_contribution
				Task.objects.filter(pk=input_creating_task).update(remaining_worth=parent_remaining_worth)
				Task.objects.filter(pk=updated_task).update(cost=new_updated_task_cost, remaining_worth=new_updated_task_remaining_worth)
			else:
				num_parents = len(parents_contributing_ingredient) - 1
				total_change_in_value_from_all_parents = update_parents_for_ingredient(parents_contributing_ingredient, actual_amount, actual_amount, num_parents,
														   input_creating_task, True)

				old_updated_task_cost = updated_task.cost
				old_updated_task_remaining_worth = updated_task.remaining_worth
				new_updated_task_cost = old_updated_task_cost + total_change_in_value_from_all_parents
				new_updated_task_remaining_worth = old_updated_task_remaining_worth + total_change_in_value_from_all_parents
				Task.objects.filter(pk=updated_task_id).update(cost=new_updated_task_cost, remaining_worth=new_updated_task_remaining_worth)
		else:
			if similar_inputs < 1:
				parent_unit_cost = input_parent.cost / input_parent.batch_size
				parent_contribution = min(parent_unit_cost * scaled_amount, input_parent.cost)
				parent_remaining_worth = input_parent.reamaining_worth + parent_contribution
				new_updated_task_cost = updated_task_with_parents.cost - parent_contribution
				new_updated_task_remaining_worth = updated_task_with_parents.remaining_worth - parent_contribution
				Task.objects.filter(pk=input_creating_task).update(remaining_worth=parent_remaining_worth)
				Task.objects.filter(pk=updated_task).update(cost=new_updated_task_cost, remaining_worth=new_updated_task_remaining_worth)
			else:
				num_parents = len(parents_contributing_ingredient) + 1
				total_change_in_value_from_all_parents = update_parents_for_ingredient(parents_contributing_ingredient, actual_amount, actual_amount, num_parents,
														   input_creating_task, False, True)

				old_updated_task_cost = updated_task.cost
				old_updated_task_remaining_worth = updated_task.remaining_worth
				new_updated_task_cost = old_updated_task_cost + total_change_in_value_from_all_parents
				new_updated_task_remaining_worth = old_updated_task_remaining_worth + total_change_in_value_from_all_parents
				Task.objects.filter(pk=updated_task_id).update(cost=new_updated_task_cost, remaining_worth=new_updated_task_remaining_worth)

	try:
		# update descendants
		updated_task_descendants = get_non_trashed_descendants(Task.objects.filter(pk=updated_task_id)[0])
		if updated_task_descendants.count() == 0:
			return
		old_cost = updated_task_with_parents.cost
		tasks = task_details(updated_task_descendants)
		descendant_ingredients = descendant_ingredient_details(updated_task_descendants, tasks)

		batch_size = tasks[updated_task]['batch_size']
		prev_unit_cost = get_unit_cost(old_cost, batch_size)
		new_unit_cost = get_unit_cost(tasks[updated_task]['cost'], batch_size)

		update_children(new_unit_cost, prev_unit_cost, updated_task, tasks, descendant_ingredients)

	except Exception as e:
		print "except block"
		print(str(e))


def ingredient_amount_update(**kwargs):
	TaskIngredient.objects.filter(pk=kwargs['task_ing_id']).update(was_amount_changed=False)

	updated_task_id = kwargs['taskID']
	old_amount = kwargs['previous_amount']
	new_amount = kwargs['actual_amount']
	ingredient_id = kwargs['ingredientID']
	update_parents_for_ingredient_and_then_child(updated_task_id, old_amount, new_amount, ingredient_id)


# calculate cost of current task and propagate changes when batch size changed
def batch_size_update(**kwargs):
	updated_task = kwargs['pk']
	updated_task_descendants = get_non_trashed_descendants(Task.objects.filter(pk=updated_task)[0])
	if updated_task_descendants.count() == 0:
		return

	tasks = task_details(updated_task_descendants)
	descendant_ingredients = descendant_ingredient_details(updated_task_descendants, tasks)
	prev_unit_cost, new_unit_cost = get_prev_and_new_unit_costs(tasks[updated_task], kwargs)

	update_children(new_unit_cost, prev_unit_cost, updated_task, tasks, descendant_ingredients)


# MAIN: updates costs when task is deleted
def task_deleted_update_cost(deleted_task):
	update_parents_of_deleted_task(deleted_task.id)
	update_children_of_deleted_task(deleted_task.id)
