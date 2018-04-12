from ics.models import *
from zappa.async import task
from django.db.models import F

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
		if(task.was_flag_changed):
			if(task.is_flagged):
				task.descendants().update(num_flagged_ancestors=F('num_flagged_ancestors')+1)
			else:
				task.descendants().update(num_flagged_ancestors=F('num_flagged_ancestors')-1)


