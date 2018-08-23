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
	ingredient_id = kwargs['ingredientID']
	update_parents_for_ingredient_and_then_child(updated_task_id, old_amount, new_amount, ingredient_id)


@task
def batch_size_update(**kwargs):
	updated_task = kwargs['pk']
	updated_task_descendants = get_non_trashed_descendants(Task.objects.filter(pk=updated_task)[0])
	if updated_task_descendants.count() == 0:
		return

	tasks = task_details(updated_task_descendants)
	descendant_ingredients = descendant_ingredient_details(updated_task_descendants, tasks)
	prev_unit_cost, new_unit_cost = get_prev_and_new_unit_costs(tasks[updated_task], kwargs)
	update_children_after_batch_size_change(new_unit_cost, prev_unit_cost, updated_task, tasks, descendant_ingredients, kwargs)


@task
def task_deleted_update_cost(deleted_task_id):
	update_parents_of_deleted_task(deleted_task_id)
	update_children_of_deleted_task(deleted_task_id)
