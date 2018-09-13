from ics.models import *
from cost_update_helpers import *
from zappa.async import task
from django.db.models import F, Count, Sum, Case, When, Value
from django.db.models.functions import Concat
from django.db.models.expressions import RawSQL
from django.db import connection


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
		if (task.was_flag_changed):
			desc = task.descendants(breakIfCycle=False)
			if desc != None:
				pipe_surrounded_id = add_pipes(task.id)
				if (task.is_flagged):
					# Add id to ancestor strings which don't already have it
					id_with_pipe_on_right_side = pipe_surrounded_id[1:]
					desc_without_this_id = desc.exclude(flagged_ancestors_id_string__contains=pipe_surrounded_id) \
						.annotate(id_with_pipe_on_right_side=Value(id_with_pipe_on_right_side, output_field=models.TextField()))

					desc_without_this_id.annotate(
						new_flagged_ancestors_id_string=Case(
							When(flagged_ancestors_id_string__contains='|', then=Concat(F('flagged_ancestors_id_string'), F('id_with_pipe_on_right_side'))),
							default=Concat(Value('|'), F('id_with_pipe_on_right_side')),
							output_field=models.TextField()
						)
					).update(flagged_ancestors_id_string=F('new_flagged_ancestors_id_string'))
				else:  # Task has been un-flagged
					print('Flag removed from task ', task.id)
					delete_id_from_all_tasks_who_have_it_in_their_list(pipe_surrounded_id)


def delete_id_from_all_tasks_who_have_it_in_their_list(pipe_surrounded_id):
	cursor = connection.cursor()
	cursor.execute("""UPDATE ics_task
							SET flagged_ancestors_id_string = (CASE WHEN task_with_ancestor_id.new_ancestors_string = '|' THEN '' ELSE task_with_ancestor_id.new_ancestors_string END)
							FROM (select
										id,
										flagged_ancestors_id_string,
										substring(flagged_ancestors_id_string from 0 for ancestor_id_position) || '|' || substring(flagged_ancestors_id_string from ancestor_id_position + %s) as new_ancestors_string
										from (
										select
											id,
											flagged_ancestors_id_string,
											strpos(flagged_ancestors_id_string, %s) AS ancestor_id_position
										from ics_task
										where strpos(flagged_ancestors_id_string, %s) > 0
										) task
							) task_with_ancestor_id
							WHERE ics_task.id = task_with_ancestor_id.id""", [str(len(pipe_surrounded_id)), pipe_surrounded_id, pipe_surrounded_id])


def get_pipe_surrounded_ids(flagged_ancestors_id_string, newly_flagged_task_id=''):
	flagged_ancestors_id_string = flagged_ancestors_id_string or ''
	id_array = flagged_ancestors_id_string.split('|')
	pipe_surrounded_ids = [add_pipes(id_string) for id_string in id_array if id_string is not '']
	if newly_flagged_task_id:
		pipe_surrounded_ids.append(add_pipes(newly_flagged_task_id))
	return pipe_surrounded_ids


def add_pipes(task_id):
	return '|' + str(task_id) + '|'



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
