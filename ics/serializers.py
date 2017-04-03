from rest_framework import serializers
from ics.models import *
from django.contrib.auth.models import User

class AttributeSerializer(serializers.ModelSerializer):
  class Meta:
    model = Attribute
    fields = ('id', 'process_type', 'name', 'rank')

class ProcessTypeSerializer(serializers.ModelSerializer):
  attributes = AttributeSerializer(source='getAllAttributes', read_only=True, many=True)
  class Meta:
    model = ProcessType
    fields = ('id', 'name', 'code', 'icon', 'attributes', 'unit', 'x', 'y', 'created_by')

class ProcessTypePositionSerializer(serializers.ModelSerializer):
  class Meta:
    model = ProcessType
    fields = ('id','x','y')


class ProductTypeSerializer(serializers.ModelSerializer):
  class Meta:
    model = ProductType
    fields = ('id', 'name', 'code')

class UserSerializer(serializers.ModelSerializer):
  processes = ProcessTypeSerializer(many=True, read_only=True)
  products = ProductTypeSerializer(many=True, read_only=True)
  class Meta:
    model = User
    fields = ('id', 'username', 'processes', 'products')

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
  inventory = serializers.CharField(source='getInventory')

  class Meta:
    model = Item
    fields = ('id', 'item_qr', 'creating_task', 'inventory')

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
  items = BasicItemSerializer(many=True, read_only=True)
  inputs = BasicInputSerializer(many=True, read_only=True)
  inputUnit = serializers.SerializerMethodField('getInputUnit')
  attribute_values = BasicTaskAttributeSerializer(read_only=True, many=True)
  product_type = ProductTypeSerializer(many=False, read_only=True)
  process_type = ProcessTypeSerializer(many=False, read_only=True)

  def getInputUnit(self, task):
    input = task.inputs.first()
    if input is not None:
      return input.task.process_type.unit
    else: 
      return ''

  class Meta:
    model = Task
    fields = ('id', 'process_type', 'product_type', 'label', 'inputUnit', 'is_open', 'is_flagged', 'created_at', 'updated_at', 'label_index', 'custom_display', 'items', 'inputs', 'attribute_values')


class RecommendedInputsSerializer(serializers.ModelSerializer):
  class Meta:
    model = RecommendedInputs
    fields = ('id', 'process_type', 'recommended_input')

class MovementItemSerializer(serializers.ModelSerializer):
  class Meta:
    model = MovementItem
    fields = ('id', 'item')

class NestedMovementItemSerializer(serializers.ModelSerializer):
  class Meta:
    model = MovementItem
    fields = ('id', 'item')
    depth = 1

class MovementListSerializer(serializers.ModelSerializer):
  items = NestedMovementItemSerializer(many=True, read_only=True)
  class Meta:
    model = Movement
    fields = ('id', 'items', 'team', 'status')

class MovementCreateSerializer(serializers.ModelSerializer):
  items = MovementItemSerializer(many=True, read_only=False)

  class Meta:
    model = Movement
    fields = ('id', 'status', 'intended_destination', 'deliverable', 'group_qr', 'team', 'items')

  def create(self, validated_data):
    items_data = validated_data.pop('items')
    movement = Movement.objects.create(**validated_data)
    for item in items_data:
      MovementItem.objects.create(movement=movement, **item)
    return movement