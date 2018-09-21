from ics.models import *
from cost_update_helpers import *
from zappa.async import task
from django.db.models import F, Count, Sum, Case, When, Value
from django.db.models.functions import Concat
from django.db import connection
from ics.raw_sql_queries import REMOVE_ID_FROM_ALL_TASKS_IN_DB_WHICH_HAVE_IT, REMOVE_ID_FROM_ALL_SPECIFIED_TASKS_WHICH_HAVE_IT


@task
def update_task_search_vector(**kwargs):
	tasks = Task.objects.with_documents().filter(**kwargs).distinct()
	for task in tasks:
		task.search = task.document
		task.save(update_fields=['search'])


@task
def handle_potential_flag_status_change(**kwargs):
	# Signal may fire twice, but the function is idempotent: it only adds/removes ids if they are missing/exist
	tasks = Task.objects.filter(**kwargs).distinct()
	for task in tasks:
		if task.was_flag_changed:
			descendants = task.descendants(breakIfCycle=False)
			if descendants is not None:
				pipe_surrounded_id = add_pipes(task.id)
				if task.is_flagged:
					add_new_id_to_descendants_ancestor_lists(descendants, pipe_surrounded_id)
				else:  # Task has been un-flagged
					delete_id_from_all_tasks_who_have_it_in_their_list(pipe_surrounded_id)


def add_new_id_to_descendants_ancestor_lists(descendants, pipe_surrounded_id):
	# Add id to ancestor strings which don't already have it
	id_with_pipe_on_right_side = pipe_surrounded_id[1:]
	desc_without_this_id = descendants.exclude(flagged_ancestors_id_string__contains=pipe_surrounded_id) \
		.annotate(id_with_pipe_on_right_side=Value(id_with_pipe_on_right_side, output_field=models.TextField()))

	desc_without_this_id.annotate(
		new_flagged_ancestors_id_string=Case(
			When(flagged_ancestors_id_string__contains='|', then=Concat(F('flagged_ancestors_id_string'), F('id_with_pipe_on_right_side'))),
			default=Concat(Value('|'), F('id_with_pipe_on_right_side')),
			output_field=models.TextField()
		)
	).update(flagged_ancestors_id_string=F('new_flagged_ancestors_id_string'))


def delete_id_from_all_tasks_who_have_it_in_their_list(pipe_surrounded_id, ids_to_query_over=None):
	parameters = [str(len(pipe_surrounded_id)), pipe_surrounded_id, pipe_surrounded_id]
	cursor = connection.cursor()
	if ids_to_query_over:
		parameters.append(ids_to_query_over)
		cursor.execute(REMOVE_ID_FROM_ALL_SPECIFIED_TASKS_WHICH_HAVE_IT, parameters)
	else:
		cursor.execute(REMOVE_ID_FROM_ALL_TASKS_IN_DB_WHICH_HAVE_IT, parameters)


def get_pipe_surrounded_ids(flagged_ancestors_id_string):
	flagged_ancestors_id_string = flagged_ancestors_id_string or ''
	id_array = flagged_ancestors_id_string.split('|')
	pipe_surrounded_ids = [add_pipes(id_string) for id_string in id_array if id_string]
	return pipe_surrounded_ids


def get_parent_ids_not_already_in_child(child_flagged_ancestors_id_string, parent_flagged_ancestors_id_string):
	child_pipe_surrounded_ids = get_pipe_surrounded_ids(child_flagged_ancestors_id_string)
	parent_pipe_surrounded_ids = get_pipe_surrounded_ids(parent_flagged_ancestors_id_string)
	return set(parent_pipe_surrounded_ids) - set(child_pipe_surrounded_ids)


def add_pipes(task_id):
	return '|' + str(task_id) + '|' if task_id is not '' else ''


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
def handle_flag_update_after_input_delete(child_task_id, former_parent_task_id, former_parent_task_flagged_ancestors_id_string):
	return "yay, all done (with nothing)"
	# try:
	# 	child_task = Task.objects.get(pk=child_task_id)
	# 	former_parent_task = Task.objects.get(pk=former_parent_task_id)
	#
	# 	# Use qs.difference() to find descendants of child_task which are NOT descendants of former_parent_task
	# 	# because those tasks are the ones which can actually remove former_parent_id (the others are still its descendants)
	# 	child_descendants_qs = child_task.descendants(breakIfCycle=False) or Task.objects.none()
	# 	child_and_its_descendants_qs = child_descendants_qs | Task.objects.filter(pk=child_task_id)
	# 	child_and_its_unique_descendant_ids = list(child_and_its_descendants_qs\
	# 		.difference(former_parent_task.descendants(breakIfCycle=False))\
	# 		.values_list('id', flat=True))
	#
	# 	# Remove from child_task + its descendants the flagged ancestors which are ancestors UNIQUE to former_parent_task
	# 	child_ancestors_qs = child_task.ancestors(breakIfCycle=False) or Task.objects.none()
	# 	child_flagged_ids = [add_pipes(task_id) for task_id in child_ancestors_qs.filter(is_flagged=True).values_list('id', flat=True)]
	# 	former_parent_flagged_ids = get_pipe_surrounded_ids(former_parent_task_flagged_ancestors_id_string)
	#
	# 	flagged_ancestors_unique_to_former_parent = set(former_parent_flagged_ids) - set(child_flagged_ids)
	# 	if former_parent_task.is_flagged:  # since ancestors doesn't include the task itself
	# 		flagged_ancestors_unique_to_former_parent.add(add_pipes(former_parent_task_id))
	#
	# 	for pipe_surrounded_id in flagged_ancestors_unique_to_former_parent:
	# 		delete_id_from_all_tasks_who_have_it_in_their_list(
	# 			pipe_surrounded_id,
	# 			ids_to_query_over=child_and_its_unique_descendant_ids
	# 		)
	# except Exception as e:
	# 	print('_______EXCEPTION CAUGHT_________')
	# 	print(e)


@task
def handle_flag_update_after_input_add(**kwargs):
	child_task_id = kwargs['taskID']
	child_task_flagged_ancestors_id_string = kwargs['task_flagged_ancestors_id_string']
	parent_task_flagged_ancestors_id_string = kwargs['creating_task_flagged_ancestors_id_string']

	child_task_qs = Task.objects.filter(pk=child_task_id)
	_descendants = child_task_qs[0].descendants(breakIfCycle=False) or Task.objects.none()
	descendants = _descendants | child_task_qs  # union operator
	parent_ids_not_already_in_child = get_parent_ids_not_already_in_child(child_task_flagged_ancestors_id_string, parent_task_flagged_ancestors_id_string)
	for pipe_surrounded_id in parent_ids_not_already_in_child:
		# descendants.exclude() returns a new query_set without mutating descendants
		descendants_lacking_this_id = descendants.exclude(flagged_ancestors_id_string__contains=pipe_surrounded_id)
		add_new_id_to_descendants_ancestor_lists(descendants_lacking_this_id, pipe_surrounded_id)


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
	updated_task_id = kwargs['pk']
	updated_task_descendants = get_non_trashed_descendants(updated_task_id)
	if updated_task_descendants.count() == 0:
		return

	tasks = task_details(updated_task_descendants)
	updated_task = tasks[updated_task_id]
	descendant_ingredients = descendant_ingredient_details(updated_task_descendants, tasks)

	change_in_item_amount = kwargs['change_in_item_amount']
	new_batch_size = float(updated_task['batch_size'])
	previous_batch_size = new_batch_size - change_in_item_amount

	cost = tasks[updated_task_id]['cost']
	prev_unit_cost = get_unit_cost(cost, previous_batch_size)
	new_unit_cost = get_unit_cost(cost, new_batch_size)

	update_parent_and_children_recursively(new_unit_cost, prev_unit_cost, updated_task_id, tasks, descendant_ingredients, previous_batch_size, new_batch_size)


@task
def task_cost_update(updated_task_id, previous_cost, new_cost):
	execute_task_cost_update(updated_task_id, previous_cost, new_cost)


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

	delete_inputs_and_outputs_and_zero_cost_for_deleted_task(deleted_task_id)
