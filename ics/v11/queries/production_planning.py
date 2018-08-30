from django.contrib.postgres.aggregates.general import ArrayAgg
from django.db.models.functions import Coalesce
from django.db.models import Sum
from django.utils import timezone
from ics.constants import BEGINNING_OF_TIME, END_OF_TIME
from ics.models import *
from ics.v11.queries.inventory import *
from datetime import datetime

def get_conversion_map(base_process_type, base_product_type):
	conversion_map = {}
	# sample the 5 most recent tasks
	tasks = Task.objects.filter(
		process_type=base_process_type,
		product_type=base_product_type
	).order_by('-created_at')[:5]

	# The more tasks you sample, the more robust and accurate your conversion map will be. However, it can take a while
	# to get all the ancestors of a task.
	for task in tasks:
		print('sampling task {}'.format(task.id))
		ancestors = task.ancestors() | Task.objects.filter(pk=task.pk)
		for a in ancestors:
			# get all the children of ancestors who are also ancestors themselves
			children = ancestors.filter(inputs__input_item__creating_task=a)
			# get all the task ingredients of those children
			task_ingredients = TaskIngredient.objects.filter(
				task__in=children,
				ingredient__process_type=a.process_type,
				ingredient__product_type=a.product_type,
			)
			for ti in task_ingredients:
				batch_size = ti.task.items.aggregate(amount=Coalesce(Sum('amount'), 0))['amount']
				if (ti.actual_amount != 0):
					conversion_rate = batch_size / ti.actual_amount
				else:
					conversion_rate = 0
				childKey = (a.process_type.id, a.product_type.id)
				parentKey = (ti.task.process_type.id, ti.task.product_type.id)
				# prevents some loops
				if parentKey == childKey:
					continue

				# adds parentKey to the conversion map
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

				# adds childKey to the conversion map (necessary for calculating rates)
				if childKey not in conversion_map:
					conversion_map[childKey] = {}
	return conversion_map

def get_queryset_info(conversion_map, source):
	if not source in conversion_map:
		return []

	paths = get_shortest_paths(conversion_map, source)
	return build_queryset_info_list(conversion_map, source, paths)

# Source: NetworkX v1.9
# Author: Aric Hagberg (hagberg@lanl.gov)
# Link: https://networkx.github.io/documentation/networkx-1.9/reference/generated/networkx.algorithms.shortest_paths.unweighted.single_source_shortest_path.html?highlight=single_source_shortest_path#networkx.algorithms.shortest_paths.unweighted.single_source_shortest_path
# Description: calculates the shortest paths from source to each node
def get_shortest_paths(conversion_map, source):
	nextlevel = {source: 1}
	paths = {source: [source]}
	while nextlevel:
		thislevel = nextlevel
		nextlevel = {}
		for v in thislevel:
			for w in conversion_map[v]:
				if w not in paths:
					paths[w] = paths[v] + [w]
					nextlevel[w] = 1
	return paths

# builds a list of querset information
def build_queryset_info_list(conversion_map, source, paths):
	queryset_info = []
	for pathKey in paths:
		process_type = pathKey[0]
		product_type = pathKey[1]
		category = ProcessType.objects.get(id=process_type).category
		if source == pathKey or not category in ['rm', 'wip']:
			continue

		path = paths[pathKey]
		conversion_rate = calculate_conversion_rate(conversion_map, path)

		amount_used = calculate_amount_used(process_type, product_type)

		# calculate amount used per second
		secondsElapsed = constants.THIRTY_DAYS.total_seconds()
		amount_used_per_second = float(amount_used) / secondsElapsed

		queryset_info.append({
			'process_type': process_type,
			'product_type': product_type,
			'category': category,
			'adjusted_amount': get_adjusted_item_amount(process_type, product_type),
			'conversion_rate': conversion_rate,
			'active_in_last_month': True if amount_used != 0 else False,
			'amount_used_per_second': amount_used_per_second,
		})
	return queryset_info

# calculates the conversion rate for a single path
def calculate_conversion_rate(conversion_map, path):
	conversion_rate = 1
	for i in range(len(path) - 1):
		parentKey = path[i]
		childKey = path[i + 1]
		conversion_rate *= conversion_map[parentKey][childKey]['conversion_rate']
	return conversion_rate

# calculates the amount used in the last month
def calculate_amount_used(process_type, product_type):
	last_month = timezone.now() - constants.THIRTY_DAYS
	amount_used = TaskIngredient.objects.filter(
		ingredient__process_type=process_type,
		ingredient__product_type=product_type,
		task__created_at__gte=last_month
	).aggregate(amount_used=Coalesce(Sum('actual_amount'), 0))['amount_used']
	return amount_used