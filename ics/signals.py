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
	if previous_cost == None:
		previous_cost = 0.000
	previous_cost_set_by_user = instance.tracker.previous('cost_set_by_user')
	new_cost_set_by_user = instance.cost_set_by_user
	# Verify that A) user actually changed cost and B) change in cost_set_by_user actually deviates from the previous cost
	user_changed_cost = new_cost_set_by_user != previous_cost_set_by_user and new_cost_set_by_user != previous_cost
	if user_changed_cost:
		task_cost_update(instance.id)


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
	new_amount = instance.amount
	if previous_amount == new_amount:
		return
	# Don't update costs twice on create and save
	if 'created' in kwargs and kwargs['created']:
		return
	batch_size_update(instance.creating_task.id)


@receiver(post_save, sender=Input)
def input_changed(sender, instance, created, **kwargs):
	update_task_ingredient_for_new_input(instance)
	kwargs = {'taskID': instance.task.id, 'creatingTaskID': instance.input_item.creating_task.id}
	check_anomalous_inputs_alerts(**kwargs)
	if created and input_has_task_ingredient(instance):
		input_update(instance.task.id)


# this signal only gets called once whereas all the others get called twice
@receiver(post_delete, sender=Input)
def input_deleted(sender, instance, **kwargs):
	kwargs = { 'pk' : instance.task.id }
	unflag_task_descendants(**kwargs)
	kwargs2 = { 'taskID' : instance.task.id, 'creatingTaskID' : instance.input_item.creating_task.id}
	check_anomalous_inputs_alerts(**kwargs2)

	if input_has_task_ingredient(instance):  # old Inputs may not
		# Don't update cost when a we're deleting all a task's inputs/outputs along with itself. We've already done that.
		if source_and_target_of_input_are_not_trashed(instance):
			input_update(instance.task.id)


@receiver(post_save, sender=TaskIngredient)
def ingredient_updated(sender, instance, **kwargs):
	if instance.was_amount_changed:
		ingredient_amount_update(instance.task.id, instance.id)


# HELPER FUNCTIONS

# Returns False if no TaskIngredient exists (eg for old tasks)
def input_has_task_ingredient(instance):
	task_ingredient_qs = TaskIngredient.objects.filter(
		task=instance.task.id,
		ingredient__process_type_id=instance.input_item.creating_task.process_type_id,
		ingredient__product_type_id=instance.input_item.creating_task.product_type_id,
	)
	return task_ingredient_qs.count() > 0


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


def source_and_target_of_input_are_not_trashed(instance):
	source_is_trashed = instance.input_item.creating_task.is_trashed
	target_is_trashed = instance.task.is_trashed
	return not (target_is_trashed or source_is_trashed)