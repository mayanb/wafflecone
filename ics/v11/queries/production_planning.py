from ics.models import *
from django.db.models.functions import Coalesce
from django.db.models import Sum
from ics.constants import BEGINNING_OF_TIME, END_OF_TIME
from django.contrib.postgres.aggregates.general import ArrayAgg

"""
For some final task t e.g. Package Tum

Get all its ancestors x
For each ancestor a in x:
	get its direct children c that are in x
	get all the task ingredients with task in c and ingredient prod/proc matching a
	for each task ingredient ti:
		count += 1
		total conversion factor += ti. actual amount / ti.task.batch_size
	store conversion_map[(a.prod, a.proc), (ti.task.prod, ti.task.proc)] = total conversion factor / count
"""
def get_conversion_map(base_process_type, base_product_type):
	conversion_map = {}
	# sample the most recent 5 tasks
	tasks = Task.objects.filter(
		process_type=base_process_type,
		product_type=base_product_type
	).order_by('-created_at')[:5]
	
	print('calculating conversion map for ({}, {})'.format(base_process_type, base_product_type))
	for task in tasks:
		print('sampling task {}'.format(task.id))
		ancestors = task.ancestors() | Task.objects.filter(pk=task.pk)
		for a in ancestors:
			children = ancestors.filter(inputs__input_item__creating_task=a)
			task_ingredients = TaskIngredient.objects.filter(
				task__in=children,
				ingredient__process_type=a.process_type,
				ingredient__product_type=a.product_type,
			)
			for ti in task_ingredients:
				batch_size = ti.task.items.aggregate(amount=Coalesce(Sum('amount'), 0))['amount']
				conversion_rate = batch_size / ti.actual_amount
				childKey = (a.process_type.id, a.product_type.id)
				parentKey = (ti.task.process_type.id, ti.task.product_type.id)
				if parentKey == childKey:
					continue
				if parentKey not in conversion_map:
					conversion_map[parentKey] = {
						childKey: {
							'count': 1,
							'total_conversion_rate': conversion_rate,
							'conversion_rate': conversion_rate,
						}
					}
				elif childKey not in conversion_map[parentKey]:
					conversion_map[parentKey][childKey] = {
						'count': 1,
						'total_conversion_rate': conversion_rate,
						'conversion_rate': conversion_rate,
					}
				else:
					conversion_map[parentKey][childKey]['count'] += 1
					conversion_map[parentKey][childKey]['total_conversion_rate'] += conversion_rate
					count = conversion_map[parentKey][childKey]['count']
					total_conversion_rate = conversion_map[parentKey][childKey]['total_conversion_rate']
					conversion_map[parentKey][childKey]['conversion_rate'] = total_conversion_rate / count

				if childKey not in conversion_map:
					conversion_map[childKey] = {}
	return conversion_map

def get_conversion_rates(conversion_map, source):
	# calculate the shortest paths from source to each node
	level = 0
	nextlevel = { source: 1 }
	paths = { source: [source] }
	while nextlevel:
		thislevel = nextlevel
		nextlevel = {}
		for v in thislevel:
			for w in conversion_map[v]:
				if w not in paths:
					paths[w] = paths[v] + [w]
					nextlevel[w] = 1
		level = level + 1

	# calculate the conversion rates of each path
	rates = {}
	for pathKey in paths:
		rate = 1
		path = paths[pathKey]
		for i in range(len(path) - 1):
			parentKey = path[i]
			childKey = path[i+1]
			rate *= conversion_map[parentKey][childKey]['conversion_rate']
		rates[pathKey] = rate
	return rates