from ics.models import *
from django.db.models.signals import post_save
from django.core.signals import request_finished
from django.dispatch import receiver

@receiver(post_save, sender=ProcessType)
def processtype_changed(sender, instance, **kwargs):
	helper(sender, instance, **kwargs)


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


def helper(sender, instance, **kwargs):
	for task in instance.tasks.with_documents().distinct():
		task.search = task.document
		task.save(update_fields=['search'])