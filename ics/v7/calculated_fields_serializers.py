from rest_framework import serializers
from ics.models import *
from ics.v7.serializers import *
from django.contrib.auth.models import User
from uuid import uuid4
from django.db.models import F, Sum, Max
from datetime import date, datetime, timedelta
import re

class FormulaAttributeSerializer(serializers.ModelSerializer):
	attribute = AttributeSerializer(many=False, read_only=True)
	product_type = ProductTypeSerializer(many=False, read_only=True)
	formula = serializers.CharField(read_only=True)
	comparator = serializers.CharField(read_only=True)

	class Meta:
		model = FormulaAttribute
		fields = ('id', 'attribute', 'product_type', 'formula', 'comparator', 'is_trashed')

class FormulaAttributeDeleteSerializer(serializers.ModelSerializer):
	attribute = AttributeSerializer(many=False, read_only=True)
	product_type = ProductTypeSerializer(many=False, read_only=True)
	formula = serializers.CharField(read_only=True)
	comparator = serializers.CharField(read_only=True)
	is_trashed = serializers.BooleanField(read_only=True)

	def update(self, instance, validated_data):
		instance.is_trashed = True
		instance.save()
		attribute = instance.attribute
		attribute.is_trashed = True
		attribute.save()
		dependencies = FormulaDependency.objects.filter(formula_attribute=instance).update(is_trashed=True)
		return instance

	class Meta:
		model = FormulaAttribute
		fields = ('id', 'attribute', 'product_type', 'formula', 'comparator', 'is_trashed')


class FormulaAttributeCreateSerializer(serializers.ModelSerializer):
	attribute_process_type = serializers.IntegerField(write_only=True)
	attribute_name = serializers.CharField(write_only=True)
	attribute_datatype = serializers.CharField(write_only=True)
	attribute = AttributeSerializer(many=False, read_only=True)


	class Meta:
		model = FormulaAttribute
		fields = ('id', 'attribute', 'is_trashed', 'product_type', 'formula', 'comparator', 'attribute_process_type', 'attribute_name', 'attribute_datatype')
		# write_only_fields = ('creating_task', 'amount', 'process_type', 'creating_product',)
		# read_only_fields = ('creating_task', 'amount', 'process_type', 'creating_product',)
		extra_kwargs = {'attribute_process_type': {'write_only': True}, 'attribute_name': {'write_only': True}, 'attribute_datatype': {'write_only': True}}


	def create(self, validated_data):
		print("hi1")
		print(validated_data)
		product_type = validated_data.get('product_type')
		formula = validated_data.get('formula')
		comparator = validated_data.get('comparator')
		attribute_process_type = validated_data.get('attribute_process_type')
		attribute_name = validated_data.get('attribute_name')
		attribute_datatype = validated_data.get('attribute_datatype')
		attribute_datatype = validated_data.get('attribute_datatype')

		process_type_obj = ProcessType.objects.get(pk=attribute_process_type)
		new_attribute = Attribute.objects.create(process_type=process_type_obj, name=attribute_name, datatype=attribute_datatype)
		new_formula_attribute = FormulaAttribute.objects.create(attribute=new_attribute, product_type=product_type, formula=formula, comparator=comparator)

		# write a regex to get all the dependency attribute id's from the formula string
		# this regex matches numbers of all lengths inside curly braces e.g. {23}
		dependent_attributes = re.findall(r'(?<=\{)\d*(?=\})', formula)

		for attribute in dependent_attributes:
			attribute_obj = Attribute.objects.get(pk=attribute)
			FormulaDependency.objects.create(formula_attribute=new_formula_attribute, dependency=attribute_obj)

		return new_formula_attribute

class FormulaDependencySerializer(serializers.ModelSerializer):
	formula_attribute = FormulaAttributeSerializer(many=False, read_only=True)
	dependency = AttributeSerializer(many=False, read_only=True)
	is_trashed = serializers.BooleanField(read_only=True)

	class Meta:
		model = FormulaDependency
		fields = ('id', 'formula_attribute', 'dependency', 'is_trashed')

class TaskFormulaAttributeSerializer(serializers.ModelSerializer):
	formula_attribute = FormulaAttributeSerializer(many=False, read_only=True)
	task_attribute = BasicTaskAttributeSerializer(many=False, read_only=True)
	predicted_value = serializers.CharField(read_only=True)

	class Meta:
		model = TaskFormulaAttribute
		fields = ('id', 'formula_attribute', 'task_attribute', 'predicted_value')



