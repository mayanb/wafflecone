from datetime import date, datetime, timedelta
from rest_framework import serializers
from ics.models import *


class TaskSerializer(serializers.ModelSerializer):
	display = serializers.CharField(source='*') # this calls __str__(instance)
	process_type_name = serializers.CharField(source='process_type.name')
	process_type_code = serializers.CharField(source='process_type.code')
	product_type_name = serializers.CharField(source='product_type.name')
	product_type_code = serializers.CharField(source='product_type.code')

	class Meta:
		model = Task
		fields = (
			'id', 
			'process_type', 
			'product_type', 
			'is_trashed', 
			'is_flagged', 
			'is_open', 
			'created_at', 
			'updated_at', 
			'display',
			'custom_display',
			'label_index',
			'label',
			'process_type_name',
			'process_type_code',
			'product_type_name',
			'product_type_code'
		)
