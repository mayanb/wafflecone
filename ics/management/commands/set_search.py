from django.core.management.base import BaseCommand, CommandError
from ics.models import *

class Command(BaseCommand):
    help = 'Updates the search field for all tasks'

    # def add_arguments(self, parser):
    #     parser.add_argument('poll_id', nargs='+', type=int)

    def handle(self, *args, **options):
        for task in Task.objects.with_documents().all():
        	task.search = task.document
        	task.save(update_fields=['search'])
        self.stdout.write("Updated tasks to have search fields")

        self.stdout.write(self.style.SUCCESS('Successfully updated Task search fields'))