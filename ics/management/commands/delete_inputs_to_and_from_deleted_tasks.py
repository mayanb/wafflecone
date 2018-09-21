from django.core.management.base import BaseCommand, CommandError
from ics.models import *
from django.db.models import F

class Command(BaseCommand):
    help = 'Deleted tasks, you no need inputs!'

    def handle(self, *args, **options):
        self.stdout.write('This command deletes any inputs to/from deleted tasks.\nIt will trigger signals.py to update TaskIngredient, which was previously not updated after a task deletion')

        # delete Inputs from deleted parents
        inputs_from_deleted_parents = Input.objects.filter(input_item__creating_task__is_trashed=True)
        for i in inputs_from_deleted_parents:
            print('from_deleted_parent_input (parent, child)', i.input_item.creating_task.id, i.task.id)
            i.delete()
        self.stdout.write('Deleted %s child inputs...' % str(inputs_from_deleted_parents.count()))

        # delete Inputs to deleted children
        inputs_to_deleted_children = Input.objects.filter(task__is_trashed=True)
        for i in inputs_to_deleted_children:
            print('to_deleted_child_input (parent, child)', i.input_item.creating_task.id, i.task.id)
            i.delete()
        self.stdout.write('Deleted %s parent inputs...' % str(inputs_to_deleted_children.count()))

        # zero cost
        count = Task.objects.filter(is_trashed=True).update(cost=None, remaining_worth=None)
        self.stdout.write('Zero-ed %s deleted tasks cost and remaining_worth...' % str(count))

        self.stdout.write(self.style.SUCCESS('Successfully deleted all inputs to/from deleted tasks. Yay!'))
