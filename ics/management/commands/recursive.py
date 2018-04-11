from django.core.management.base import BaseCommand, CommandError
from ics.models import *
from uuid import uuid4


class Command(BaseCommand):
	help = 'test recursiion.'

	def handle(self, *args, **options):
		curr = Task.objects.get(pk=11777)
		descendants = Task.objects.filter(id__in=curr.ancestors_raw_query())
		for desc in descendants:
			self.stdout.write(str(desc))