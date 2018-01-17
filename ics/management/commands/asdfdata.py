from django.core.management.base import BaseCommand, CommandError
from ics.models import *
from uuid import uuid4
from dateutil import rrule
from datetime import datetime, timedelta
from numpy import median, ceil
from django.db.models import Count, CharField, Value as V
from django.db.models.functions import Concat

class Command(BaseCommand):
	help = 'update readable_qr for items'

	# def add_arguments(self, parser):
	#     parser.add_argument('poll_id', nargs='+', type=int)

	def handle(self, *args, **options):
		team=1
		bucket_size = 10*60
		times = {}
		for task in Task.objects.filter(process_type__team_created_by=team):
			start_time = task.created_at
			end_time = start_time
			for output in task.items.all():
				if output.created_at > end_time:
					end_time = output.created_at
			time = end_time - start_time
			times[task.id] = time.total_seconds()

		for proctype in ProcessType.objects.filter(team_created_by=team):
			total_time = 0.0
			num_tasks = 0
			median_times = []
			for task in Task.objects.filter(process_type=proctype):
				num_tasks += 1
				total_time += times[task.id]
				median_times.append(ceil(times[task.id]/bucket_size))
				# median_times.append(times[task.id])
				# print(times[task.id])
			avg_time = total_time/num_tasks
			print proctype.name
			print avg_time
			# med = median(median_times)
			med = median(median_times)
			print med
			print "************"



  #   	for dt in rrule.rule(rrule.WEEKLY, dtstart=datetime(2017, 1, 1, 1, 1, 1), until=datetime.now()):
  #   		for proctype in ProcessType.objects.filter(team_created_by=team, name="Roast"):

  #   		print dt

