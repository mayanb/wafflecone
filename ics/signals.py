from ics.models import *
from django.db.models.signals import pre_save, post_save, pre_delete, post_delete
from django.db.models import Count, F
from django.dispatch import receiver
from ics.async_actions import *
from ics.alerts import *

@receiver(post_save, sender=ProcessType)
def processtype_changed(sender, instance, **kwargs):
	kwargs = { 'process_type__id' : instance.id }
	update_task_search_vector(**kwargs)

@receiver(post_save, sender=ProductType)
def producttype_changed(sender, instance, **kwargs):
	kwargs = { 'product_type__id' : instance.id }
	update_task_search_vector(**kwargs)

@receiver(post_save, sender=TaskAttribute)
def taskattribute_changed(sender, instance, **kwargs):
	kwargs = { 'pk' : instance.task.id }
	update_task_search_vector(**kwargs)


@receiver(post_save, sender=Task)
def task_changed(sender, instance, **kwargs):
	kwargs = { 'pk' : instance.id }
	update_task_descendents_flag_number(**kwargs)

	#Don't create duplicate alerts after updating task search field
	if 'update_fields' not in kwargs or not kwargs['update_fields'] or 'search' not in kwargs['update_fields']:
		check_flagged_tasks_alerts(**kwargs)
	# >>> Handle Deleted Task
	previously_was_trashed = instance.tracker.previous('is_trashed')
	if previously_was_trashed is None:
		return  # This is a newly created task, yet to be saved to the DB. There's no cost to update from it.

	task_was_trashed = instance.is_trashed and not previously_was_trashed
	if task_was_trashed:
		task_deleted_update_cost(instance.id)
		return
	# >>> Handle new cost_set_by_user for Task
	previous_cost = instance.tracker.previous('cost')
	previous_cost_set_by_user = instance.tracker.previous('cost_set_by_user')
	new_cost_set_by_user = instance.cost_set_by_user
	# Verify that A) user actually changed cost and B) change in cost_set_by_user actually deviates from the previous cost
	user_changed_cost = new_cost_set_by_user != previous_cost_set_by_user and new_cost_set_by_user != previous_cost
	if user_changed_cost:
		change_in_remaining_worth = new_cost_set_by_user - previous_cost
		# Task.objects.filter(pk=instance.id).update(remaining_worth=F('remaining_worth') + change_in_remaining_worth)
		task_cost_update(instance.id, previous_cost, new_cost_set_by_user)


@receiver(post_delete, sender=Task)
def task_deleted(sender, instance, **kwargs):
	kwargs = { 'pk' : instance.id }
	check_flagged_tasks_alerts(**kwargs)
	check_goals_alerts(**kwargs)


@receiver(post_save, sender=Item)
def item_changed(sender, instance, **kwargs):
	kwargs2 = { 'pk': instance.creating_task.id }
	check_goals_alerts(**kwargs2)

	# No costs to update if amount hasn't changed.
	previous_amount = instance.tracker.previous('amount')
	if previous_amount == instance.amount:
		return
	# Don't update costs twice on create and save
	if 'created' in kwargs and kwargs['created']:
		return
	kwargs3 = {'pk': instance.creating_task.id, 'new_amount': float(instance.amount), 'previous_amount': float(previous_amount)}
	batch_size_update(**kwargs3)


@receiver(post_save, sender=Input)
def input_changed(sender, instance, created, **kwargs):
	update_task_ingredient_for_new_input(instance)
	kwargs = {'taskID': instance.task.id, 'creatingTaskID': instance.input_item.creating_task.id}
	check_anomalous_inputs_alerts(**kwargs)
	if created:
		kwargs2 = get_input_kwargs(instance, added=True)
		if kwargs2:
			input_update(**kwargs2)


@receiver(pre_delete, sender=Input)
def input_deleted_pre_delete(sender, instance, **kwargs):
	kwargs2 = get_input_kwargs(instance)
	if kwargs2:
		input_update(**kwargs2)
		update_task_ingredient_after_input_delete(instance)


# this signal only gets called once whereas all the others get called twice
@receiver(post_delete, sender=Input)
def input_deleted(sender, instance, **kwargs):
	kwargs = { 'pk' : instance.task.id }
	unflag_task_descendants(**kwargs)
	kwargs2 = { 'taskID' : instance.task.id, 'creatingTaskID' : instance.input_item.creating_task.id}
	check_anomalous_inputs_alerts(**kwargs2)


@receiver(post_save, sender=TaskIngredient)
def ingredient_updated(sender, instance, **kwargs):
	# get the previous value
	previous_amount = instance.tracker.previous('actual_amount') and float(instance.tracker.previous('actual_amount'))
	if instance.was_amount_changed:
		kwargs = {'taskID': instance.task.id, 'process_type': instance.ingredient.process_type.id, 'product_type': instance.ingredient.product_type.id,
				  'actual_amount': float(instance.actual_amount), 'task_ing_id': instance.id, 'previous_amount': previous_amount}
		ingredient_amount_update(**kwargs)


# HELPER FUNCTIONS

# Returns None of if no TaskIngredient exists (eg for old tasks)
def get_input_kwargs(instance, added=False):
	task_ingredient_qs = TaskIngredient.objects.filter(
																			task=instance.task.id,
																			ingredient__process_type_id=instance.input_item.creating_task.process_type_id,
																			ingredient__product_type_id=instance.input_item.creating_task.product_type_id,
																		)
	task_ingredient = task_ingredient_qs.count() > 0 and task_ingredient_qs[0]
	if not task_ingredient:  # Impossible to proceed
		return

	task_ingredient__actual_amount = float(task_ingredient.actual_amount)
	process_type = task_ingredient.ingredient.process_type.id
	product_type = task_ingredient.ingredient.product_type.id
	recipe_exists_for_ingredient = instance.task.recipe and Ingredient.objects.filter(
		recipe=instance.task.recipe,
		process_type=process_type,
		product_type=product_type,
	).count()
	num_similar_inputs = Input.objects.filter(
		task=instance.task,
		input_item__creating_task__product_type=instance.input_item.creating_task.product_type,
		input_item__creating_task__process_type=instance.input_item.creating_task.process_type,
	).count()
	adding_first_or_deleting_last_input = num_similar_inputs == 1  # both cases same since we use pre_delete and post_save

	return {
		'taskID': instance.task.id,
		'creatingTaskID': instance.input_item.creating_task.id,
		'added': added,
		'process_type': process_type,
		'product_type': product_type,
		'task_ingredient__actual_amount': task_ingredient__actual_amount,
		'input_item__creating_task__product_type': instance.input_item.creating_task.product_type_id,
		'input_item__creating_task__process_type': instance.input_item.creating_task.process_type_id,
		'recipe_exists_for_ingredient': recipe_exists_for_ingredient,
		'adding_first_or_deleting_last_input': adding_first_or_deleting_last_input,
	}


def update_task_ingredient_after_input_delete(instance):
	similar_inputs = Input.objects.filter(task=instance.task, \
	                                      input_item__creating_task__product_type=instance.input_item.creating_task.product_type, \
	                                      input_item__creating_task__process_type=instance.input_item.creating_task.process_type)
	task_ings = TaskIngredient.objects.filter(task=instance.task, \
	                                          ingredient__product_type=instance.input_item.creating_task.product_type, \
	                                          ingredient__process_type=instance.input_item.creating_task.process_type)
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
		task_ings_without_recipe.update(actual_amount=F('actual_amount') - instance.input_item.amount)


def update_task_ingredient_for_new_input(new_input):
	input_creating_product = new_input.input_item.creating_task.product_type
	input_creating_process = new_input.input_item.creating_task.process_type
	matching_task_ings = TaskIngredient.objects.filter(task=new_input.task, ingredient__product_type=input_creating_product, ingredient__process_type=input_creating_process)
	if matching_task_ings.count() == 0:
		# if there isn't already a taskIngredient and ingredient for this input's creating task, then make a new one
		ing_query = Ingredient.objects.filter(product_type=input_creating_product, process_type=input_creating_process, recipe=None)
		if(ing_query.count() == 0):
			new_ing = Ingredient.objects.create(recipe=None, product_type=input_creating_product, process_type=input_creating_process, amount=0)
		else:
			new_ing = ing_query[0]
		TaskIngredient.objects.create(ingredient=new_ing, task=new_input.task, actual_amount=new_input.input_item.amount)
	else:
		# when creating an input, if there is already a corresponding task ingredient
		# if the task ingredient has a recipe, set the ingredient's actual_amount to its scaled_amount
		matching_task_ings.exclude(ingredient__recipe=None).update(actual_amount=F('scaled_amount'))
		# if the task ingredient doesn't have a recipe, add the new input's amount to the actual_amount
		matching_task_ings.filter(ingredient__recipe=None).update(actual_amount=F('actual_amount')+new_input.input_item.amount)