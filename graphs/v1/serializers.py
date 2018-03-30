# from rest_framework import serializers
# from ics.models import *
# from django.contrib.auth.models import User
# from uuid import uuid4
# from django.db.models import F, Sum, Max, Count
# from datetime import date, datetime, timedelta
# from ics.v5.serializers import ProcessTypeSerializer


# # serializes all fields of task
# class TaskGraphSerializer(serializers.ModelSerializer):
# 	count = serializers.CharField(source='c', read_only=True)
# 	first_process = serializers.CharField(source='process_type__name')
# 	second_process = serializers.CharField(source='op', read_only=True)

# 	class Meta:
# 		model = Task
# 		fields = ('count', 'first_process', 'second_process', )


# class ProcessCooccurrenceSerializer(serializers.ModelSerializer):
# 	links = serializers.SerializerMethodField()
# 	nodes = ProcessTypeSerializer(source='processes', many=True, read_only=True)

# 	def get_links(self, team):

# 		# why is this not working :(
# 		annotated_items = {}
# 		for item in Item.objects.all():
# 			num_inputs = item.inputs.count()
# 			if not num_inputs:
# 				num_inputs = 1
# 			weight = float(item.amount)/num_inputs
# 			annotated_items[item.id] = weight


# 		queryset = Task.objects.filter(is_trashed=False, process_type__team_created_by=team)
# 		queryset = queryset.annotate(op=F('items__inputs__task__process_type__name'), item_id=F('items__id'), ot_id=F('items__inputs__task__id'))
# 		queryset = queryset.values('process_type__name', 'id', 'op', 'ot_id', 'item_id')

# 		process_type_pair_to_weight = {}
# 		for obj in queryset:
# 			p1_name = obj['process_type__name']
# 			p2_name = obj['op']
# 			if obj['item_id'] in annotated_items:
# 				weight = annotated_items[obj['item_id']]
# 			else:
# 				weight = 1
# 			tuple_key = (p1_name, p2_name)
# 			if tuple_key in process_type_pair_to_weight:
# 				process_type_pair_to_weight[tuple_key] += weight
# 			else:
# 				process_type_pair_to_weight[tuple_key] = weight

# 		links = []
# 		for tuple_key in process_type_pair_to_weight:
# 			if tuple_key[0] not None and tuple_key[1] not None:
# 				new_link = {}
# 				new_link["source"] = tuple_key[0]
# 				new_link["target"] = tuple_key[1]
# 				new_link["value"] = process_type_pair_to_weight[tuple_key]
# 				links.append(new_link)

# 		# nodes
# 		nodes = []
# 		for proctype in ProcessType.objects.all():
# 			new_node = {}
# 			new_node["id"] = proctype['name']


# 		return TaskGraphSerializer(queryset, many=True, read_only=True).data



# 	class Meta:
# 		model = Team
# 		fields = ('links', 'nodes')
