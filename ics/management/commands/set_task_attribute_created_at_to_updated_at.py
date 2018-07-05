from django.core.management.base import BaseCommand, CommandError
from ics.models import *
from django.db.models import F

class Command(BaseCommand):
    help = 'We are adding the created_at field to task attributes now that we need it to sort recurring attribute logs. This command seeds them with already existing updated_at.'

    def handle(self, *args, **options):
        all_task_attributes = TaskAttribute.objects
        all_task_attributes.update(created_at=F('updated_at'))

        self.stdout.write("Number of TaskAttributes.created_ats updated = " + str(all_task_attributes.count()))
        self.stdout.write(self.style.SUCCESS('Successfully set created_at fields for TaskAttributes. Yay!'))
