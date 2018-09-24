from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models.functions import Coalesce

from ics.models import *
from django.db.models import F, Count, Sum, Q


# RECURSIVE FUNCTION A: retrieves descendants and labels them with meta data (if needed), calls (B)
def execute_task_cost_update(updated_task_id, previous_cost, new_cost, tasks=None, descendant_ingredients=None):
	if not (tasks and descendant_ingredients):
		# Include updated_task in descendants for later use (not because it's deleted), e.g. its children, cost etc
		_updated_task_descendants = get_non_trashed_descendants(updated_task_id, include_even_if_deleted=updated_task_id)
		if _updated_task_descendants.count() == 0:
			return

		tasks = task_details(_updated_task_descendants)
		descendant_ingredients = descendant_ingredient_details(_updated_task_descendants, tasks)

	batch_size = float(tasks[updated_task_id]['batch_size'])
	prev_unit_cost = get_unit_cost(previous_cost, batch_size)
	new_unit_cost = get_unit_cost(new_cost, batch_size)
	update_parent_and_children_recursively(new_unit_cost, prev_unit_cost, updated_task_id, tasks, descendant_ingredients, batch_size, batch_size)


# RECURSIVE FUNCTION B: given the changes in the parent_task, propagates that cost change to descendants by calling (A)
# Iterate over each direct child in the order inputs were added, calculating how much worth they were given previously
# and how much worth they get now (post batch_size/ingredient/cost/input change).
# Since we don't know if future children might return worth to the parent or a child might take more worth,
# we begin the 'simulation' with parent.remaining_worth = parent.cost, and decrement as we go, recreating the order
# worth was originally assigned, but updating worth based on recent changes.
def update_parent_and_children_recursively(
				new_unit_cost,
				prev_unit_cost,
				parent_id,
				tasks,
				descendant_ingredients,
				parent_previous_batch_size,
				parent_new_batch_size,
				child_with_changed_ingredient_amount=None,
				previous_total_amount_of_ingredient_for_child=None,
				new_total_amount_of_ingredient_for_child=None,
				input_deleted=False,
				input_added=False,
				creating_task_of_changed_input=-1):
	parent = tasks[parent_id]
	direct_children_in_input_order = parent['direct_children_in_input_order']
	if len(direct_children_in_input_order) is 0:
		return
	is_changed_inputs_parent = parent_id == creating_task_of_changed_input
	an_input_was_added_from_this_parent = is_changed_inputs_parent and input_added
	an_input_was_deleted_from_this_parent = is_changed_inputs_parent and input_deleted

	parent['remaining_worth'] = parent['cost']
	for direct_child in direct_children_in_input_order:
		is_a_deleted_input = child_is_a_deleted_input(direct_child, child_with_changed_ingredient_amount, input_deleted)
		is_a_new_input = child_is_a_new_input(direct_child, child_with_changed_ingredient_amount, input_added)
		adding_this_parent_as_input = is_a_new_input and an_input_was_added_from_this_parent
		deleting_this_parent_as_input = is_a_deleted_input and an_input_was_deleted_from_this_parent

		num_parents = {
			'previous': get_adjusted_num_parents(parent, direct_child, descendant_ingredients, is_a_new_input, is_a_deleted_input, previous=True),
			'now': get_adjusted_num_parents(parent, direct_child, descendant_ingredients, is_a_new_input, is_a_deleted_input),
		}

		previous_total_amount_of_ingredient = None
		new_total_amount_of_ingredient = None
		if direct_child == child_with_changed_ingredient_amount:
			# Helps handle input deletions/additions and ingredient amount changes.
			previous_total_amount_of_ingredient = previous_total_amount_of_ingredient_for_child
			new_total_amount_of_ingredient = new_total_amount_of_ingredient_for_child

		cost_previously_from_parent, cost_now_from_parent, parent_previous_batch_size, parent_new_batch_size = get_previous_and_new_cost_for_child(
			parent_id, direct_child, tasks, descendant_ingredients, parent_previous_batch_size, parent_new_batch_size,
			new_unit_cost, prev_unit_cost, previous_total_amount_of_ingredient, new_total_amount_of_ingredient, num_parents,
			deleting_this_parent_as_input, adding_this_parent_as_input
		)

		change_in_worth_child_uses = float(cost_now_from_parent - cost_previously_from_parent)
		update_child_cost_in_db_and_parent_locally(parent_id, direct_child, tasks, change_in_worth_child_uses, cost_now_from_parent)

		total_child_cost_now = tasks[direct_child]['cost']
		total_child_cost_previously = total_child_cost_now - change_in_worth_child_uses
		if direct_child in tasks:
			execute_task_cost_update(direct_child, total_child_cost_previously, total_child_cost_now, tasks=tasks, descendant_ingredients=descendant_ingredients)
		else:
			execute_task_cost_update(direct_child, total_child_cost_previously, cost_now_from_parent)

	# Each child can potentially adjust the remaining worth of the parent (locally), do a single final DB save
	Task.objects.filter(pk=parent_id).update(remaining_worth=parent['remaining_worth'])


def get_adjusted_num_parents(parent_obj, child_id, descendant_ingredients, is_a_new_input=False, is_a_deleted_input=False, previous=False):
	process_type = parent_obj['process_type']
	product_type = parent_obj['product_type']
	task_ing_map = descendant_ingredients[child_id]['task_ing_map']
	num_parents = len(task_ing_map[(process_type, product_type)]['parent_tasks'])
	if is_a_deleted_input:  # Delete input is calculated pre_delete, where all parents still exist.
		adjusted_num_parents = num_parents if previous else num_parents - 1
	elif is_a_new_input:  # New input is calculated post_save, where all parents exist.
		adjusted_num_parents = num_parents - 1 if previous else num_parents
	else:
		adjusted_num_parents = num_parents
	return adjusted_num_parents if adjusted_num_parents > 0 else 1


def child_is_a_deleted_input(direct_child, child_with_changed_ingredient_amount, input_deleted):
	return direct_child == child_with_changed_ingredient_amount and input_deleted


def child_is_a_new_input(direct_child, child_with_changed_ingredient_amount, input_added):
	return direct_child == child_with_changed_ingredient_amount and input_added


# Takes into account the fact that the child can only receive up to the amount the parent has remaining
# in its batch_size (that is, not already used by earlier inputs).
def get_previous_and_new_cost_for_child(updated_task, direct_child, tasks, descendant_ingredients, parent_previous_batch_size, parent_new_batch_size, new_unit_cost, prev_unit_cost, previous_total_amount_of_ingredient, new_total_amount_of_ingredient, num_parents, deleting_this_parent_as_input, adding_this_parent_as_input):
	# Calculate new/previous amount used by child
	previous_actual_amount_used_by_child = get_actual_amount_used_by_child(updated_task, direct_child, tasks, descendant_ingredients, parent_previous_batch_size, num_parents['previous'], previous_total_amount_of_ingredient)
	new_actual_amount_used_by_child = get_actual_amount_used_by_child(updated_task, direct_child, tasks, descendant_ingredients, parent_new_batch_size, num_parents['now'], new_total_amount_of_ingredient)

	if deleting_this_parent_as_input:
		new_actual_amount_used_by_child = 0
	elif adding_this_parent_as_input:
		previous_actual_amount_used_by_child = 0

	parent_previous_batch_size -= previous_actual_amount_used_by_child
	parent_new_batch_size -= new_actual_amount_used_by_child

	# Calculate new/previous costs, subtracting previous_cost from parents so update_cost knows how much worth
	# remains in the parent which can be assigned to this child.
	cost_previously = prev_unit_cost * previous_actual_amount_used_by_child
	cost_now = new_unit_cost * new_actual_amount_used_by_child
	return cost_previously, cost_now, parent_previous_batch_size, parent_new_batch_size


def get_actual_amount_used_by_child(updated_task, direct_child, tasks, descendant_ingredients, parent_remaining_batch_size, num_parents_for_ingredient, total_amount_of_ingredient=None):
	child_desired_ingredient_amount = get_child_desired_ingredient_amount(updated_task, direct_child, tasks, descendant_ingredients, num_parents_for_ingredient, total_amount_of_ingredient)
	return float(min(parent_remaining_batch_size, child_desired_ingredient_amount))


def get_child_desired_ingredient_amount(parent, child, tasks, descendant_ingredients, num_parents_for_ingredient, total_amount_of_ingredient=None):
	process_type = tasks[parent]['process_type']
	product_type = tasks[parent]['product_type']
	task_ing_map = descendant_ingredients[child]['task_ing_map']
	# For Ingredient Amount change or input change we need to specify previous/new ingredient amount
	total_amount_of_ingredient = total_amount_of_ingredient or task_ing_map[(process_type, product_type)]['amount']
	return float(total_amount_of_ingredient / num_parents_for_ingredient)


def get_direct_children_in_input_order(parent, direct_children):
	return Input.objects.filter(input_item__creating_task=parent, task__in=direct_children).order_by('id').values_list('task', flat=True)


# Make-shift solution: we're unable to filter out rashed tasks in Array Aggs, so we just have to skip em
def task_is_trashed(task, maps_of_non_trashed_tasks):
	for map in maps_of_non_trashed_tasks:
		if task not in map:
			return True
	return False


# updates cost and remaining worth of tasks and returns new_difference which will be passed to child task
def update_child_cost_in_db_and_parent_locally(parent_id, child, tasks, change_in_worth_child_uses, cost_now_from_parent):
	parent = tasks[parent_id]
	parent_remaining_worth = parent['remaining_worth']
	update_cost_and_remaining_worth_of_child(child, tasks, change_in_worth_child_uses, parent_remaining_worth)
	update_remaining_worth_of_parent_locally(parent_id, tasks, cost_now_from_parent)


def parent_has_capacity_to_receive_returned_value(change_in_amount_child_uses, parent_remaining_worth, parent_cost):
	return parent_remaining_worth - parent_cost >= change_in_amount_child_uses


def update_cost_and_remaining_worth_of_child(child, tasks, new_difference, parent_remaining_worth):
	new_difference = min(new_difference, parent_remaining_worth)
	tasks[child]['remaining_worth'] = add_dollar_values(tasks[child]['remaining_worth'], new_difference)
	tasks[child]['cost'] = add_dollar_values(tasks[child]['cost'], new_difference)
	Task.objects.filter(pk=child).update(cost=tasks[child]['cost'], remaining_worth=tasks[child]['remaining_worth'])


def update_remaining_worth_of_parent_locally(parent_id, tasks, cost_now_from_parent):
	parent = tasks[parent_id]
	cost = parent['cost']
	parent['remaining_worth'] = add_dollar_values(parent['remaining_worth'], -1 * cost_now_from_parent, upper_limit=cost)


# Returns 0 if difference makes value negative
def add_dollar_values(curr_value, new_difference_to_add, upper_limit=None):
	new_dollar_value = float(curr_value or 0) + float(new_difference_to_add)
	result = max(new_dollar_value, 0)
	if upper_limit is not None:
		result = min(result, upper_limit)
	return result


# Fetch parents and children related tasks. Don't filter out trashed tasks, since we may be updating cost
# for a newly deleted task, and we've already carefully filtered out unwanted tasks from updated_task_descendants.
def task_details(updated_task_descendants, include_even_if_deleted=-1):
	# contains task ids of descendants and ids of parents of descendants
	related_tasks = set()
	for task in list(updated_task_descendants):
		related_tasks.add(task.id)
	# for each descendant get parent id
	parents = Task.objects.filter(pk__in=related_tasks).annotate(
		task_parent_ids=ArrayAgg('inputs__input_item__creating_task__id'))

	for parent in parents:
		related_tasks = related_tasks.union(parent.task_parent_ids)

	related_tasks_batch_size = Task.objects.filter(pk__in=related_tasks).annotate(
		batch_size=Coalesce(Sum('items__amount'), 0)).order_by('id')
	related_tasks_with_parents_children = Task.objects.filter(pk__in=related_tasks).annotate(
		children_list=ArrayAgg('items__inputs__task'),
		task_parent_ids=ArrayAgg('inputs__input_item__creating_task__id'),
		ingredients=ArrayAgg('task_ingredients__ingredient')).order_by('id')
	tasks = {}
	for x in range(0, related_tasks_with_parents_children.count()):
		task = related_tasks_with_parents_children[x]
		non_trashed_direct_children = set(list(Task.objects.filter(is_trashed=False, pk__in=task.children_list).values_list('pk', flat=True)))
		direct_children_in_input_order = get_direct_children_in_input_order(task.id, non_trashed_direct_children)
		parent_ids = task.task_parent_ids
		non_trashed_parents = set(list(Task.objects.filter(is_trashed=False, pk__in=parent_ids).values_list('pk', flat=True)))

		tasks[task.id] = {
			'direct_children_in_input_order': direct_children_in_input_order,
			'process_type': related_tasks_batch_size[x].process_type_id,
			'ingredients': set(task.ingredients),
			'product_type': related_tasks_batch_size[x].product_type_id,
			'cost': related_tasks_batch_size[x].cost,
			'parents': non_trashed_parents,
			'remaining_worth': related_tasks_batch_size[x].remaining_worth,
			'batch_size': related_tasks_batch_size[x].batch_size
		}
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


def get_non_trashed_descendants(task, include_even_if_deleted=-1):
	desc = Task.objects.get(pk=task).descendants(breakIfCycle=True)
	if desc is None:
		return Task.objects.none()
	else:
		return desc.union(Task.objects.filter(pk=include_even_if_deleted))


def get_unit_cost(cost, batch_size):
	if float(batch_size) == 0:
		return 0.000
	return float(cost) / float(batch_size)


# UPDATE INPUT HELPERS

def get_creating_task_of_changed_input(creating_task_of_changed_input_id):
	query_set = Task.objects.filter(is_trashed=False, pk=creating_task_of_changed_input_id).annotate(
		batch_size=Coalesce(Sum('items__amount'), 0))
	return False if query_set.count() == 0 else query_set[0]  # It's possible the parent is a deleted tasks.


# Adding inputs adds its batch size. Deleting inputs subtracts its batch size.
# Note: this can produce negative amounts in special cases, matching codebase.
def get_amounts(task_ingredient__actual_amount, input_item__amount, input_added, recipe_exists_for_ingredient, adding_first_or_deleting_last_input):
	if input_added:  # which happens post_save
		new_amount_of_ingredient = task_ingredient__actual_amount  # we've already updated TaskIngredient
		old_amount_of_ingredient = new_amount_of_ingredient - input_item__amount  # New inputs add input item's amount
		if recipe_exists_for_ingredient:
			old_amount_of_ingredient = 0 if adding_first_or_deleting_last_input else new_amount_of_ingredient

	else:  # Input Deleted, which happens pre_delete (so the TaskIngredient still exists)
		old_amount_of_ingredient = task_ingredient__actual_amount  # We've yet to update TaskIngredient
		new_amount_of_ingredient = old_amount_of_ingredient - input_item__amount  # Deleting subtracts input item's amount
		if recipe_exists_for_ingredient:
			new_amount_of_ingredient = 0 if adding_first_or_deleting_last_input else old_amount_of_ingredient

	return old_amount_of_ingredient, new_amount_of_ingredient


# Used on each parent contributing to an ingredient type. Basically a prep-er/wrapper function that retrieves data.
def update_creating_task_and_all_its_children(
				updated_task,
				parent_task,
				creating_task_batch_size,
				previous_total_amount_of_ingredient_for_child,
				new_total_amount_of_ingredient_for_child,
				input_deleted,
				input_added,
				creating_task_of_changed_input=-1):
	updated_task_descendants = get_non_trashed_descendants(parent_task, include_even_if_deleted=updated_task)
	tasks = task_details(updated_task_descendants, include_even_if_deleted=updated_task)
	descendant_ingredients = descendant_ingredient_details(updated_task_descendants, tasks)
	cost = tasks[parent_task]['cost']
	unit_cost = get_unit_cost(cost, creating_task_batch_size)

	update_parent_and_children_recursively(
			unit_cost,
			unit_cost,
			parent_task,
			tasks,
			descendant_ingredients,
			creating_task_batch_size,
			creating_task_batch_size,
			child_with_changed_ingredient_amount=updated_task,
			previous_total_amount_of_ingredient_for_child=previous_total_amount_of_ingredient_for_child,
			new_total_amount_of_ingredient_for_child=new_total_amount_of_ingredient_for_child,
			input_deleted=input_deleted,
			input_added=input_added,
			creating_task_of_changed_input=creating_task_of_changed_input,
	)


# UPDATE INGREDIENT HELPERS

def get_parents_contributing_ingredient(updated_task_id, process_type, product_type):
	parents_in_input_order = Input.objects.filter(
		task=updated_task_id,
		input_item__creating_task__process_type=process_type,
		input_item__creating_task__product_type=product_type
	) \
		.annotate(batch_size=Coalesce(Sum('input_item__creating_task__items__amount'), 0)) \
		.annotate(cost=F('input_item__creating_task__cost')) \
		.order_by('id').values_list('input_item__creating_task__id', 'batch_size', 'cost')

	return make_unique(parents_in_input_order)


def make_unique(my_list):
	new_list = []
	for item in my_list:
		if item not in new_list:
			new_list.append(item)
	return new_list


def update_parents_for_ingredient_and_their_children(updated_task_id, old_amount, new_amount, process_type, product_type, creating_task_of_changed_input=-1, input_added=False, input_deleted=False, child_task_is_being_deleted_entirely=False):
	parents_contributing_ingredient = get_parents_contributing_ingredient(updated_task_id, process_type, product_type)
	for parent_tuple in parents_contributing_ingredient:
		parent_id = parent_tuple[0]
		parent_batch_size = parent_tuple[1]
		parent_cost = parent_tuple[2]
		if parent_cost is None:
			continue
		# Delete every parent as an input to updated_task_id (deleted task)
		if child_task_is_being_deleted_entirely:
			creating_task_of_changed_input = parent_id

		update_creating_task_and_all_its_children(
			updated_task_id,
			parent_id,
			float(parent_batch_size),
			previous_total_amount_of_ingredient_for_child=old_amount,
			new_total_amount_of_ingredient_for_child=new_amount,
			input_deleted=input_deleted,
			input_added=input_added,
			creating_task_of_changed_input=creating_task_of_changed_input,
		)

# DELETE TASK HELPERS

def delete_inputs_and_outputs_and_zero_cost_for_deleted_task(deleted_task_id):
	Input.objects.filter(input_item__creating_task=deleted_task_id).delete()  # delete direct children
	Input.objects.filter(task=deleted_task_id).delete()  # delete direct parents
	Task.objects.filter(pk=deleted_task_id).update(cost=0, remaining_worth=0)  # zero cost


def update_task_ingredient_after_input_delete(**kwargs):
	child_task_id = kwargs['taskID']
	process_type = kwargs['process_type']
	product_type = kwargs['product_type']
	input_item__amount = kwargs['input_item__amount']

	similar_inputs = Input.objects.filter(task=child_task_id,
																				input_item__creating_task__product_type=product_type,
																				input_item__creating_task__process_type=process_type)
	task_ings = TaskIngredient.objects.filter(task=child_task_id,
																						ingredient__product_type=product_type,
																						ingredient__process_type=process_type)
	task_ings_without_recipe = task_ings.filter(ingredient__recipe=None)
	task_ings_with_recipe = task_ings.exclude(ingredient__recipe=None)
	if similar_inputs.count() <= 1:
		# if the input is the only one left for a taskingredient without a recipe, delete the taskingredient
		if task_ings_without_recipe.count() > 0:
			if task_ings_without_recipe[0].ingredient:
				if not task_ings_without_recipe[0].ingredient.recipe:
					task_ings_without_recipe.delete()
		# if the input is the only one left for a taskingredient with a recipe, reset the actual_amount of the taskingredient to 0
		if task_ings_with_recipe.count > 0:
			task_ings_with_recipe.update(actual_amount=0)
	else:
		# if there are other inputs left for a taskingredient without a recipe, decrement the actual_amount by the removed item's amount
		task_ings_without_recipe.update(actual_amount=F('actual_amount') - input_item__amount)
