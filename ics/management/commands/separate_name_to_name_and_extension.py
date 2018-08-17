from django.core.management.base import BaseCommand, CommandError
from ics.models import *
import os

class Command(BaseCommand):
	help = 'Separates TaskFile name field to name and extension fields.'

	def handle(self, *args, **options):
		files = TaskFile.objects.all()

		for file in files:
			originalName = file.name
			newName, extension = os.path.splitext(originalName)
			if extension:
				file.name = newName
				file.extension = extension
				file.save()
				self.stdout.write('Separated "{}" into "{}" and "{}"'.format(originalName, newName, extension))

		self.stdout.write(self.style.SUCCESS('Successfully updated name and extension fields'))