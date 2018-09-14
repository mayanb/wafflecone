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


# this gets called from a signal that only is triggered once so it's incrementing by 2 to keep pace
@task
def unflag_task_descendants(**kwargs):
	tasks = Task.objects.filter(**kwargs).distinct()
	for task in tasks:
		desc = task.descendants(breakIfCycle=False)
		if desc != None:
			desc.update(num_flagged_ancestors=F('num_flagged_ancestors') - 2)


@task
def input_update(**kwargs):
	recipe = kwargs['recipe']
	updated_task_id = kwargs['taskID']

	if recipe:
		handle_input_change_with_recipe(kwargs, updated_task_id)
	else:
		handle_input_change_with_no_recipe(kwargs, updated_task_id)


@task
def handle_flag_update_after_input_delete(**kwargs):
	child_task_id = kwargs['taskID']
	former_parent_task_id = kwargs['creatingTaskID']
	former_parent_task_flagged_ancestors_id_string = kwargs['creating_task_flagged_ancestors_id_string']

	child_task = Task.objects.get(pk=child_task_id)
	former_parent_task = Task.objects.get(pk=former_parent_task_id)

	# Use qs.difference() to find descendants of child_task which are NOT descendants of former_parent_task
	# because those tasks are the ones which can actually remove former_parent_id (the others are still its descendants)
	child_descendants_qs = child_task.descendants(breakIfCycle=False) or Task.objects.none()
	child_and_its_descendants_qs = child_descendants_qs | Task.objects.filter(pk=child_task_id)
	child_and_its_unique_descendant_ids = list(child_and_its_descendants_qs\
		.difference(former_parent_task.descendants(breakIfCycle=False))\
		.values_list('id', flat=True))

	# Remove from child_task + its descendants the flagged ancestors which are ancestors UNIQUE to former_parent_task
	child_ancestors_qs = child_task.ancestors(breakIfCycle=False) or Task.objects.none()
	child_flagged_ids = [add_pipes(task_id) for task_id in child_ancestors_qs.filter(is_flagged=True).values_list('id', flat=True)]
	former_parent_flagged_ids = get_pipe_surrounded_ids(former_parent_task_flagged_ancestors_id_string)

	flagged_ancestors_unique_to_former_parent = set(former_parent_flagged_ids) - set(child_flagged_ids)
	if former_parent_task.is_flagged:  # since ancestors doesn't include the task itself
		flagged_ancestors_unique_to_former_parent.add(add_pipes(former_parent_task_id))

	for pipe_surrounded_id in flagged_ancestors_unique_to_former_parent:
		delete_id_from_all_tasks_who_have_it_in_their_list(
			pipe_surrounded_id,
			ids_to_query_over=child_and_its_unique_descendant_ids
		)


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
	update_parents_for_ingredient_and_then_child(updated_task_id, old_amount, new_amount, process_type, product_type)


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
def task_deleted_update_cost(deleted_task_id):
	update_parents_of_deleted_task(deleted_task_id)
	update_children_of_deleted_task(deleted_task_id)
