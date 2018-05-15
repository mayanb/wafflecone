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
	update_task_descendents_flag_number(pk=instance.id)

	#Don't create duplicate alerts after updating task search field
	if 'update_fields' not in kwargs or not kwargs['update_fields'] or 'search' not in kwargs['update_fields']:
		check_flagged_tasks_alerts(instance)
		check_goals_alerts(instance)
		check_anomolous_inputs_alerts(instance)

# this signal only gets called once whereas all the others get called twice
@receiver(post_delete, sender=Input)
def input_deleted(sender, instance, **kwargs):
	kwargs = { 'pk' : instance.task.id }
	unflag_task_descendants(**kwargs)

@receiver(post_save, sender=Item)
def item_changed(sender, instance, **kwargs):
	check_goals_alerts(instance.creating_task)

@receiver(post_save, sender=Input)
def input_changed(sender, instance, **kwargs):
	check_anomolous_inputs_alerts(instance.task)

