from django.core.management.base import BaseCommand, CommandError
from ics.models import *
from django.db.models import F


class Command(BaseCommand):
	help = 'For testing/initiating the Team__last_synced_with_square_at field.'

	def handle(self, *args, **options):
		num_hours = 3

		def three_hours_ago():
			return timezone.now() - timezone.timedelta(hours=num_hours)
		Team.objects.update(last_synced_with_square_at=three_hours_ago())
		self.stdout.write(self.style.SUCCESS('Set last_synced_with_square_at to %d hours ago for all teams.' % num_hours))
