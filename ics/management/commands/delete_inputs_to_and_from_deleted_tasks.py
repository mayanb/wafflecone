from django.core.management.base import BaseCommand, CommandError
from ics.models import *
from django.db.models import F

class Command(BaseCommand):
    help = 'Deleted tasks, you no need inputs!'

    def handle(self, *args, **options):
        self.stdout.write('IMPORTANT: You are going to want to comment out the pre_/post_delete Input signals or this will run super slow')
        # delete Inputs to deleted children
        Input.objects.filter(input_item__creating_task__is_trashed=True).delete()

        # delete Inputs from deleted parents
        Input.objects.filter(task__is_trashed=True).delete()

        # zero cost
        Task.objects.filter(is_trashed=True).update(cost=None, remaining_worth=None)

        self.stdout.write(self.style.SUCCESS('Successfully deleted all inputs to/from deleted tasks. Yay!'))
