from django.core.management.base import BaseCommand, CommandError
from ics.models import *

class Command(BaseCommand):
    help = 'Creates teams for users/userprofiles and associates the teams with other objects'

    # def add_arguments(self, parser):
    #     parser.add_argument('poll_id', nargs='+', type=int)

    def handle(self, *args, **options):

        for user in User.objects.all():
            team = Team.objects.create(name=user.username)
            UserProfile.objects.create(user=user, team=team)
            self.stdout.write("Created team %s with id %d" % (team.name, team.id))

        for proc in ProcessType.objects.all():
            username = proc.created_by.username
            assoc_team = Team.objects.filter(name=username)[0]
            proc.team_created_by = assoc_team
            proc.save(update_fields=['team_created_by'])
        self.stdout.write("Updated ProcessTypes to point to teams")

        for prod in ProductType.objects.all():
            username = prod.created_by.username
            assoc_team = Team.objects.filter(name=username)[0]
            prod.team_created_by = assoc_team
            prod.save(update_fields=['team_created_by'])
        self.stdout.write("Updated ProductTypes to point to teams")


        for mov in Movement.objects.all():
            origin_username = mov.origin.username
            assoc_team_origin = Team.objects.filter(name=origin_username)[0]
            mov.team_origin = assoc_team_origin
            destination = mov.destination
            if destination is not None:
                destination_username = mov.destination.username
                assoc_team_destination = Team.objects.filter(name=destination_username)[0]
                mov.team_destination = assoc_team_destination
                mov.save(update_fields=['team_origin', 'team_destination'])
            else:
                mov.save(update_fields=['team_origin'])
        self.stdout.write("Updated Movements to point to teams")

        for item in Item.objects.all():
            inventory = item.inventory
            if inventory is not None:
                username = item.inventory.username
                assoc_team = Team.objects.filter(name=username)[0]
                item.team_inventory = assoc_team
                item.save(update_fields=['team_inventory'])
        self.stdout.write("Updated Items to point to teams")

        self.stdout.write(self.style.SUCCESS('Successfully updated models to point to teams'))