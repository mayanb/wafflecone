from django.core.management.base import BaseCommand, CommandError
from ics.models import *
from uuid import uuid4

class Command(BaseCommand):
    help = 'update readable_qr for items'

    # def add_arguments(self, parser):
    #     parser.add_argument('poll_id', nargs='+', type=int)

    def handle(self, *args, **options):
        Item.objects.filter(is_virtual=True).delete()
        	# item.readable_qr = item.item_qr[-6:]
        self.stdout.write("Deleted virtual Items")


   #      for task in Task.objects.all():
			# qr_code = "plmr.io/" + str(uuid4())
			# newVirtualItem = Item(is_virtual=True, creating_task=task, item_qr=qr_code)
			# newVirtualItem.save()

        # self.stdout.write("Added virtual Items")

        self.stdout.write(self.style.SUCCESS('Successfully fixed virtual items'))