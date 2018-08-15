from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models.functions import Coalesce

from ics.models import *
from django.db.models import F, Count, Sum


# calculate costs for all the children of current task
def update_children(new_unit_cost, prev_unit_cost, updated_task, tasks, descendant_ingredients):
	# calculate difference of unit costs
	unit_cost_diff = new_unit_cost - prev_unit_cost
	print('unit_cost_diff', unit_cost_diff)
	if unit_cost_diff == 0:
		return
	# iterate through each child of the updated task and propagate data
	for child in tasks[updated_task]['children']:
		if child is not None:
			new_difference = update_cost(updated_task, child, unit_cost_diff, tasks, descendant_ingredients)
			# call rec_cost() to propagate values to children of child task if it is present in tasks list
			if child in tasks:
				visited = {}  # handles tasks with circular dependencies
				rec_cost(child, new_difference, tasks, visited, descendant_ingredients)


# Make-shift solution: we're unable to filter out rashed tasks in ArrayAggs, so we just have to skip em
def task_is_trashed(task, maps_of_non_trashed_tasks):
	for map in maps_of_non_trashed_tasks:
		if task not in map:
			return True
	return False


# updates cost and remaining worth of tasks and returns new_difference which will be passed to child task
def update_cost(task, child, unit_cost_diff, tasks, descendant_ingredients):
	# if task_is_trashed(task, [descendant_ingredients, tasks]) or task_is_trashed(child, [descendant_ingredients, tasks]):
	# 	return 0  # @Aditya, does zero work?
	# find number of parent contributing same ingredient to the child task
	num_parents = len(descendant_ingredients[child]['task_ing_map'][(tasks[task]['process_type'], tasks[task]['product_type'])]['parent_tasks'])
	# total amount of ingredient associated with the child task
	total_amount = descendant_ingredients[child]['task_ing_map'][(tasks[task]['process_type'], tasks[task]['product_type'])]['amount']
	# actual amount to be transferred to the child
	actual_amount = float(total_amount / num_parents)
	new_difference = unit_cost_diff * actual_amount
	print('new_difference', new_difference, 'parent task', task)
	update_cost_and_remaining_worth_of_child(child, tasks, new_difference)
	update_remaining_worth_of_parent(task, tasks, new_difference)
	return new_difference


def update_cost_and_remaining_worth_of_child(child, tasks, new_difference):
	tasks[child]['remaining_worth'] = get_new_dollar_value(tasks[child]['remaining_worth'], new_difference)
	tasks[child]['cost'] = get_new_dollar_value(tasks[child]['cost'], new_difference)
	Task.objects.filter(pk=child).update(cost=tasks[child]['cost'], remaining_worth=tasks[child]['remaining_worth'])


def update_remaining_worth_of_parent(task, tasks, new_difference):
	tasks[task]['remaining_worth'] = get_new_dollar_value(tasks[task]['remaining_worth'], -1 * new_difference)
	Task.objects.filter(pk=task).update(remaining_worth=tasks[task]['remaining_worth'])


# Returns 0 if difference makes value negative
def get_new_dollar_value(curr_value, new_difference_to_add):
	new_dollar_value = float(curr_value or 0) + new_difference_to_add
	return zero_or_greater(new_dollar_value)


def zero_or_greater(number):
	return number if number >= 0 else 0


# function to recursively propagate data
def rec_cost(parent, new_difference, tasks, visited, descendant_ingredients):
	# batch_size should not be 0 (when you run script again)
	unit_cost_diff = get_unit_cost(new_difference, float(tasks[parent]['batch_size']))
	for child in tasks[parent]['children']:
		if child is not None and child not in visited:
			visited[child] = child
			new_difference = update_cost(parent, child, unit_cost_diff, tasks, descendant_ingredients)
			if child in tasks:
				rec_cost(child, new_difference, tasks, visited, descendant_ingredients)


# fetch parents and children for list of related tasks
def task_details(updated_task_descendants):
	# contains task ids of descendants and ids of parents of descendants
	related_tasks = set()
	for task in list(updated_task_descendants):
		related_tasks.add(task.id)
	# for each descendant get parent id
	parents = Task.objects.filter(is_trashed=False, pk__in=related_tasks).annotate(
		task_parent_ids=ArrayAgg('inputs__input_item__creating_task__id'))

	for parent in parents:
		related_tasks = related_tasks.union(parent.task_parent_ids)

	related_tasks_batch_size = Task.objects.filter(is_trashed=False, pk__in=related_tasks).annotate(
		batch_size=Coalesce(Sum('items__amount'), 0))
	related_tasks_with_parents_children = Task.objects.filter(is_trashed=False, pk__in=related_tasks).annotate(
		children_list=ArrayAgg('items__inputs__task'),
		task_parent_ids=ArrayAgg('inputs__input_item__creating_task__id'),
		ingredients=ArrayAgg('task_ingredients__ingredient'))
	tasks = {}
	for x in range(0, related_tasks_with_parents_children.count()):
		tasks[related_tasks_with_parents_children[x].id] = {'children': set(related_tasks_with_parents_children[x].children_list),
						'process_type': related_tasks_batch_size[x].process_type_id,
						'ingredients': set(related_tasks_with_parents_children[x].ingredients),
						'product_type': related_tasks_batch_size[x].product_type_id, 'cost': related_tasks_batch_size[x].cost,
					    'parents': set(related_tasks_with_parents_children[x].task_parent_ids),
				    	'remaining_worth': related_tasks_batch_size[x].remaining_worth, 'batch_size': related_tasks_batch_size[x].batch_size}
	return tasks


# returns ingredient used by each descendant
def descendant_ingredient_details(updated_task_descendants, tasks):
	descendant_ingredients = {}
	# populate task_ing_map with taskingredients along with all the parents contributing that ingredient for each descendant
	for task in updated_task_descendants:
		key = task.id
		descendant_ingredients[key] = {}
		task_ing_map = {}
		for task_ing in tasks[key]['ingredients']:
			ingredient_details = TaskIngredient.objects.filter(task_id=key, ingredient_id=task_ing).values('actual_amount',
																						'ingredient__process_type', 'ingredient__product_type')[0]
			task_ing_map[(ingredient_details['ingredient__process_type'], ingredient_details['ingredient__product_type'])] = {
								'amount': ingredient_details['actual_amount'], 'parent_tasks': set()}
		for parent in tasks[key]['parents']:
			if task_is_trashed(parent, [tasks]):
				continue
			task_ing_map[(tasks[parent]['process_type'], tasks[parent]['product_type'])]['parent_tasks'].add(
				parent)
		descendant_ingredients[key]['task_ing_map'] = task_ing_map
	return descendant_ingredients


def get_non_trashed_descendants(task):
	return Task.descendants(task).filter(is_trashed=False)


# BATCH SIZE UPDATE HELPERS

def get_prev_and_new_unit_costs(task, kwargs):
	new_batch_size = task['batch_size']
	amount_diff = kwargs['new_amount'] - kwargs['previous_amount']
	old_batch_size = new_batch_size - amount_diff
	cost = task['cost']
	prev_unit_cost = get_unit_cost(cost, old_batch_size)
	new_unit_cost = get_unit_cost(cost, new_batch_size)
	print('prev_unit_cost, new_unit_cost')
	print(prev_unit_cost, new_unit_cost)
	return prev_unit_cost, new_unit_cost


def get_unit_cost(cost, batch_size):
	return float(round(cost / batch_size, 2))


# DELETED TASK HELPERS:

def update_parents_of_deleted_task(updated_task_id):
	# get all the ids of ingredients used and parents who contribute those ingredients
	qs = Task.objects.filter(is_trashed=False, pk=updated_task_id).annotate(
		task_parent_ids=ArrayAgg('inputs__input_item__creating_task__id'),
		ingredients=ArrayAgg('task_ingredients__ingredient')
	)
	if qs.count() != 1 or qs[0].ingredients == [None]:
		return
	updated_task = qs[0]
	parent_ids = updated_task.task_parent_ids
	updated_task_parents = Task.objects.filter(pk__in=set(parent_ids)).annotate(
		batch_size=Coalesce(Sum('items__amount'), 0))

	# map ingredients with parents
	ingredients_to_parents_map = {}
	print(updated_task.ingredients)
	for ingredient_id in updated_task.ingredients:
		ingredient = Ingredient.objects.get(pk=ingredient_id)
		parents_contributing_ingredient = {}
		for x in range(0, len(set(parent_ids))):
			if updated_task_parents[x].process_type_id == ingredient.process_type_id and \
							updated_task_parents[x].product_type_id == ingredient.product_type_id:
				parents_contributing_ingredient[updated_task_parents[x].id] = updated_task_parents[x]
		ingredients_to_parents_map[ingredient.id] = parents_contributing_ingredient

	# iterate over each ingredient
	print(ingredients_to_parents_map)
	for ingredient_id, parents_contributing_ingredient in ingredients_to_parents_map.iteritems():
		old_amount = TaskIngredient.objects.filter(ingredient_id=ingredient_id).values('actual_amount')[0]['actual_amount']
		new_amount = 0
		num_parents = len(parents_contributing_ingredient)
		update_parents_for_ingredient(parents_contributing_ingredient, old_amount, new_amount, num_parents)


def update_parents_for_ingredient(parents_contributing_ingredient, old_amount, new_amount, num_parents, creating_task=-1,
								  input_added=False, input_deleted=False):
	old_avg_amount = old_amount / num_parents
	new_avg_amount = new_amount / num_parents
	total_change_in_value_from_all_parents = 0
	print(parents_contributing_ingredient)
	for task in parents_contributing_ingredient:
		parent = parents_contributing_ingredient[task]
		if parent.cost is None:
			return

		unit_cost = parent.cost / parent.batch_size

		cost_or_ingredient_used_previously = old_avg_amount * unit_cost
		if task == creating_task and input_added:
			cost_or_ingredient_used_previously = 0

		cost_of_ingredient_used_now = new_avg_amount * unit_cost
		if task == creating_task and input_deleted:
			cost_of_ingredient_used_now = 0

		utilization_diff = cost_of_ingredient_used_now - cost_or_ingredient_used_previously
		print("parent cost", parent.cost, "parent batch size", parent.batch_size, "prev util", cost_or_ingredient_used_previously, "new util", cost_of_ingredient_used_now, "utilization diff", utilization_diff)

		if requires_more_than_remains_in_parent(utilization_diff, parent):
			new_remaining_worth = 0
			total_change_in_value_from_all_parents += parent.remaining_worth
		elif child_gives_back_more_than_it_took(utilization_diff, parent):
			new_remaining_worth = min(parent.remaining_worth - utilization_diff, parent.cost)
			total_change_in_value_from_all_parents += new_remaining_worth - parent.remaining_worth
		else:  # barring 2 extreme cases above requiring capping, simply use utilization_diff
			new_remaining_worth = parent.remaining_worth - utilization_diff
			total_change_in_value_from_all_parents += utilization_diff

		Task.objects.filter(pk=task).update(remaining_worth=new_remaining_worth)
		print("new remaining", new_remaining_worth, "total diff", total_change_in_value_from_all_parents)
	return total_change_in_value_from_all_parents


def requires_more_than_remains_in_parent(utilization_diff, parent):
	return utilization_diff > parent.remaining_worth


def child_gives_back_more_than_it_took(utilization_diff, parent):
	return parent.remaining_worth - utilization_diff > parent.cost


def update_children_of_deleted_task(deleted_task):
	# fetch all the descendants of deleted task
	deleted_task_descendants = get_non_trashed_descendants(Task.objects.filter(pk=deleted_task)[0])
	if not deleted_task_descendants:
		print ("No descendents")
		return
	tasks = task_details(deleted_task_descendants)
	descendant_ingredients = descendant_ingredient_details(deleted_task_descendants, tasks)
	if tasks[deleted_task]['children'] != set([None]):
		batch_size = tasks[deleted_task]['batch_size']
		cost = tasks[deleted_task]['cost']
		prev_unit_cost = get_unit_cost(cost, batch_size)
		new_unit_cost = 0
		update_children(new_unit_cost, prev_unit_cost, deleted_task, tasks, descendant_ingredients)


# UPDATE INPUT HELPERS

def handle_input_change_with_no_recipe(kwargs, updated_task, updated_task_id):
	input_creating_task = kwargs['creatingTaskID']
	input_added = kwargs['added']
	# fetch task which created the input
	input_parent = Task.objects.filter(is_trashed=False, pk=input_creating_task).annotate(
		batch_size=Coalesce(Sum('items__amount'), 0))[0]
	if input_parent.cost is None:
		return
	if input_added:
		print('input added...')
		new_updated_task_cost = updated_task.cost + input_parent.remaining_worth
		new_updated_task_remaining_worth = updated_task.remaining_worth + input_parent.remaining_worth
		parent_remaining_worth = 0
	else:  # input deleted
		# TO DO: deleting an input automatically subtracts the FULL batch_size from the TaskIngredient
		# We should re-distribute value to all other Parent Inputs of this ingredient type
		new_updated_task_cost = updated_task.cost + input_parent.cost - input_parent.remaining_worth
		new_updated_task_remaining_worth = updated_task.remaining_worth + input_parent.cost - input_parent.remaining_worth
		parent_remaining_worth = input_parent.cost
	print('new_updated_task_cost', new_updated_task_cost, 'new_updated_task_remaining_worth', new_updated_task_remaining_worth, 'parent_remaining_worth', parent_remaining_worth)
	Task.objects.filter(pk=input_creating_task).update(remaining_worth=parent_remaining_worth)
	Task.objects.filter(pk=updated_task_id).update(cost=new_updated_task_cost, remaining_worth=new_updated_task_remaining_worth)


# UPDATE INGREDIENT HELPERS

def get_parents_contributing_ingredient(parent_ids, ingredient_id):
	updated_task_parents = Task.objects.filter(pk__in=set(parent_ids)).annotate(
		batch_size=Coalesce(Sum('items__amount'), 0))
	ingredient = Ingredient.objects.get(pk=ingredient_id)
	parents_contributing_ingredient = {}
	for x in range(0, len(set(parent_ids))):
		if updated_task_parents[x].process_type_id == ingredient.process_type_id and \
						updated_task_parents[x].product_type_id == ingredient.product_type_id:
			parents_contributing_ingredient[updated_task_parents[x].id] = updated_task_parents[x]
	return parents_contributing_ingredient


def update_children_after_amount_update(updated_task_id, old_updated_task_cost, new_updated_task_cost):
	updated_task_descendants = get_non_trashed_descendants(Task.objects.filter(pk=updated_task_id)[0])
	if updated_task_descendants.count() == 0:
		return
	tasks = task_details(updated_task_descendants)
	descendant_ingredients = descendant_ingredient_details(updated_task_descendants, tasks)
	batch_size = tasks[updated_task_id]['batch_size']
	prev_unit_cost = get_unit_cost(old_updated_task_cost, batch_size)
	new_unit_cost = get_unit_cost(new_updated_task_cost, batch_size)

	update_children(new_unit_cost, prev_unit_cost, updated_task_id, tasks, descendant_ingredients)
