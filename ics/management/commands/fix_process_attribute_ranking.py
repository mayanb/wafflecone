from django.core.management.base import BaseCommand, CommandError
from ics.models import *
from django.db.models import F

class Command(BaseCommand):
    help = 'Buggy attribute rank updating seriously garbled rankings. This fixes it by resetting incremental rank ignoring is_trashed tasks, working with a front end change.'

    def handle(self, *args, **options):
        count = 0
        for process in ProcessType.objects.prefetch_related('attribute_set'):
            for index, attribute in enumerate(process.attribute_set.filter(is_trashed=False).order_by('rank')):
                if attribute.rank != index:
                  print(index, attribute.rank, attribute.name)
                  attribute.rank = index
                  attribute.save(update_fields=['rank'])
                  count += 1

        self.stdout.write(self.style.SUCCESS('Successfully fixed rankings %s incorrect (non-trashed) attribute rankings. Yay!' % count))