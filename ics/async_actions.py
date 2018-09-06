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


# This is nearly identical to ingredient_amount_update(), except with special flags to handle
# special cases of introducing or exiting an input, since one is done post_save and the other pre_delete.
# It also handles of tasks with recipes.
@task
def input_update(**kwargs):
	updated_task_id = kwargs['taskID']
	creating_task_of_changed_input_id = kwargs['creatingTaskID']
	input_added = kwargs['added']
	task_ingredient__actual_amount = kwargs['task_ingredient__actual_amount']
	process_type = kwargs['process_type']
	product_type = kwargs['product_type']
	recipe_exists_for_ingredient = kwargs['recipe_exists_for_ingredient']
	adding_first_or_deleting_last_input = kwargs['adding_first_or_deleting_last_input']
	creating_task_of_changed_input = get_creating_task_of_changed_input(creating_task_of_changed_input_id)

	if not creating_task_of_changed_input or creating_task_of_changed_input.cost is None:
		return

	old_amount, new_amount = get_amounts(
		task_ingredient__actual_amount,
		float(creating_task_of_changed_input.batch_size),
		input_added,
		recipe_exists_for_ingredient,
		adding_first_or_deleting_last_input,
	)

	update_parents_for_ingredient_and_their_children(
		updated_task_id,
		old_amount,
		new_amount,
		process_type,
		product_type,
		creating_task_of_changed_input=creating_task_of_changed_input.id,
		input_added=input_added,
		input_deleted=not input_added,  # Function is only ever called with input add/delete
	)


@task
def ingredient_amount_update(**kwargs):
	TaskIngredient.objects.filter(pk=kwargs['task_ing_id']).update(was_amount_changed=False)

	updated_task_id = kwargs['taskID']
	old_amount = kwargs['previous_amount']
	new_amount = kwargs['actual_amount']
	process_type = kwargs['process_type']
	product_type = kwargs['product_type']
	update_parents_for_ingredient_and_their_children(updated_task_id, old_amount, new_amount, process_type, product_type)


@task
def batch_size_update(**kwargs):
	updated_task = kwargs['pk']
	updated_task_descendants = get_non_trashed_descendants(updated_task)
	if updated_task_descendants.count() == 0:
		return

	tasks = task_details(updated_task_descendants)
	descendant_ingredients = descendant_ingredient_details(updated_task_descendants, tasks)
	prev_unit_cost, new_unit_cost = get_prev_and_new_unit_costs(tasks[updated_task], kwargs)
	parent_previous_batch_size = float(kwargs['previous_amount'])
	parent_new_batch_size = float(kwargs['new_amount'])
	update_children_after_batch_size_or_child_ingredient_amount_change(new_unit_cost, prev_unit_cost, updated_task, tasks, descendant_ingredients, parent_previous_batch_size, parent_new_batch_size)


@task
def task_cost_update(updated_task_id, previous_cost, new_cost):
	# Include updated_task in descendants for later use (not because it's deleted), e.g. its children, cost etc
	updated_task_descendants = get_non_trashed_descendants(updated_task_id, include_even_if_deleted=updated_task_id)
	if updated_task_descendants.count() == 0:
		return

	tasks = task_details(updated_task_descendants)
	descendant_ingredients = descendant_ingredient_details(updated_task_descendants, tasks)
	batch_size = float(tasks[updated_task_id]['batch_size'])
	prev_unit_cost = get_unit_cost(previous_cost, batch_size)
	new_unit_cost = get_unit_cost(new_cost, batch_size)
	update_children_after_batch_size_or_child_ingredient_amount_change(new_unit_cost, prev_unit_cost, updated_task_id, tasks, descendant_ingredients, batch_size, batch_size)


@task
def task_deleted_update_cost(deleted_task_id):
	task_ingredients = TaskIngredient.objects.filter(task=deleted_task_id).annotate(batch_size=Coalesce(Sum('task__items__amount'), 0)) \
		.values('actual_amount', 'ingredient__process_type__id', 'ingredient__product_type__id')

	for task_ingredient in task_ingredients:
		update_parents_for_ingredient_and_their_children(  # use this to delete input from all parents
			deleted_task_id,
			old_amount=float(task_ingredient['actual_amount']),
			new_amount=0,  # return worth to all inputs
			process_type=task_ingredient['ingredient__process_type__id'],
			product_type=task_ingredient['ingredient__product_type__id'],
			input_added=False,
			input_deleted=True,
			child_task_is_being_deleted_entirely=True,  # Flag signals removal of ALL parents as inputs to deleted_task
		)
