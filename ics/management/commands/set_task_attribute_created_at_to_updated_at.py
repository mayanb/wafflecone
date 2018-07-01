from django.core.management.base import BaseCommand, CommandError
from ics.models import *

class Command(BaseCommand):
    help = 'We are adding the created_at field to task attributes now that we need it to sort recurring attribute logs. This command seeds them with already existing updated_at.'

    def handle(self, *args, **options):
        all_task_attributes = TaskAttribute.objects.all()
        for task_attribute in all_task_attributes:
            task_attribute.created_at = task_attribute.updated_at
            task_attribute.save(update_fields=['created_at'])
            print(task_attribute.id)
        self.stdout.write("Number of TaskAttributes.created_ats updated = " + str(all_task_attributes.count()))

        self.stdout.write(self.style.SUCCESS('Successfully set created_at fields for TaskAttributes. Yay!'))
