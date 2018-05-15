from django.core.management.base import BaseCommand, CommandError
from ics.models import *

class Command(BaseCommand):
    help = 'Prints the list of users for each team'

    def handle(self, *args, **options):

        for team in Team.objects.all():
        	print team.name
        	print list(team.userprofiles.values_list('user__username', flat=True))
        	print "***************************************************"
