from django.core.management.base import BaseCommand, CommandError
from ics.models import *

class Command(BaseCommand):
    help = 'Creates teams for users/userprofiles and associates the teams with other objects'

    # def add_arguments(self, parser):
    #     parser.add_argument('poll_id', nargs='+', type=int)

    def handle(self, *args, **options):
        for item in Item.objects.exclude(inventory=None).filter(team_inventory=None):
            inventory = item.inventory
            username = item.inventory.username
            assoc_team = Team.objects.filter(name=username)[0]
            item.team_inventory = assoc_team
            item.save(update_fields=['team_inventory'])
        self.stdout.write("Updated Items to point to teams")

        self.stdout.write(self.style.SUCCESS('Successfully updated Item model to point to teams'))