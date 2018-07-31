from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models.functions import Coalesce

from ics.models import *
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
def update_cost_changed_input(**kwargs):
	updated_task = kwargs['taskID']
	input_creating_task = kwargs['creatingTaskID']
	input_added = kwargs['added']
	# fetch updated_task object with children
	parents = Task.objects.filter(is_trashed=False, pk=updated_task).annotate(
		task_parent_ids=ArrayAgg('inputs__input_item__creating_task__id'))
	# fetch task which created the input
	input_parent = Task.objects.filter(is_trashed=False, pk=input_creating_task).annotate(
				batch_size=Coalesce(Sum('items__amount'), 0))
	if input_parent[0].cost is None:
		# return if cost is None for parent
		return

	# update remaining worth of parent task -> subtract/add cost worth task's batch_size
	if input_added:
		new_remaining_worth = (input_parent[0].remaining_worth or input_parent[0].cost) - input_parent[0].cost
	else:
		new_remaining_worth = (input_parent[0].remaining_worth or input_parent[0].cost) + input_parent[0].cost
	Task.objects.filter(pk=input_creating_task).update(remaining_worth=new_remaining_worth)

	# update cost and remaining worth of updated task -> add cost worth parent task's batch size
	if input_added:
		new_updated_task_cost = (parents[0].cost or 0) + input_parent[0].cost
		new_updated_task_remaining_worth = (parents[0].remaining_worth or 0) + input_parent[0].cost
	else:
		new_updated_task_cost = parents[0].cost - input_parent[0].cost
		new_updated_task_remaining_worth = parents[0].remaining_worth - input_parent[0].cost
	Task.objects.filter(pk=updated_task).update(cost=new_updated_task_cost,
												remaining_worth=new_updated_task_remaining_worth)

	try:
		# query to fetch tasks which are parent to atleast one task and their children
		tasks_with_child = Task.objects.filter(is_trashed=False).annotate(num_children=Count(F('items__inputs')),
																		  children_list=ArrayAgg('items__inputs__task'),
																		  batch_size=Coalesce(Sum('items__amount'),
																							  0)).filter(
			num_children__gt=0)
		tasks = {}
		parents_list(tasks_with_child, tasks)
		# propagate cost if updated_task is parent to atleast one child
		if updated_task in tasks:
			ids = Task.objects.values('id')
			# query to fetch tasks along with their parent tasks
			parents = Task.objects.filter(is_trashed=False, pk__in=ids).annotate(
				task_parent_ids=ArrayAgg('inputs__input_item__creating_task__id'))
			faulty_tasks = {}  # stores tasks which are not available in taskingredient table
			list_parents = {}  # stores parents list and taskingredients for each child task
			get_ingredients(faulty_tasks, list_parents, parents)

			# populate task_ing_map with taskingredients along with all the parents contributing that ingredient for each task
			for key in list_parents:
				task_ing_map = {}
				for task_ing in list_parents[key]['task_ings']:
					task_ing_map[(task_ing.ingredient.process_type_id, task_ing.ingredient.product_type_id)] = {
						'amount': task_ing.actual_amount, 'parent_tasks': set()}
				if input_added and key == updated_task and (input_parent[0].process_type_id, input_parent[0].product_type_id) not in task_ing_map:
					task_ing_map[(input_parent[0].process_type_id, input_parent[0].product_type_id)] = {
						'amount': input_parent[0].batch_size, 'parent_tasks': set()}
				for parent in list_parents[key]['parents']:
					if parent in tasks:
						if input_added:
							task_ing_map[(tasks[parent]['process_type'], tasks[parent]['product_type'])]['parent_tasks'].add(
								parent)
						elif parent != input_creating_task:
							task_ing_map[(tasks[parent]['process_type'], tasks[parent]['product_type'])][
								'parent_tasks'].add(parent)
				list_parents[key]['task_ing_map'] = task_ing_map

			# stores intermediate results of cost and remaining_worth for all tasks to avoid recursive db calls
			initial_costs = Task.objects.filter(is_trashed=False).all()
			final_costs = {}
			for task in initial_costs:
				final_costs[task.id] = {'id': task.id, 'cost': task.cost, 'remaining_worth': task.remaining_worth}
			old_cost = parents[0].cost
			if input_added:
				old_batch_size = tasks[updated_task]['batch_size']
				new_batch_size = tasks[updated_task]['batch_size'] + input_parent[0].batch_size
			else:
				old_batch_size = tasks[updated_task]['batch_size'] + input_parent[0].batch_size
				new_batch_size = tasks[updated_task]['batch_size']
			prev_unit_cost = float(round(old_cost / old_batch_size, 2))
			new_unit_cost = float(round(tasks[updated_task]['cost'] / new_batch_size, 2))

			# calculate difference of unit costs
			unit_cost = new_unit_cost - prev_unit_cost
			# iterate through each child of the updated task and propagate data
			for child in tasks[updated_task]['list_children']:
				if child is not None and child not in faulty_tasks and child in final_costs:
					new_difference = update_cost(updated_task, child, unit_cost, tasks, list_parents, final_costs, input_added)
					# call rec_cost() to propagate values to children of child task if it is present in tasks list
					if child in tasks:
						visited = {}  # handles tasks with circular dependencies
						rec_cost(child, new_difference, final_costs, tasks, faulty_tasks, list_parents, visited, input_added)
	except Exception as e:
		print "except block"
		print(str(e))


# updates cost and remaining worth of tasks and returns new_difference which will be passed to child task
def update_cost(task, child, unit_cost, tasks, list_parents, final_costs, input_added):
	# find number of parent contributing same ingredient to the child task
	num_parents = len(list_parents[child]['task_ing_map'][(tasks[task]['process_type'], tasks[task]['product_type'])]['parent_tasks'])
	# total amount of ingredient associated with the child task
	total_amount = list_parents[child]['task_ing_map'][(tasks[task]['process_type'], tasks[task]['product_type'])]['amount']
	# actual amount to be transferred to the child
	actual_amount = float(total_amount / num_parents)
	new_difference = unit_cost * actual_amount
	final_costs[child]['cost'] = final_costs[child]['cost'] or 0
	final_costs[child]['remaining_worth'] = final_costs[child]['remaining_worth'] or 0
	# updated total cost and remaining_worth associated with the child and parent
	if input_added:
		final_costs[child]['cost'] = float(final_costs[child]['cost']) + new_difference
		final_costs[child]['remaining_worth'] = float(final_costs[child]['remaining_worth']) + new_difference
		final_costs[task]['remaining_worth'] = float(final_costs[task]['remaining_worth']) - new_difference
	else:
		final_costs[child]['cost'] = float(final_costs[child]['cost']) - new_difference
		final_costs[child]['remaining_worth'] = float(final_costs[child]['remaining_worth']) - new_difference
		final_costs[task]['remaining_worth'] = float(final_costs[task]['remaining_worth']) + new_difference
	# update child costs
	Task.objects.filter(pk=child).update(cost=final_costs[child]['cost'], remaining_worth=final_costs[child]['remaining_worth'])
	# update parent task costs
	Task.objects.filter(pk=task).update(remaining_worth=final_costs[task]['remaining_worth'])
	return new_difference


# function to recursively propagate data
def rec_cost(parent, proportional_cost, final_costs, tasks, faulty_tasks, list_parents, visited, input_added):
	# batch_size should not be 0 (when you run script again)
	unit_cost = float(round(proportional_cost / float(tasks[parent]['batch_size']), 2))
	for child in tasks[parent]['list_children']:
		if child is not None and child not in faulty_tasks and child in final_costs and child not in visited:
			visited[child] = child
			new_difference = update_cost(parent, child, unit_cost, tasks, list_parents, final_costs, input_added)
			if child in tasks:
				rec_cost(child, new_difference, final_costs, tasks, faulty_tasks, list_parents, visited, input_added)


# to get the list of tasks which are parent to some tasks and populate required fields in tasks
def parents_list(tasks_with_child, tasks):
	for task in tasks_with_child:
		children = set(task.children_list)
		tasks[task.id] = {'list_children': children, 'process_type': task.process_type_id,
						  'product_type': task.product_type_id, 'cost': task.cost,
						  'remaining_worth': task.remaining_worth, 'batch_size': task.batch_size}


# creates list of all the taskingredients used by each task
def get_ingredients(faulty_tasks, list_parents, parents):
	for child in parents:
		if child.task_parent_ids != [None]:
			list_parents[child.id] = {'parents': set(child.task_parent_ids)}
			list_parents[child.id]['task_ings'] = TaskIngredient.objects.filter(task=child.id)
			if len(list_parents[child.id]['task_ings']) == 0:
				list_parents.pop(child.id)
				faulty_tasks[child.id] = child.id
