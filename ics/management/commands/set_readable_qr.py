from django.core.management.base import BaseCommand, CommandError
from ics.models import *

class Command(BaseCommand):
    help = 'update readable_qr for items'

    # def add_arguments(self, parser):
    #     parser.add_argument('poll_id', nargs='+', type=int)

    def handle(self, *args, **options):
        for item in Item.objects.all():
        	# item.readable_qr = item.item_qr[-6:]
            item.save(update_fields=['readable_qr'])
        self.stdout.write("Updated Items to point to teams")

        self.stdout.write(self.style.SUCCESS('Successfully updated Item model with readable_qr'))