from django.core.management.base import BaseCommand, CommandError
from ics.models import *
from django.db.models import F
from ics.async_actions import add_new_id_to_descendants_ancestor_lists, add_pipes

class Command(BaseCommand):
	help = 'Set all tasks flagged_ancestors_id_string.'

	def handle(self, *args, **options):
		# Zero everything
		Task.objects.all().update(flagged_ancestors_id_string='')
		# Cascade each flagged task's id to its descendants flagged_ancestors_id_string
		for flagged_task in Task.objects.filter(is_flagged=True):
			print(flagged_task)
			desc = flagged_task.descendants(breakIfCycle=False)
			if desc is not None:
				add_new_id_to_descendants_ancestor_lists(desc, add_pipes(flagged_task.id))
				self.stdout.write(self.style.SUCCESS('Successfully updated %d descendants for a flagged task' % desc.count()))
