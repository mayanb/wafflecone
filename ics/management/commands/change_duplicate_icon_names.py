from django.core.management.base import BaseCommand, CommandError
from ics.models import *

class Command(BaseCommand):
    help = 'One time change: we had a lot of the same icons under different names. This gives each duplicate set a single name.'

    def handle(self, *args, **options):
        default_icon_duplicates = 'DS.png, UBS.png, nibspack.png, group.png, gami.png, sample.png, unfoiledbarsample.png, nibstore.png, samplebarfoil.png,'
        num_changed = 0

        def updateIcon(proc, new_name):
            proc.icon = new_name
            proc.save()
            print(proc.icon)

        for process in ProcessType.objects.all():
            icon_name = process.icon
            if icon_name in default_icon_duplicates:
                updateIcon(process, 'default.png')
                num_changed += 1

            elif icon_name == 'winnow.png':
                updateIcon(process, 'breakandwinnow.png')
                num_changed += 1
            elif icon_name == 'melangerpull.png':
                updateIcon(process, 'rotaryconchepull.png')
                num_changed += 1
            elif icon_name == 'cook.png':
                updateIcon(process, 'roast.png')
                num_changed += 1
            elif icon_name == 'rotaryconche.png':
                updateIcon(process, 'conche.png')
                num_changed += 1
            elif icon_name == 'package.png':
                updateIcon(process, 'box.png')
                num_changed += 1

            print(num_changed)

        self.stdout.write("Number of updated fields = " + str(num_changed))
        self.stdout.write(self.style.SUCCESS('Successfully changed each set of duplicate process icons to a new, single name'))
