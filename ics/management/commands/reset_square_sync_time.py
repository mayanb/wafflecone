from django.core.management.base import BaseCommand, CommandError
from ics.models import *
from django.db.models import F

class Command(BaseCommand):
    help = 'For testing/initiating the Team__last_synced_with_square_at field, since time windows should be ~2 hours since Square throttles to 200 payments per request'

    def handle(self, *args, **options):
        def three_hours_ago():
            return timezone.now() - timezone.timedelta(hours=3)
        Team.objects.update(last_synced_with_square_at=three_hours_ago())
        self.stdout.write(self.style.SUCCESS('Set last_synced_with_square_at to 3 hours ago for all teams.'))
