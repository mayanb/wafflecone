from ics.models import *
from django.db.models.signals import post_save, post_delete
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

@receiver(post_delete, sender=Task)
def task_deleted(sender, instance, **kwargs):
	kwargs = { 'pk' : instance.id }
	check_flagged_tasks_alerts(**kwargs)
	check_goals_alerts(**kwargs)

# this signal only gets called once whereas all the others get called twice
@receiver(post_delete, sender=Input)
def input_deleted(sender, instance, **kwargs):
	kwargs = { 'pk' : instance.task.id }
	unflag_task_descendants(**kwargs)
	kwargs2 = { 'taskID' : instance.task.id, 'creatingTaskID' : instance.input_item.creating_task.id}
	check_anomalous_inputs_alerts(**kwargs2)

@receiver(post_save, sender=Item)
def item_changed(sender, instance, **kwargs):
	kwargs = { 'pk' : instance.creating_task.id }
	check_goals_alerts(**kwargs)

@receiver(post_save, sender=Input)
def input_changed(sender, instance, **kwargs):
	kwargs = { 'taskID' : instance.task.id, 'creatingTaskID' : instance.input_item.creating_task.id}
	check_anomalous_inputs_alerts(**kwargs)

