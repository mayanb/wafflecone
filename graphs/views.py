from __future__ import unicode_literals
from rest_framework import status
from rest_framework.response import Response
from django.db import models
from django.db.models import F, Q, Count, Case, When, Min, Value, Subquery, OuterRef, Sum, DecimalField, ExpressionWrapper, FloatField, CharField, Value as V
from django.db.models.functions import Coalesce, Concat
from django.forms.models import model_to_dict
from django.contrib.postgres.aggregates.general import ArrayAgg
from ics.models import *
from django.contrib.auth.models import User
from django.core import serializers
from graphs.serializers import *
from rest_framework import generics
from django.shortcuts import get_object_or_404, render
import django_filters
from rest_framework.filters import OrderingFilter
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from ics.paginations import *
import datetime

from django.shortcuts import render
import json

# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
from rest_framework.decorators import api_view
import requests
import datetime

dateformat = "%Y-%m-%d-%H-%M-%S-%f"



# @csrf_exempt
@api_view(['GET'])
def GetProcessCoocurrence(request):
	team = request.GET.get('team')

		# nodes
	nodes = []
	team_procs = set()
	for proctype in ProcessType.objects.filter(team_created_by=team):
		new_node = {}
		new_node["id"] = proctype.id
		new_node["name"] = proctype.name
		nodes.append(new_node)
		team_procs.add(proctype.id)
	print('done creating nodes')


	case = Case(When(num_inputs=0, then=Value(1)), default=F('num_inputs'), output_field=DecimalField())
	exp = ExpressionWrapper((F('amount')/case), output_field=FloatField())
	annotated_items_list = list(Item.objects.annotate(num_inputs=Count('inputs')).annotate(weight=exp))

	annotated_items = {}
	for item in annotated_items_list:
		annotated_items[item.id] = item.weight
	print('done annotating items')


	annotated_process_list = list(ProcessType.objects.annotate(total_amt=Sum('tasks__items__amount')))
	annotated_process = {}
	for proc in annotated_process_list:
		annotated_process[proc.id] = proc.total_amt
	print('done annotating processes')

	queryset = Task.objects.filter(is_trashed=False, process_type__team_created_by=team)
	queryset = queryset.annotate(op=F('items__inputs__task__process_type__name'), op_id=F('items__inputs__task__process_type__id'), item_id=F('items__id'), ot_id=F('items__inputs__task__id'))
	queryset = queryset.values('process_type__name', 'process_type__id', 'id', 'op', 'op_id', 'ot_id', 'item_id')

	print queryset.count()
	process_type_pair_to_weight = {}
	for obj in queryset:
		p1_name = obj['process_type__name']
		p2_name = obj['op']
		p1_id = obj['process_type__id']
		p2_id = obj['op_id']

		if p2_id in team_procs:
			weight = annotated_items[obj['item_id']]/float(annotated_process[p1_id])
			if not weight:
				weight=1

			tuple_key = (p1_id, p2_id)
			if tuple_key in process_type_pair_to_weight:
				process_type_pair_to_weight[tuple_key] += weight
			else:
				process_type_pair_to_weight[tuple_key] = weight

	print('done creating tuples')

	links = []
	for tuple_key in process_type_pair_to_weight:
		if tuple_key[0] and tuple_key[1]:
			if process_type_pair_to_weight[tuple_key] > 0.09:
				new_link = {}
				new_link["source"] = tuple_key[0]
				new_link["target"] = tuple_key[1]
				new_link["value"] = process_type_pair_to_weight[tuple_key]
				links.append(new_link)
	print('done creating links')


	response = HttpResponse(json.dumps({"nodes": nodes, "links": links}), content_type="text/plain")
	return response;



# @csrf_exempt
@api_view(['GET'])
def GetInputValidation(request):
	team = request.GET.get('team')
	input_item_qr = request.GET.get('input_item_qr')
	input_task_id = request.GET.get('input_task_id')
	print(input_item_qr)
	print(input_task_id)

	if Item.objects.filter(item_qr=input_item_qr).count() == 0:
		body = {}
		body['is_valid_qr'] = False
		body['item'] = None
		body['is_reasonable_input'] = False
		return HttpResponse(json.dumps(body), content_type="applicatiion/json")
  	else:
  		input_item = Item.objects.filter(item_qr=input_item_qr)[0]

	input_task = Task.objects.get(pk=input_task_id)

	inputs = Input.objects.filter(
			task__process_type=input_task.process_type, 
			task__product_type=input_task.product_type
		).annotate(
			prod_proc=Concat(
				'input_item__creating_task__process_type__id', 
				V(' '), 
				'input_item__creating_task__product_type__id', 
				output_field=CharField()
			)
		).values('prod_proc').annotate(count=Count('prod_proc')).order_by('-count')

	input_types = {}
	for inp in inputs:
		input_types[inp['prod_proc']] = inp['count']

	ordered_inputs = sorted(input_types, key=input_types.get, reverse=True)
	if len(ordered_inputs) == 0:
		body = {}
		body['is_valid_qr'] = True
		body['item'] = json.loads(serializers.serialize('json', [input_item,])[1:-1])
		body['is_reasonable_input'] = False
		return HttpResponse(json.dumps(body), content_type="applicatiion/json")
	if len(ordered_inputs) > 1:
		initial_inputs = ordered_inputs[0:len(ordered_inputs)/2]
		input_item_str = str(input_item.creating_task.process_type.id) + ' ' + str(input_item.creating_task.product_type.id)
		if input_item_str in initial_inputs:
			body = {}
			body['is_valid_qr'] = True
			body['item'] = json.loads(serializers.serialize('json', [input_item,])[1:-1])
			body['is_reasonable_input'] = True
			return HttpResponse(json.dumps(body), content_type="applicatiion/json")
		else:
			body = {}
			body['is_valid_qr'] = True
			body['item'] = json.loads(serializers.serialize('json', [input_item,])[1:-1])
			body['is_reasonable_input'] = False
			return HttpResponse(json.dumps(body), content_type="applicatiion/json")

# @csrf_exempt
@api_view(['GET'])
def GetProcessTimes(request):
	team = request.GET.get('team')

		# nodes
	nodes = []
	team_procs = set()
	for proctype in ProcessType.objects.filter(team_created_by=team):
		new_node = {}
		new_node["id"] = proctype.id
		new_node["name"] = proctype.name
		nodes.append(new_node)
		team_procs.add(proctype.id)
	print('done creating nodes')

	times = {}
	tasks = []
	for task in Task.objects.filter(process_type__team_created_by=team):
		start_time = task.created_at
		end_time = start_time
		for output in task.items.all():
			if output.created_at > end_time:
				end_time = output.created_at
		time = end_time - start_time
		times[task.id] = time

	response = HttpResponse(json.dumps({"nodes": nodes, "links": links}), content_type="text/plain")
	return response;


# class GetProcessCoocurrence(generics.ListAPIView):
# 	serializer_class = ProcessCooccurrenceSerializer
# 	#pagination_class = SmallPagination

# 	def get_queryset(self):
# 		team = self.request.query_params.get('team', None)
# 		if team is not None:
# 			return Team.objects.filter(pk=team)
# 		return Team.objects.none()
# 		# # filter according to various parameters
# 		# team = self.request.query_params.get('team', None)
# 		# if team is not None:
# 		# 	queryset = queryset.filter(process_type__team_created_by=team)
# 		# # filter according to date creation, based on parameters
# 		# start = self.request.query_params.get('start', None)
# 		# end = self.request.query_params.get('end', None)
# 		# if start is not None and end is not None:
# 		# 	start = start.strip().split('-')
# 		# 	end = end.strip().split('-')
# 		# 	startDate = datetime.date(int(start[0]), int(start[1]), int(start[2]))
# 		# 	endDate = datetime.date(int(end[0]), int(end[1]), int(end[2]))
# 		# 	queryset = queryset.filter(created_at__date__range=(startDate, endDate))
# 		return queryset
