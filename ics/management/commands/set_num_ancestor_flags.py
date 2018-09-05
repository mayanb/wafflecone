from django.core.management.base import BaseCommand, CommandError
from ics.models import *
from django.db.models import F

class Command(BaseCommand):
	help = 'Updates the num_flagged_ancestors field for all tasks that have flagged ancestors'

	def handle(self, *args, **options):
		for task in Task.objects.filter(is_flagged=True):
			print(task)
			desc = task.descendants(breakIfCycle=False)
			if desc != None:
				print(desc.count())
				desc.update(num_flagged_ancestors=F('num_flagged_ancestors') + 2)
				self.stdout.write(self.style.SUCCESS('Successfully updated descendants for a task'))