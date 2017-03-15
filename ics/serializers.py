from rest_framework import serializers
from ics.models import *

class AttributeSerializer(serializers.ModelSerializer):
  class Meta:
    model = Attribute
    fields = ('id', 'process_type', 'name')

class UserSerializer(serializers.ModelSerializer):
  class Meta:
    model = User
    fields = ('id', 'name')

class ProcessTypeSerializer(serializers.ModelSerializer):
  attributes = AttributeSerializer(source='getAllAttributes', read_only=True, many=True)
  class Meta:
    model = ProcessType
    fields = ('id', 'name', 'code', 'icon', 'attributes', 'unit', 'x', 'y')

class ProcessTypePositionSerializer(serializers.ModelSerializer):
  class Meta:
    model = ProcessType
    fields = ('id','x','y')


class ProductTypeSerializer(serializers.ModelSerializer):
  class Meta:
    model = ProductType
    fields = ('id', 'name', 'code')

# serializes only post-editable fields of task
class EditTaskSerializer(serializers.ModelSerializer):
  class Meta:
    model = Task
    fields = ('label', 'is_open', 'label_index', 'custom_display', 'is_trashed', 'is_flagged')

# serializes all fields of task
class BasicTaskSerializer(serializers.ModelSerializer):
  class Meta:
    model = Task
    fields = ('id', 'process_type', 'product_type', 'label', 'is_open', 'is_flagged', 'created_at', 'updated_at', 'label_index', 'custom_display', 'is_trashed')

class BasicItemSerializer(serializers.ModelSerializer):
  class Meta:
    model = Item
    fields = ('id', 'item_qr', 'creating_task')

class NestedItemSerializer(serializers.ModelSerializer):
  creating_task = BasicTaskSerializer(many=False, read_only=True)

  class Meta:
    model = Item
    fields = ('id', 'item_qr', 'creating_task')

class BasicInputSerializer(serializers.ModelSerializer):
  class Meta:
    model = Input
    fields = ('id', 'input_item', 'task')

class NestedInputSerializer(serializers.ModelSerializer):
  input_item = NestedItemSerializer(many=False, read_only=True)

  class Meta:
    model = Input
    fields = ('id', 'input_item', 'task')

class BasicTaskAttributeSerializer(serializers.ModelSerializer):
  class Meta:
    model = TaskAttribute
    fields = ('id', 'attribute', 'task', 'value')

class NestedTaskAttributeSerializer(serializers.ModelSerializer):
  attribute = AttributeSerializer(many=False, read_only=True)

  class Meta:
    model = TaskAttribute
    fields = ('id', 'attribute', 'task', 'value')

# serializes all fields of the task, with nested items, inputs, and attributes
class NestedTaskSerializer(serializers.ModelSerializer):
  items = serializers.SerializerMethodField('getItems')
  inputs = BasicInputSerializer(source='getInputs', read_only=True, many=True)
  inputUnit = serializers.SerializerMethodField('getInputUnit')
  attributes = AttributeSerializer(source='getAllAttributes', read_only=True, many=True)
  attribute_values = BasicTaskAttributeSerializer(source='getTaskAttributes', read_only=True, many=True)
  product_type = ProductTypeSerializer(many=False, read_only=True)
  process_type = ProcessTypeSerializer(many=False, read_only=True)

  def getInputUnit(self, task):
    input = task.input_set.first()
    if input is not None:
      return input.task.process_type.unit
    else: 
      return ''

  def getItems(self, task):
     if self.context.get('inventory', None) is not None:
      return BasicItemSerializer(task.item_set.all().filter(input__isnull=True), many=True).data
     else:
      return BasicItemSerializer(task.item_set.all(), many=True).data
      

  class Meta:
    model = Task
    fields = ('id', 'process_type', 'product_type', 'label', 'inputUnit', 'is_open', 'is_flagged', 'created_at', 'updated_at', 'label_index', 'custom_display', 'items', 'inputs', 'attributes', 'attribute_values')


class RecommendedInputsSerializer(serializers.ModelSerializer):
  class Meta:
    model = RecommendedInputs
    fields = ('id', 'process_type', 'recommended_input')