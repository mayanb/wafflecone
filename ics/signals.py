from ics.models import *
from django.db.models.signals import post_save
from django.core.signals import request_finished
from django.dispatch import receiver
from zappa.async import task

@receiver(post_save, sender=ProcessType)
def processtype_changed(sender, instance, **kwargs):
	helper(instance.id)


@receiver(post_save, sender=ProductType)
def producttype_changed(sender, instance, **kwargs):
	for task in instance.task_set.with_documents().distinct():
		task.search = task.document
		task.save(update_fields=['search'])

@receiver(post_save, sender=TaskAttribute)
def taskattribute_changed(sender, instance, **kwargs):
	print(instance.task.id)
	task = Task.objects.with_documents().filter(pk=instance.task.id)[0]
	task.search = task.document
	task.save(update_fields=['search'])

@receiver(request_finished)
def my_callback(sender, **kwargs):
	print("request finished")


@task
def helper(proc):
	print('hello')
	tasks = Task.objects.with_documents().filter(process_type__id=proc)
	for task in tasks.distinct():
		task.search = task.document
		task.save(update_fields=['search'])