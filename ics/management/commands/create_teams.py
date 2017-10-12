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

        self.stdout.write(self.style.SUCCESS('Successfully created teams for all users'))