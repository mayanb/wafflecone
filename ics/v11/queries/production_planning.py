from ics.models import *
from django.db.models.functions import Coalesce
from django.db.models import Sum
from ics.constants import BEGINNING_OF_TIME, END_OF_TIME
from django.contrib.postgres.aggregates.general import ArrayAgg

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

# Source: NetworkX v1.9
# Author: Aric Hagberg (hagberg@lanl.gov)
# Link: https://networkx.github.io/documentation/networkx-1.9/reference/generated/networkx.algorithms.shortest_paths.unweighted.single_source_shortest_path.html?highlight=single_source_shortest_path#networkx.algorithms.shortest_paths.unweighted.single_source_shortest_path
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
		rate = 1.0
		path = paths[pathKey]
		for i in range(len(path) - 1):
			parentKey = path[i]
			childKey = path[i+1]
			rate *= conversion_map[parentKey][childKey]['conversion_rate']
		rates[pathKey] = rate
	return rates

def getUniqueAncestors(process, product, categories):
	queryset = Item.objects.none()

	if process is not None and product is not None and categories is not None:
		# take a sample of the 10 most recent tasks with the same process and product types
		sampleTasks = Task.objects.filter(
			is_trashed=False,
			process_type=process,
			product_type=product
		).order_by('-created_at')[:10]

		# extract all unique ancestors of specified category (i.e raw material, work in progress, finished goods)
		ancestorProcesses = []
		ancestorProducts = []
		for sampleTask in sampleTasks:
			# gets all ancestors of a task
			ancestors = sampleTask.ancestors().filter(process_type__category__in=categories)
			for ancestor in ancestors:
				# prevents adding duplicates
				if not (ancestor.process_type in ancestorProcesses and ancestor.product_type in ancestorProducts):
					ancestorProcesses.append(ancestor.process_type)
					ancestorProducts.append(ancestor.product_type)

		queryset = Item.objects.filter(
			creating_task__is_trashed=False,
			creating_task__process_type__in=ancestorProcesses,
			creating_task__product_type__in=ancestorProducts,
		)
	return queryset