from django.core.management.base import BaseCommand, CommandError
from ics.models import *
from django.db.models import F

class Command(BaseCommand):
	help = 'Sets the num_flagged_ancestors field to 0 for all tasks that have flagged ancestors'

	def handle(self, *args, **options):
		Task.objects.all().update(num_flagged_ancestors=0)
		self.stdout.write(self.style.SUCCESS('Successfully updated all tasks'))