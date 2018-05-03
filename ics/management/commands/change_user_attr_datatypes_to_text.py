import csv
from ics.models import *
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
	help = 'In order to release the user attributes, change existing ones to text so we dont throw people off'

	def handle(self):
		user_attributes = Attribute.objects.filter(datatype='USER')
		user_attributes.update(datatype='TEXT')
		msg = 'Successfully changed all ' + str(len(user_attributes)) + ' Process user attributes to text attributes'
		self.stdout.write(self.style.SUCCESS(msg))