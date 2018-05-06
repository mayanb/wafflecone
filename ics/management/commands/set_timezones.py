from django.core.management.base import BaseCommand
from ics.models import *


class Command(BaseCommand):
	help = 'Set timezones for teams not based in US/Pacific'

	def set_timezone(self, name, timezone):
		team = Team.objects.get(name=name)
		team.timezone = pytz.timezone(timezone).zone
		team.save()
		self.stdout.write("Updated timezone of " + name + " to " + timezone)

	def handle(self, *args, **options):
		self.set_timezone('soma', 'US/Eastern')
		self.set_timezone('teammindo', 'US/Eastern')
		self.stdout.write(self.style.SUCCESS('Timezones successfully updated'))

