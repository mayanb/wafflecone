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
# @Maya
# this function will be altered this afternoon when we handle recipe changes
@task
def input_update(**kwargs):
	# when recipe is defined
	recipe = kwargs['recipe']
	if recipe is None:
		updated_task = kwargs['taskID']
		input_creating_task = kwargs['creatingTaskID']
		input_added = kwargs['added']
		# fetch updated_task object with it's parents
		updated_task_with_parents = Task.objects.filter(is_trashed=False, pk=updated_task).annotate(
			task_parent_ids=ArrayAgg('inputs__input_item__creating_task__id'))[0]
		# fetch task which created the input
		input_parent = Task.objects.filter(is_trashed=False, pk=input_creating_task).annotate(
					batch_size=Coalesce(Sum('items__amount'), 0))[0]
		if input_parent.cost is None:
			return
		if input_added:
			new_updated_task_cost = updated_task_with_parents.cost + input_parent.remaining_worth
			new_updated_task_remaining_worth = updated_task_with_parents.remaining_worth + input_parent.remaining_worth
			parent_remaining_worth = 0
		else:
			new_updated_task_cost = updated_task_with_parents.cost + input_parent.cost - input_parent.remaining_worth
			new_updated_task_remaining_worth = updated_task_with_parents.remaining_worth + input_parent.cost - input_parent.remaining_worth
			parent_remaining_worth = input_parent.cost
		# Task.objects.filter(pk=input_creating_task).update(remaining_worth=parent_remaining_worth)
		# Task.objects.filter(pk=updated_task).update(cost=new_updated_task_cost, remaining_worth=new_updated_task_remaining_worth)
	# recipe not defined
	else:
		updated_task_id = kwargs['taskID']
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
		updated_task_with_parents = Task.objects.filter(is_trashed=False, pk=updated_task_id).annotate(
			task_parent_ids=ArrayAgg('inputs__input_item__creating_task__id'))[0]

		#***************#
		updated_task = Task.objects.filter(is_trashed=False, pk=updated_task_id).annotate(
			task_parent_ids=ArrayAgg('inputs__input_item__creating_task__id'))[0]
		parent_ids = updated_task.task_parent_ids
		updated_task_parents = Task.objects.filter(pk__in=set(parent_ids)).annotate(
			batch_size=Coalesce(Sum('items__amount'), 0))
		ingredient = Ingredient.objects.get(pk=ingredient_id)
		parents_contributing_ingredient = {}
		for x in range(0, len(set(parent_ids))):
			if updated_task_parents[x].process_type_id == ingredient.process_type_id and \
					updated_task_parents[x].product_type_id == ingredient.product_type_id:
				parents_contributing_ingredient[updated_task_parents[x].id] = updated_task_parents[x]

		if input_added:
			if similar_inputs < 2:
				parent_unit_cost = input_parent.cost/input_parent.batch_size
				parent_contribution = min(parent_unit_cost * scaled_amount, input_parent.reamaining_worth)
				parent_remaining_worth = input_parent.reamaining_worth - parent_contribution
				new_updated_task_cost = updated_task_with_parents.cost + parent_contribution
				new_updated_task_remaining_worth = updated_task_with_parents.remaining_worth + parent_contribution
				# Task.objects.filter(pk=input_creating_task).update(remaining_worth=parent_remaining_worth)
				# Task.objects.filter(pk=updated_task).update(cost=new_updated_task_cost, remaining_worth=new_updated_task_remaining_worth)
			else:
				num_parents = len(parents_contributing_ingredient) - 1
				total_diff = update_parents_for_ingredient(parents_contributing_ingredient, actual_amount, actual_amount, num_parents,
														   input_creating_task, True)

				old_updated_task_cost = updated_task.cost
				old_updated_task_remaining_worth = updated_task.remaining_worth
				new_updated_task_cost = old_updated_task_cost + total_diff
				new_updated_task_remaining_worth = old_updated_task_remaining_worth + total_diff
				# Task.objects.filter(pk=updated_task_id).update(cost=new_updated_task_cost, remaining_worth=new_updated_task_remaining_worth)
		else:
			if similar_inputs < 1:
				parent_unit_cost = input_parent.cost / input_parent.batch_size
				parent_contribution = min(parent_unit_cost * scaled_amount, input_parent.cost)
				parent_remaining_worth = input_parent.reamaining_worth + parent_contribution
				new_updated_task_cost = updated_task_with_parents.cost - parent_contribution
				new_updated_task_remaining_worth = updated_task_with_parents.remaining_worth - parent_contribution
				# Task.objects.filter(pk=input_creating_task).update(remaining_worth=parent_remaining_worth)
				# Task.objects.filter(pk=updated_task).update(cost=new_updated_task_cost, remaining_worth=new_updated_task_remaining_worth)
			else:
				num_parents = len(parents_contributing_ingredient) + 1
				total_diff = update_parents_for_ingredient(parents_contributing_ingredient, actual_amount, actual_amount, num_parents,
														   input_creating_task, False, True)

				old_updated_task_cost = updated_task.cost
				old_updated_task_remaining_worth = updated_task.remaining_worth
				new_updated_task_cost = old_updated_task_cost + total_diff
				new_updated_task_remaining_worth = old_updated_task_remaining_worth + total_diff
				# Task.objects.filter(pk=updated_task_id).update(cost=new_updated_task_cost, remaining_worth=new_updated_task_remaining_worth)

	try:
		# update descendants
		# fetch all the descendants of updated task
		updated_task_descendants = get_non_trashed_descendants(Task.objects.filter(pk=updated_task)[0])
		if updated_task_descendants.count() == 0:
			return
		old_cost = updated_task_with_parents.cost
		tasks = task_details(updated_task_descendants)
		descendant_ingredients = descendant_ingredient_details(updated_task_descendants, tasks)

		batch_size = tasks[updated_task]['batch_size']
		prev_unit_cost = float(round(old_cost / batch_size, 2))
		new_unit_cost = float(round(tasks[updated_task]['cost'] / batch_size, 2))
		# call update_children to update costs of all updated_task's children
		update_children(new_unit_cost, prev_unit_cost, updated_task, tasks, descendant_ingredients)

	except Exception as e:
		print "except block"
		print(str(e))


def ingredient_amount_update(**kwargs):
	TaskIngredient.objects.filter(pk=kwargs['task_ing_id']).update(was_amount_changed=False)
	# update parents and updated_task
	updated_task_id = kwargs['taskID']
	updated_task = Task.objects.filter(is_trashed=False, pk=updated_task_id).annotate(
		task_parent_ids=ArrayAgg('inputs__input_item__creating_task__id'))[0]
	parent_ids = updated_task.task_parent_ids
	updated_task_parents = Task.objects.filter(pk__in=set(parent_ids)).annotate(
		batch_size=Coalesce(Sum('items__amount'), 0))
	ingredient = Ingredient.objects.get(pk=kwargs['ingredientID'])
	parents_contributing_ingredient = {}
	for x in range(0, len(set(parent_ids))):
		if updated_task_parents[x].process_type_id == ingredient.process_type_id and \
				updated_task_parents[x].product_type_id == ingredient.product_type_id:
			parents_contributing_ingredient[updated_task_parents[x].id] = updated_task_parents[x]
	if len(parents_contributing_ingredient) < 2:
		return
	old_amount = kwargs['previous_amount']
	new_amount = kwargs['actual_amount']
	num_parents = len(parents_contributing_ingredient)

	total_diff = update_parents_for_ingredient(parents_contributing_ingredient, old_amount, new_amount, num_parents)
	old_updated_task_cost = updated_task.cost
	old_updated_task_remaining_worth = updated_task.remaining_worth
	new_updated_task_cost = old_updated_task_cost + total_diff
	new_updated_task_remaining_worth = old_updated_task_remaining_worth + total_diff
	# Task.objects.filter(pk=updated_task_id).update(cost=new_updated_task_cost, remaining_worth=new_updated_task_remaining_worth)

	# update children
	# fetch all the descendants of updated task
	updated_task_descendants = get_non_trashed_descendants(Task.objects.filter(pk=updated_task_id)[0])
	if updated_task_descendants.count() == 0:
		return
	tasks = task_details(updated_task_descendants)
	descendant_ingredients = descendant_ingredient_details(updated_task_descendants, tasks)
	batch_size = tasks[updated_task_id]['batch_size']
	prev_unit_cost = float(round(old_updated_task_cost / batch_size, 2))
	new_unit_cost = float(round(new_updated_task_cost / batch_size, 2))
	# call update_children to update costs of all updated_task's children
	# update_children(new_unit_cost, prev_unit_cost, updated_task_id, tasks, descendant_ingredients)


# calculate cost of current task and propagate changes when batch size changed
def batch_size_update(**kwargs):
	updated_task = kwargs['pk']
	# fetch all the descendants of updated task
	updated_task_descendants = get_non_trashed_descendants(Task.objects.filter(pk=updated_task)[0])
	if updated_task_descendants.count() == 0:
		return
	tasks = task_details(updated_task_descendants)
	descendant_ingredients = descendant_ingredient_details(updated_task_descendants, tasks)
	new_batch_size = tasks[updated_task]['batch_size']
	cost = tasks[updated_task]['cost']
	amount_diff = kwargs['new_amount'] - kwargs['previous_amount']
	old_batch_size = new_batch_size - amount_diff
	prev_unit_cost = float(round(cost / old_batch_size, 2))
	new_unit_cost = float(round(cost / new_batch_size, 2))
	update_children(new_unit_cost, prev_unit_cost, updated_task, tasks, descendant_ingredients)


# calculate costs for all the children of current task
def update_children(new_unit_cost, prev_unit_cost, updated_task, tasks, descendant_ingredients):
	# calculate difference of unit costs
	unit_cost = new_unit_cost - prev_unit_cost
	# iterate through each child of the updated task and propagate data
	for child in tasks[updated_task]['children']:
		if child is not None:
			new_difference = update_cost(updated_task, child, unit_cost, tasks, descendant_ingredients)
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
def update_cost(task, child, unit_cost, tasks, descendant_ingredients):
	if task_is_trashed(task, [descendant_ingredients, tasks]) or task_is_trashed(child, [descendant_ingredients, tasks]):
		return 0  # @Aditya, does zero work?
	# find number of parent contributing same ingredient to the child task
	num_parents = len(descendant_ingredients[child]['task_ing_map'][(tasks[task]['process_type'], tasks[task]['product_type'])]['parent_tasks'])
	# total amount of ingredient associated with the child task
	total_amount = descendant_ingredients[child]['task_ing_map'][(tasks[task]['process_type'], tasks[task]['product_type'])]['amount']
	# actual amount to be transferred to the child
	actual_amount = float(total_amount / num_parents)
	new_difference = unit_cost * actual_amount
	tasks[child]['cost'] = tasks[child]['cost'] or 0
	tasks[child]['remaining_worth'] = tasks[child]['remaining_worth'] or 0
	# updated total cost and remaining_worth associated with the child and parent
	print "new difference"
	print new_difference
	tasks[child]['cost'] = float(tasks[child]['cost']) + new_difference
	tasks[child]['remaining_worth'] = float(tasks[child]['remaining_worth']) + new_difference
	tasks[task]['remaining_worth'] = float(tasks[task]['remaining_worth']) - new_difference
	# update child costs
	Task.objects.filter(pk=child).update(cost=tasks[child]['cost'], remaining_worth=tasks[child]['remaining_worth'])
	# update parent task costs
	Task.objects.filter(pk=task).update(remaining_worth=tasks[task]['remaining_worth'])
	return new_difference


# function to recursively propagate data
def rec_cost(parent, proportional_cost, tasks, visited, descendant_ingredients):
	# batch_size should not be 0 (when you run script again)
	unit_cost = float(round(proportional_cost / float(tasks[parent]['batch_size']), 2))
	for child in tasks[parent]['children']:
		if child is not None and child not in visited:
			visited[child] = child
			new_difference = update_cost(parent, child, unit_cost, tasks, descendant_ingredients)
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


# MAIN: updates costs when task is deleted
def task_deleted_update_cost(deleted_task):
	update_parents_of_deleted_task(deleted_task.id)
	update_children_of_deleted_task(deleted_task.id)


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
	total_diff = 0
	print parents_contributing_ingredient
	for task in parents_contributing_ingredient:
		if parents_contributing_ingredient[task].cost is None:
			return
		print "parent cost"
		print parents_contributing_ingredient[task].cost
		print "parent batch size"
		print parents_contributing_ingredient[task].batch_size
		unit_cost = parents_contributing_ingredient[task].cost / parents_contributing_ingredient[task].batch_size
		# cost of ingredient used previously
		prev_utilization = old_avg_amount * unit_cost
		if task == creating_task and input_added:
			prev_utilization = 0
		# cost of ingredient used now
		new_utilization = new_avg_amount * unit_cost
		if task == creating_task and input_deleted:
			new_utilization = 0
		print "prev util"
		print prev_utilization
		print "new util"
		print new_utilization
		utilization_diff = new_utilization - prev_utilization
		print "utilization diff"
		print utilization_diff
		if utilization_diff > parents_contributing_ingredient[task].remaining_worth:
			print "if"
			new_remaining_worth = 0
			total_diff += parents_contributing_ingredient[task].remaining_worth
		elif parents_contributing_ingredient[task].remaining_worth - utilization_diff < parents_contributing_ingredient[task].cost:
			print "elif"
			new_remaining_worth = parents_contributing_ingredient[task].remaining_worth - utilization_diff
			total_diff += utilization_diff
		else:
			print "else"
			new_remaining_worth = parents_contributing_ingredient[task].cost
			total_diff += parents_contributing_ingredient[task].remaining_worth - parents_contributing_ingredient[task].cost
		# Task.objects.filter(pk=task).update(remaining_worth=new_remaining_worth)
		print "new remaining"
		print new_remaining_worth
		print "total diff"
		print total_diff
	return total_diff


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
		prev_unit_cost = float(round(cost / batch_size, 2))
		new_unit_cost = 0
		# print("cost: %d, batch_size: %d, prev_unit_cost: %d, new_unit_cost: %d" % (cost, batch_size, prev_unit_cost, new_unit_cost))
		update_children(new_unit_cost, prev_unit_cost, deleted_task, tasks, descendant_ingredients)


def get_non_trashed_descendants(task):
	return Task.descendants(task).filter(is_trashed=False)
