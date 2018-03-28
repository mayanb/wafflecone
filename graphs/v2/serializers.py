from rest_framework import serializers
from ics.models import *

class ProductionActualsSerializer(serializers.Serializer):
	bucket = serializers.DateTimeField(read_only=True)
	num_tasks = serializers.IntegerField(read_only=True)
	total_amount = serializers.SerializerMethodField()

	def get_total_amount(self, obj):
		return obj['total_amount'] or 0

class ProductionActualsDOMSerializer(serializers.Serializer):
	bucket = serializers.DateTimeField(read_only=True)
	num_tasks = serializers.IntegerField(read_only=True)
	total_amount = serializers.IntegerField(read_only=True)