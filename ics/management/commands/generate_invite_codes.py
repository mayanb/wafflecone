from django.core.management.base import BaseCommand, CommandError
from ics.models import *
from uuid import uuid4

class Command(BaseCommand):
    help = 'Generate 20 new invite codes.'

    def handle(self, *args, **options):
        for _ in range(20):
            code = str(uuid4())
            InviteCode.objects.create(invite_code=code)
            self.stdout.write("created invite code " + code)
        self.stdout.write(self.style.SUCCESS('Successfully created 20 new invite codes'))