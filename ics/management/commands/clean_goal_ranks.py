from django.core.management.base import BaseCommand, CommandError
from ics.models import *

class Command(BaseCommand):
    help = 'Clean attribute ranks for all processes'

    def handle(self, *args, **options):
        users = UserProfile.objects.all()
        for user in users: 
            all_goals = [
                Goal.objects.filter(userprofile=user.id, timerange='d').order_by('rank'),
                Goal.objects.filter(userprofile=user.id, timerange='w').order_by('rank'),
                Goal.objects.filter(userprofile=user.id, timerange='m').order_by('rank'),
            ]

            rank = 0
            for goalset in all_goals:
                rank = 0
                for goal in goalset:
                    goal.rank = rank
                    goal.save()
                    rank += 1
            self.stdout.write("updated goals for user " + user.user.username)
        self.stdout.write(self.style.SUCCESS('Successfully updated all goals'))