from rest_framework import serializers
from ics.models import *
from ics.v7.serializers import *
from django.contrib.auth.models import User
from uuid import uuid4
from django.db.models import F, Sum, Max
from datetime import date, datetime, timedelta
import re
import string


class FormulaAttributeSerializer(serializers.ModelSerializer):
	attribute = AttributeSerializer(many=False, read_only=True)
	product_type = ProductTypeWithUserSerializer(many=False, read_only=True)
	formula = serializers.CharField(read_only=True)
	comparator = serializers.CharField(read_only=True)

	class Meta:
		model = FormulaAttribute
		fields = ('id', 'attribute', 'product_type', 'formula', 'comparator', 'is_trashed')

class FormulaAttributeDeleteSerializer(serializers.ModelSerializer):
	attribute = AttributeSerializer(many=False, read_only=True)
	product_type = ProductTypeWithUserSerializer(many=False, read_only=True)
	formula = serializers.CharField(read_only=True)
	comparator = serializers.CharField(read_only=True)
	is_trashed = serializers.BooleanField(read_only=True)

	def update(self, instance, validated_data):
		instance.is_trashed = True
		instance.save()
		dependencies = FormulaDependency.objects.filter(formula_attribute=instance).update(is_trashed=True)
		return instance

	class Meta:
		model = FormulaAttribute
		fields = ('id', 'attribute', 'product_type', 'formula', 'comparator', 'is_trashed')


class FormulaAttributeCreateSerializer(serializers.ModelSerializer):
	attribute_obj = AttributeSerializer(source='attribute', read_only=True)
	class Meta:
		model = FormulaAttribute
		fields = ('id', 'attribute', 'attribute_obj', 'is_trashed', 'product_type', 'formula', 'comparator')


	def create(self, validated_data):
		print("hi1")
		print(validated_data)
		product_type = validated_data.get('product_type')
		attribute = validated_data.get('attribute')
		formula = validated_data.get('formula')
		comparator = validated_data.get('comparator')

		new_formula_attribute = FormulaAttribute.objects.create(attribute=attribute, product_type=product_type, formula=formula, comparator=comparator)

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
	task = BasicTaskSerializer(many=False, read_only=True)
	predicted_value = serializers.CharField(read_only=True)

	class Meta:
		model = TaskFormulaAttribute
		fields = ('id', 'formula_attribute', 'task', 'predicted_value')





# serializes all fields of the task, with nested items, inputs, and attributes
class NestedTaskSerializer(serializers.ModelSerializer):
	items = BasicItemSerializer(many=True)
	inputs = BasicInputSerializer(many=True, read_only=True)
	input_unit = serializers.CharField(read_only=True)
	#inputUnit = serializers.SerializerMethodField('getInputUnit')
	attribute_values = BasicTaskAttributeSerializer(read_only=True, many=True)
	predicted_attribute_values = TaskFormulaAttributeSerializer(source='getAllPredictedAttributes', read_only=True, many=True)

	product_type = ProductTypeWithUserSerializer(many=False, read_only=True)
	process_type = ProcessTypeWithUserSerializer(many=False, read_only=True)
	display = serializers.CharField(source='*')
	total_amount = serializers.CharField(read_only=True)

	def getInputUnit(self, task):
		input = task.inputs.first()
		if input is not None:
			return input.input_item.creating_task.process_type.unit
		else: 
			return ''

	def getItems(self, task):
		if self.context.get('team_inventory', None) is not None:
			return BasicItemSerializer(task.items.all().filter(inputs__isnull=True), many=True).data
		else:
			return BasicItemSerializer(task.items.all().annotate(is_used=F('inputs__task')), many=True).data

	class Meta:
		model = Task
		fields = (
			'id', 
			'total_amount', 
			'process_type', 
			'product_type', 
			'label', 
			'input_unit', 
			'is_open', 
			'is_flagged', 
			'flag_update_time', 
			'created_at', 
			'updated_at', 
			'label_index', 
			'custom_display', 
			'items', 
			'inputs', 
			'attribute_values',
			'predicted_attribute_values',  
			'display',
			'is_trashed',
			'search',
		)


class FlowTaskSerializer(serializers.ModelSerializer):
	creating_task = serializers.IntegerField(write_only=True)
	amount = serializers.DecimalField(max_digits=10, decimal_places=3, write_only=True)
	new_process_type = serializers.IntegerField(write_only=True)
	creating_product = serializers.IntegerField(write_only=True)
	new_task = NestedTaskSerializer(source='*', read_only=True)
	new_label = serializers.CharField(write_only=True)

	class Meta:
		model = Task
		fields = ('new_task', 'creating_task', 'amount', 'new_process_type', 'creating_product', 'new_label')
		# write_only_fields = ('creating_task', 'amount', 'process_type', 'creating_product',)
		# read_only_fields = ('creating_task', 'amount', 'process_type', 'creating_product',)
		extra_kwargs = {'creating_task': {'write_only': True}, 'amount': {'write_only': True}, 'new_process_type': {'write_only': True}, 'creating_product': {'write_only': True}, 'new_label': {'write_only': True}}


	def create(self, validated_data):
		print("hi1")
		print(validated_data)
		print("hi2")
		creating_task = validated_data.get('creating_task')
		amount = validated_data.get('amount')
		new_process_type = validated_data.get('new_process_type')
		creating_product = validated_data.get('creating_product')
		new_label = validated_data.get('new_label')

		qr_code = "plmr.io/" + str(uuid4())
		virtual_item = Item.objects.create(is_virtual=True, creating_task_id=creating_task, item_qr=qr_code, amount=amount)
		new_task = Task.objects.create(process_type_id=new_process_type, product_type_id=creating_product, label=new_label)
		Input.objects.create(input_item=virtual_item, task=new_task)
		return new_task


class CreateTaskAttributeSerializer(serializers.ModelSerializer):
	att_name = serializers.CharField(source='attribute.name', read_only=True)
	datatype = serializers.CharField(source='attribute.datatype', read_only=True)
	task_predicted_values = TaskFormulaAttributeSerializer(source='getTaskPredictedAttributes', read_only=True, many=True)


	def getTaskPredictedAttributes(self, task_attribute):
		return TaskFormulaAttribute.objects.filter(task=task_attribute.task)

	class Meta:
		model = TaskAttribute
		fields = ('id', 'attribute', 'task', 'value', 'att_name', 'datatype', 'task_predicted_values')

	def create(self, validated_data):
		print(validated_data)
		attribute = validated_data.get('attribute')
		task = validated_data.get('task')
		value = validated_data.get('value')

		# create the TaskAttribute object and set its value
		attribute_obj = attribute
		task_obj = task
		new_task_attribute = TaskAttribute.objects.create(attribute=attribute_obj, task=task_obj, value=value)

		dependent_attrs = FormulaDependency.objects.filter(dependency=attribute, is_trashed=False)
		print(dependent_attrs)
		for dependent_attr in dependent_attrs:
			print("updating/creating a taskformulaatribute")
			formula_attr = dependent_attr.formula_attribute
			predicted = calculateFormula(formula_attr.formula, task_obj)
			if(predicted != None):
				TaskFormulaAttribute.objects.update_or_create(formula_attribute=formula_attr, task=task_obj, defaults={'predicted_value': predicted})
			else:
				TaskFormulaAttribute.objects.update_or_create(formula_attribute=formula_attr, task=task_obj, defaults={'predicted_value': ""})
		return new_task_attribute


def calculateFormula(formula, task_obj):
	filled_in_formula = formula
	dependent_attributes = re.findall(r'(?<=\{)\d*(?=\})', formula)
	dependent_attr_map = {}
	attribute_objects = Attribute.objects.filter(id__in=dependent_attributes)

	for attribute in attribute_objects:
		if(TaskAttribute.objects.filter(attribute=attribute, task=task_obj).count() > 0):
			dependent_task_attribute = TaskAttribute.objects.filter(attribute=attribute, task=task_obj).latest('updated_at')
			dependent_attr_map[attribute.id] = dependent_task_attribute.value

	if all(value != None for value in dependent_attr_map.values()):
		# fill in the formula with all the values
		for attr_id in dependent_attr_map:
			attr_id_str = "{" + str(attr_id) + "}"
			print(attr_id_str)
			print(dependent_attr_map[attr_id])
			filled_in_formula = string.replace(filled_in_formula, attr_id_str, dependent_attr_map[attr_id])
		print("*************************************")
		print(filled_in_formula)
		if(('{' in filled_in_formula) or ('}' in filled_in_formula)):
			return None
		new_predicted_value = eval(filled_in_formula)
		return new_predicted_value
	else:
		return None




# def updateDependencies(root_formula_attribute, task):
# 	dependents = list(FormulaDependency.objects.filter(dependency=root_formula_attribute.attribute, is_trashed=False).values('formula_attribute'))
# 	dependents_ids = map(lambda d: d['formula_attribute'], dependendents)
# 	formula_attribute_dependents = FormulaAttribute.objects.filter(id__in=dependent_ids, is_trashed=False)

# 	# FormulaAttribute.objects.filter(ancestors__dependency=root_formula_attribute.attribute, is_trashed=False, ancestors__is_trashed=False)

# 	for formula_attribute_dependent in formula_attribute_dependents:
# 		predicted_value = calculateFormula(formula_attribute_dependent.formula, task)
# 		# set the predicted value for the root's taskformulaattribute
# 		task_attribute = TaskAttribute.objects.filter(task=task, attribute=formula_attribute_dependent.attribute)
# 		root_task_formula_attribute = TaskFormulaAttribute.objects.filter(task_attribute=task_attribute, formula_attribute=formula_attribute_dependent).update(predicted_value=predicted_value)
# 	return






