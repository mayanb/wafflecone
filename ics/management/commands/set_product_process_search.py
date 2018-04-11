from django.core.management.base import BaseCommand, CommandError
from ics.models import *

class Command(BaseCommand):
	help = 'Updates the search field for all products and processes'

	def handle(self, *args, **options):
		for product in ProductType.objects.with_documents().all():
			product.search = product.document
			product.save(update_fields=['search'])
			self.stdout.write("Updated products to have search fields")
		for process in ProcessType.objects.with_documents().all():
			process.search = process.document
			process.save(update_fields=['search'])
			self.stdout.write("Updated processes to have search fields")

		self.stdout.write(self.style.SUCCESS('Successfully updated Product Process search fields'))