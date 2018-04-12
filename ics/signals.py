from ics.models import *
from django.db.models.signals import post_save
from django.dispatch import receiver
from ics.async_actions import *

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