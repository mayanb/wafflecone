from django.core.management.base import BaseCommand, CommandError
from ics.models import *

class Command(BaseCommand):
    help = 'Clean attribute ranks for all processes'

    def handle(self, *args, **options):
        goals = Goal.objects.all()
        for goal in goals:
            goal_product_type = GoalProductType.objects.create(goal=goal, product_type=goal.product_type)
        self.stdout.write(self.style.SUCCESS('Successfully updated all goals'))