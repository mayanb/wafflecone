from ics.models import *
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
	help = 'In order to release the user attributes, change existing ones to text so we dont throw people off'

	def handle(self, *args, **options):
		user_attributes = Attribute.objects.filter(datatype='USER')
		msg = 'Successfully changed all ' + str(user_attributes.count()) + ' Process user attributes to text attributes'
		user_attributes.update(datatype='TEXT')

		self.stdout.write(self.style.SUCCESS(msg))