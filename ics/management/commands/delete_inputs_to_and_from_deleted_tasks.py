from django.core.management.base import BaseCommand, CommandError
from ics.models import *
from django.db.models import F

class Command(BaseCommand):
    help = 'Deleted tasks, you no need inputs!'

    def handle(self, *args, **options):
        self.stdout.write('This command deletes any inputs to/from deleted tasks.\nIt will trigger signals.py to update TaskIngredient, which was previously not updated after a task deletion')

        # delete Inputs to deleted children
        count, o = Input.objects.filter(input_item__creating_task__is_trashed=True).delete()
        self.stdout.write('Deleted %s child inputs...' % str(count))

        # delete Inputs from deleted parents
        count, o = Input.objects.filter(task__is_trashed=True).delete()
        self.stdout.write('Deleted %s parent inputs...' % str(count))

        # zero cost
        count = Task.objects.filter(is_trashed=True).update(cost=None, remaining_worth=None)
        self.stdout.write('Zero-ed %s deleted tasks cost and remaining_worth...' % str(count))

        self.stdout.write(self.style.SUCCESS('Successfully deleted all inputs to/from deleted tasks. Yay!'))
