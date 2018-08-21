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
			prev_unit_cost, new_unit_cost = update_cost(updated_task, child, prev_unit_cost, new_unit_cost, tasks, descendant_ingredients)
			# call rec_cost() to propagate values to children of child task if it is present in tasks list
			if child in tasks:
				visited = {}  # handles tasks with circular dependencies
				rec_cost(child, prev_unit_cost, new_unit_cost, tasks, visited, descendant_ingredients)


# Make-shift solution: we're unable to filter out rashed tasks in Array Aggs, so we just have to skip em
def task_is_trashed(task, maps_of_non_trashed_tasks):
	for map in maps_of_non_trashed_tasks:
		if task not in map:
			return True
	return False


# updates cost and remaining worth of tasks and returns new_difference which will be passed to child task
def update_cost(parent, child, prev_unit_cost, new_unit_cost, tasks, descendant_ingredients):
	process_type = tasks[parent]['process_type']
	product_type = tasks[parent]['product_type']
	num_parents_for_ingredient = len(descendant_ingredients[child]['task_ing_map'][(process_type, product_type)]['parent_tasks'])
	total_amount_of_ingredient = descendant_ingredients[child]['task_ing_map'][(tasks[parent]['process_type'], tasks[parent]['product_type'])]['amount']
	amount_used_by_child = float(total_amount_of_ingredient / num_parents_for_ingredient)

	cost_now = new_unit_cost * amount_used_by_child
	cost_previously = prev_unit_cost * amount_used_by_child
	parent_cost = float(tasks[parent]['cost'])
	change_in_amount_child_uses = get_capped_utilization_diff(cost_now, cost_previously, parent_cost)

	update_cost_and_remaining_worth_of_child(child, tasks, change_in_amount_child_uses)
	update_remaining_worth_of_parent(parent, tasks, change_in_amount_child_uses)

	return get_prev_and_new_unit_costs_for_child(tasks[child], change_in_amount_child_uses)


def get_prev_and_new_unit_costs_for_child(child, change_in_amount_child_uses):
	cost = child['cost']
	batch_size = child['batch_size']
	prev_unit_cost = get_unit_cost(cost, batch_size)
	new_unit_cost = get_unit_cost(cost + change_in_amount_child_uses, batch_size)
	return prev_unit_cost, new_unit_cost


def parent_has_capacity_to_receive_returned_value(change_in_amount_child_uses, parent_remaining_worth, parent_cost):
	return parent_remaining_worth - parent_cost >= change_in_amount_child_uses


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
def rec_cost(parent, prev_unit_cost, new_unit_cost, tasks, visited, descendant_ingredients):
	for child in tasks[parent]['children']:
		if child is not None and child not in visited:
			visited[child] = child
			prev_unit_cost, new_unit_cost = update_cost(parent, child, prev_unit_cost, new_unit_cost, tasks, descendant_ingredients)
			if child in tasks:
				rec_cost(child, prev_unit_cost, new_unit_cost, tasks, visited, descendant_ingredients)


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

	trashed_task_ids_set = get_trashed_task_ids_set()

	related_tasks_batch_size = Task.objects.filter(is_trashed=False, pk__in=related_tasks).annotate(
		batch_size=Coalesce(Sum('items__amount'), 0))
	related_tasks_with_parents_children = Task.objects.filter(is_trashed=False, pk__in=related_tasks).annotate(
		children_list=ArrayAgg('items__inputs__task'),
		task_parent_ids=ArrayAgg('inputs__input_item__creating_task__id'),
		ingredients=ArrayAgg('task_ingredients__ingredient'))
	tasks = {}
	for x in range(0, related_tasks_with_parents_children.count()):
		tasks[related_tasks_with_parents_children[x].id] = {
			'children': set(related_tasks_with_parents_children[x].children_list) - trashed_task_ids_set,
			'process_type': related_tasks_batch_size[x].process_type_id,
			'ingredients': set(related_tasks_with_parents_children[x].ingredients),
			'product_type': related_tasks_batch_size[x].product_type_id,
			'cost': related_tasks_batch_size[x].cost,
			'parents': set(related_tasks_with_parents_children[x].task_parent_ids) - trashed_task_ids_set,
			'remaining_worth': related_tasks_batch_size[x].remaining_worth,
			'batch_size': related_tasks_batch_size[x].batch_size
		}
	return tasks


#  Not a scalable solution, but even if we doubled our task count we'd likely still have only 3k deleted tasks
def get_trashed_task_ids_set():
	return set(Task.objects.filter(is_trashed=True).values_list('pk', flat=True))


# returns ingredient used by each descendant
def descendant_ingredient_details(updated_task_descendants, tasks):
	descendant_ingredients = {}
	# populate task_ing_map with taskingredients along with all the parents contributing that ingredient for each descendant
	for task in updated_task_descendants:
		key = task.id
		descendant_ingredients[key] = {}
		task_ing_map = {}
		for task_ing in tasks[key]['ingredients']:
			if task_ing is None:
				continue
			ingredient_details = TaskIngredient.objects.filter(task_id=key, ingredient_id=task_ing).values('actual_amount',
																						'ingredient__process_type', 'ingredient__product_type')[0]
			process_type = ingredient_details['ingredient__process_type']
			product_type = ingredient_details['ingredient__product_type']
			task_ing_map[(process_type, product_type)] = {'amount': ingredient_details['actual_amount'], 'parent_tasks': set()}

		for parent in tasks[key]['parents']:
			if task_is_trashed(parent, [tasks]):
				continue
			process_type = tasks[parent]['process_type']
			product_type = tasks[parent]['product_type']
			task_ing_map[(process_type, product_type)]['parent_tasks'].add(parent)
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
	return float(cost) / float(batch_size)


# DELETED TASK HELPERS:

def update_children_of_deleted_task(deleted_task):
	# fetch all the descendants of deleted task
	deleted_task_descendants = get_non_trashed_descendants(Task.objects.filter(pk=deleted_task)[0])
	if not deleted_task_descendants:
		print ("No descendents")
		return
	tasks = task_details(deleted_task_descendants)
	descendant_ingredients = descendant_ingredient_details(deleted_task_descendants, tasks)
	if tasks[deleted_task]['children'] != {None}:
		batch_size = tasks[deleted_task]['batch_size']
		cost = tasks[deleted_task]['cost']
		prev_unit_cost = get_unit_cost(cost, batch_size)
		new_unit_cost = 0
		update_children(new_unit_cost, prev_unit_cost, deleted_task, tasks, descendant_ingredients)


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


def update_parents_for_ingredient(parents_contributing_ingredient, old_amount, new_amount, num_parents, creating_task_of_changed_input=-1, input_added=False, input_deleted=False):
	total_change_in_value_from_all_parents = 0
	for task in parents_contributing_ingredient:
		parent = parents_contributing_ingredient[task]
		if parent.cost is None:
			return

		unit_cost = parent.cost / parent.batch_size
		if task == creating_task_of_changed_input and input_added:
			cost_of_ingredient_used_previously = 0
		else:
			old_avg_amount = old_amount / get_adjusted_num_parents(num_parents, input_added, input_deleted, for_old_amount=True)
			cost_of_ingredient_used_previously = old_avg_amount * unit_cost

		if task == creating_task_of_changed_input and input_deleted:
			cost_of_ingredient_used_now = 0
		else:
			new_avg_amount = new_amount / get_adjusted_num_parents(num_parents, input_added, input_deleted, for_old_amount=False)
			cost_of_ingredient_used_now = new_avg_amount * unit_cost

		utilization_diff = get_capped_utilization_diff(cost_of_ingredient_used_now, cost_of_ingredient_used_previously, parent.cost)
		print("parent cost", parent.cost, "parent batch size", parent.batch_size, "prev util", cost_of_ingredient_used_previously, "new util", cost_of_ingredient_used_now, "utilization diff", utilization_diff)

		new_remaining_worth = parent.remaining_worth - utilization_diff
		total_change_in_value_from_all_parents += utilization_diff

		Task.objects.filter(pk=task).update(remaining_worth=new_remaining_worth)
		print("new remaining", new_remaining_worth, "total diff", total_change_in_value_from_all_parents)
	return total_change_in_value_from_all_parents


def get_adjusted_num_parents(num_parents, input_added, input_deleted, for_old_amount):
	if input_deleted:  # Delete input is calculated pre_delete, where all parents still exist.
		adjusted_num_parents = num_parents if for_old_amount else num_parents - 1
	elif input_added:  # New input is calculated post_save, where all parents exist.
		adjusted_num_parents = num_parents - 1 if for_old_amount else num_parents
	else:
		adjusted_num_parents = num_parents
	return adjusted_num_parents if adjusted_num_parents > 0 else 1


# utilization_diff + remaining_worth must remain with the range of 0 to cost (inclusive).
# In this function, we only return the fraction of the utilization_diff which falls within this range.
# This, for example prevents 100 kgs worth of cost from being added to a parent of batch_size = 100 kgs
# when its only child goes from using 400 kgs to 300 kgs (here, named each_is_greater_than_parent).
def get_capped_utilization_diff(cost_now, cost_previously, parent_cost):
	if each_is_greater_than_parent_cost(cost_now, cost_previously, parent_cost):
		return 0  # no actual change to anyone's cost/value will result, since both exceed parents cost.
	elif one_is_above_and_one_is_below_parent_cost(cost_now, cost_previously, parent_cost):
		if cost_now < cost_previously:
			return cost_now - parent_cost
		elif cost_previously < cost_now:
			return parent_cost - cost_previously
	else:
		return cost_now - cost_previously


def each_is_greater_than_parent_cost(cost_now, cost_previously, parent_cost):
	return cost_now > parent_cost and cost_previously > parent_cost


def one_is_above_and_one_is_below_parent_cost(cost_now, cost_previously, parent_cost):
	now_above_previously = cost_now > parent_cost and cost_previously <= parent_cost
	previously_above_now = cost_now <= parent_cost and cost_previously > parent_cost
	return now_above_previously or previously_above_now


def requires_more_than_remains_in_parent(utilization_diff, parent):
	return utilization_diff > parent.remaining_worth


def child_gives_back_more_than_it_took(utilization_diff, parent):
	return parent.remaining_worth - utilization_diff > parent.cost


# UPDATE INPUT HELPERS

# This is nearly identical to async_action.py/ingredient_amount_update(...), except with special flags to handle
# special cases of introducing or exiting an input.
def handle_input_change_with_no_recipe(kwargs, updated_task_id):
	creating_task_of_changed_input_id = kwargs['creatingTaskID']
	input_added = kwargs['added']
	task_ingredient__actual_amount = kwargs['task_ingredient__actual_amount']
	ingredient_id = kwargs['ingredientID']
	creating_task_of_changed_input = get_creating_task_of_changed_input(creating_task_of_changed_input_id)

	if not creating_task_of_changed_input or creating_task_of_changed_input.cost is None:
		return

	# Adding inputs adds its batch size.
	# Deleting inputs subtracts its batch size. Note: can produce negative amounts in special cases, matching codebase.
	old_amount, new_amount = get_amounts(task_ingredient__actual_amount, creating_task_of_changed_input.batch_size, input_added)
	update_parents_for_ingredient_and_then_child(
		updated_task_id,
		old_amount,
		new_amount,
		ingredient_id,
		creating_task_of_changed_input=creating_task_of_changed_input.id,
		input_added=input_added,
		input_deleted=not input_added,
	)


def get_creating_task_of_changed_input(creating_task_of_changed_input_id):
	query_set = Task.objects.filter(is_trashed=False, pk=creating_task_of_changed_input_id).annotate(
		batch_size=Coalesce(Sum('items__amount'), 0))
	return False if query_set.count() == 0 else query_set[0]  # It's possible the parent is a deleted tasks.


def get_amounts(task_ingredient__actual_amount, batch_size, input_added):
	print('input_added', input_added)
	if input_added:  # which happens post_save
		new_amount = task_ingredient__actual_amount  # we've already updated TaskIngredient
		old_amount = new_amount - batch_size
	else:
		old_amount = task_ingredient__actual_amount  # we've yet to update TaskIngredient
		new_amount = old_amount - batch_size
	print('old amount', old_amount, 'new_amount', new_amount)
	return old_amount, new_amount


def handle_input_change_with_recipe(kwargs, updated_task_id):
	print('Input change with recipe', kwargs['recipe'])


# UPDATE INGREDIENT HELPERS

def get_parents_contributing_ingredient(parent_ids, ingredient_id):
	updated_task_parents = Task.objects.filter(pk__in=set(parent_ids), is_trashed=False).annotate(
		batch_size=Coalesce(Sum('items__amount'), 0))
	ingredient = Ingredient.objects.get(pk=ingredient_id)
	parents_contributing_ingredient = {}
	if parent_ids == [None] or updated_task_parents.count() == 0:
		return {}

	for x in range(0, len(set(parent_ids))):
		if updated_task_parents[x].process_type_id == ingredient.process_type_id and \
						updated_task_parents[x].product_type_id == ingredient.product_type_id:
			parents_contributing_ingredient[updated_task_parents[x].id] = updated_task_parents[x]
	return parents_contributing_ingredient


def update_parents_for_ingredient_and_then_child(updated_task_id, old_amount, new_amount, ingredient_id, creating_task_of_changed_input=-1, input_added=False, input_deleted=False):
	updated_task = Task.objects.filter(is_trashed=False, pk=updated_task_id).annotate(task_parent_ids=ArrayAgg('inputs__input_item__creating_task__id'))[0]
	updated_task.task_parent_ids = remove_trashed_tasks(updated_task.task_parent_ids, get_trashed_task_ids_set())
	parents_contributing_ingredient = get_parents_contributing_ingredient(updated_task.task_parent_ids, ingredient_id)
	num_parents = len(parents_contributing_ingredient)
	total_change_in_value_from_all_parents = update_parents_for_ingredient(parents_contributing_ingredient, old_amount, new_amount, num_parents, creating_task_of_changed_input, input_added, input_deleted)

	old_updated_task_cost = updated_task.cost
	old_updated_task_remaining_worth = updated_task.remaining_worth

	new_updated_task_cost = old_updated_task_cost + total_change_in_value_from_all_parents
	new_updated_task_remaining_worth = old_updated_task_remaining_worth + total_change_in_value_from_all_parents
	Task.objects.filter(pk=updated_task_id).update(cost=new_updated_task_cost, remaining_worth=new_updated_task_remaining_worth)

	update_children_after_amount_update(updated_task_id, old_updated_task_cost, new_updated_task_cost)


def remove_trashed_tasks(task_ids, trashed_task_ids_set):
	return list(set(task_ids) - trashed_task_ids_set)


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
