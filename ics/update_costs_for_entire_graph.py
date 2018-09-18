from ics.models import *
from django.contrib.postgres.aggregates.general import ArrayAgg
from django.db.models import F, Sum
from django.db.models.functions import Coalesce


def iterative_bfs(start_id, seen=[]):
	q = [start_id]
	while q:
		v = q.pop(0)
		if not v in seen:
			seen = seen + [v]
			neighbors = get_task_neighbor_ids(v)
			q = q + neighbors
	return seen


def get_task_neighbor_ids(task_id):
	children_and_parents = Task.objects.filter(pk=task_id)\
		.annotate(chidren_list=ArrayAgg('items__inputs__task__id'))\
		.annotate(parent_list=ArrayAgg('inputs__input_item__creating_task__id'))
	if children_and_parents.count() > 0:
		children = children_and_parents[0].chidren_list
		parents = children_and_parents[0].parent_list
		neighbors = children + parents
		return neighbors
	else:
		return []


def edge_list(tasks):
	inputs = Input.objects.filter(task__id__in=tasks, input_item__creating_task__id__in=tasks).order_by('id').values_list(
		'task_id', 'input_item__creating_task__id')

	edge_list = []
	for inp in inputs:
		edge_list.append((inp))
	return edge_list


def convert(z):
	if z == None:
		z = 0.00
	return z


def update_costs_for_entire_graph(task_id):
	amt_per_parent_left = {}

	task_ids_for_entire_graph = iterative_bfs(task_id)
	list_of_edges = edge_list(task_ids_for_entire_graph)

	# set everything that doesn't have a user set cost to 0.00
	q = Task.objects.filter(pk__in=task_ids_for_entire_graph)
	q.filter(cost_set_by_user=None).update(cost_set_by_user=0.00, cost=0.00, remaining_worth=0.00)
	q.filter(cost_set_by_user=0.00).update(cost=0.00, remaining_worth=0.00)
	q.exclude(cost_set_by_user=None).update(cost=F('cost_set_by_user'), remaining_worth=F('cost_set_by_user'))

	for edge in list_of_edges:
		child = edge[0]
		parent = edge[1]
		if child == None or Task.objects.get(pk=child).is_trashed or parent == None or Task.objects.get(
						pk=parent).is_trashed:
			continue
		parent = Task.objects.filter(pk=parent).annotate(batch_size=Sum(Coalesce('items__amount', 0)))[0]
		child = Task.objects.filter(pk=child).annotate(batch_size=Sum(Coalesce('items__amount', 0)))[0]
		if parent.id not in amt_per_parent_left:
			amt_per_parent_left[parent.id] = {}
			amt_per_parent_left[parent.id]['size_remaining'] = float(parent.batch_size)
			amt_per_parent_left[parent.id]['total_batch_size'] = float(parent.batch_size)
			amt_per_parent_left[parent.id]['cost'] = float(convert(parent.cost))
			amt_per_parent_left[parent.id]['remaining_worth'] = float(convert(parent.remaining_worth))
		if child.id not in amt_per_parent_left:
			amt_per_parent_left[child.id] = {}
			amt_per_parent_left[child.id]['size_remaining'] = float(child.batch_size)
			amt_per_parent_left[child.id]['total_batch_size'] = float(child.batch_size)
			amt_per_parent_left[child.id]['cost'] = float(convert(child.cost))
			amt_per_parent_left[child.id]['remaining_worth'] = float(convert(child.remaining_worth))

		ti = TaskIngredient.objects.filter(task=child, ingredient__product_type=parent.product_type,
		                                   ingredient__process_type=parent.process_type).first()
		matching_parents = list(
			Input.objects.filter(task=child, input_item__creating_task__process_type=ti.ingredient.process_type,
			                     input_item__creating_task__product_type=ti.ingredient.product_type).values_list(
				'input_item__creating_task__id', flat=True))
		amt_to_give = float(ti.actual_amount) / len(set(matching_parents))
		amt_actually_given = min(amt_to_give, amt_per_parent_left[parent.id]['size_remaining'])
		amt_per_parent_left[parent.id]['size_remaining'] -= amt_actually_given
		if parent.cost and parent.cost > 0.000:
			added_cost = (amt_actually_given / amt_per_parent_left[parent.id]['total_batch_size']) * \
			             amt_per_parent_left[parent.id]['cost']
			amt_per_parent_left[child.id]['cost'] += added_cost
			amt_per_parent_left[child.id]['remaining_worth'] += added_cost
			Task.objects.filter(pk=child.id).update(cost=amt_per_parent_left[child.id]['cost'],
			                                        remaining_worth=amt_per_parent_left[child.id]['remaining_worth'])
			amt_per_parent_left[parent.id]['remaining_worth'] -= added_cost
			Task.objects.filter(pk=parent.id).update(remaining_worth=amt_per_parent_left[parent.id]['remaining_worth'])
