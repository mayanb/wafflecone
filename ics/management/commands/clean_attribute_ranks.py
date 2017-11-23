from django.core.management.base import BaseCommand, CommandError
from ics.models import *
from uuid import uuid4

class Command(BaseCommand):
    help = 'Clean attribute ranks for all processes'

    def handle(self, *args, **options):
        processes = ProcessType.objects.all()
        for process in processes: 
            attributes = Attribute.objects.filter(is_trashed=False, process_type=process.id).order_by('rank')
            rank = 0
            for attr in attributes:
                attr.rank = rank
                attr.save()
                rank += 1
            self.stdout.write("updated attributes for process " + process.name)

        self.stdout.write(self.style.SUCCESS('Successfully updated all attributes'))