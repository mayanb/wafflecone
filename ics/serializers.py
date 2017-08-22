from rest_framework import serializers
from ics.models import *
from django.contrib.auth.models import User
from uuid import uuid4
from django.db.models import F, Sum, Max
from datetime import date, datetime, timedelta

class AttributeSerializer(serializers.ModelSerializer):
  class Meta:
    model = Attribute
    fields = ('id', 'process_type', 'name', 'rank')

class ProcessTypeSerializer(serializers.ModelSerializer):
  attributes = AttributeSerializer(source='getAllAttributes', read_only=True, many=True)
  created_by_name = serializers.CharField(source='created_by.username', read_only=True)
  class Meta:
    model = ProcessType
    fields = ('id', 'name', 'code', 'icon', 'attributes', 'unit', 'x', 'y', 'created_by', 'output_desc', 'created_by_name', 'default_amount')

class ProcessTypePositionSerializer(serializers.ModelSerializer):
  class Meta:
    model = ProcessType
    fields = ('id','x','y')


class ProductTypeSerializer(serializers.ModelSerializer):
  class Meta:
    model = ProductType
    fields = ('id', 'name', 'code')

class ProductCodeSerializer(serializers.ModelSerializer):
  class Meta:
    model=ProductType
    fields = ('code',)

class UserSerializer(serializers.ModelSerializer):
  processes = ProcessTypeSerializer(many=True, read_only=True)
  products = ProductTypeSerializer(many=True, read_only=True)
  class Meta:
    model = User
    fields = ('id', 'username', 'processes', 'products')

# serializes only post-editable fields of task
class EditTaskSerializer(serializers.ModelSerializer):
  #id = serializers.IntegerField(read_only=True)
  created_at = serializers.DateTimeField(read_only=True)
  display = serializers.CharField(source='*', read_only=True)
  process_type = serializers.IntegerField(source='process_type.id', read_only=True)
  class Meta:
    model = Task
    fields = ('id', 'is_open', 'custom_display', 'is_trashed', 'is_flagged', 'display', 'process_type', 'created_at')

# serializes all fields of task
class BasicTaskSerializer(serializers.ModelSerializer):
  display = serializers.CharField(source='*', read_only=True)
  class Meta:
    model = Task
    fields = ('id', 'process_type', 'product_type', 'label', 'is_open', 'is_flagged', 'created_at', 'updated_at', 'label_index', 'custom_display', 'is_trashed', 'display')

class BasicItemSerializer(serializers.ModelSerializer):
  is_used = serializers.CharField(read_only=True)

  class Meta:
    model = Item
    fields = ('id', 'item_qr', 'creating_task', 'inventory', 'is_used', 'amount')

class NestedItemSerializer(serializers.ModelSerializer):
  creating_task = BasicTaskSerializer(many=False, read_only=True)
  #inventory = serializers.CharField(source='getInventory')

  class Meta:
    model = Item
    fields = ('id', 'item_qr', 'creating_task', 'inventory', 'amount')

class BasicInputSerializer(serializers.ModelSerializer):
  input_task_display = serializers.CharField(source='input_item.creating_task', read_only=True)
  input_task = serializers.CharField(source='input_item.creating_task.id', read_only=True)
  input_qr = serializers.CharField(source='input_item.item_qr', read_only=True)
  input_task_n = EditTaskSerializer(source='input_item.creating_task', read_only=True)

  class Meta:
    model = Input
    fields = ('id', 'input_item', 'task', 'input_task', 'input_task_display', 'input_qr', 'input_task_n')

class NestedInputSerializer(serializers.ModelSerializer):
  input_item = NestedItemSerializer(many=False, read_only=True)

  class Meta:
    model = Input
    fields = ('id', 'input_item', 'task')

class BasicTaskAttributeSerializer(serializers.ModelSerializer):
  att_name = serializers.CharField(source='attribute.name', read_only=True)
  
  class Meta:
    model = TaskAttribute
    fields = ('id', 'attribute', 'task', 'value', 'att_name')

class NestedTaskAttributeSerializer(serializers.ModelSerializer):
  attribute = AttributeSerializer(many=False, read_only=True)

  class Meta:
    model = TaskAttribute
    fields = ('id', 'attribute', 'task', 'value')

# serializes all fields of the task, with nested items, inputs, and attributes
class NestedTaskSerializer(serializers.ModelSerializer):
  items = BasicItemSerializer(many=True)
  inputs = BasicInputSerializer(many=True, read_only=True)
  input_unit = serializers.CharField(read_only=True)
  #inputUnit = serializers.SerializerMethodField('getInputUnit')
  attribute_values = BasicTaskAttributeSerializer(read_only=True, many=True)
  product_type = ProductTypeSerializer(many=False, read_only=True)
  process_type = ProcessTypeSerializer(many=False, read_only=True)
  display = serializers.CharField(source='*')
  total_amount = serializers.CharField(read_only=True)

  def getInputUnit(self, task):
    input = task.inputs.first()
    if input is not None:
      return input.input_item.creating_task.process_type.unit
    else: 
      return ''

  def getItems(self, task):
    if self.context.get('inventory', None) is not None:
      return BasicItemSerializer(task.items.all().filter(input__isnull=True), many=True).data
    else:
      return BasicItemSerializer(task.items.all().annotate(is_used=F('input__task')), many=True).data

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
      'created_at', 
      'updated_at', 
      'label_index', 
      'custom_display', 
      'items', 
      'inputs', 
      'attribute_values', 
      'display'
    )


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
    fields = ('id', 'item',)
    depth = 1

class MovementListSerializer(serializers.ModelSerializer):
  items = NestedMovementItemSerializer(many=True, read_only=True)
  origin = serializers.CharField(source='origin.username')
  destination = serializers.CharField(source='destination.username')
  class Meta:
    model = Movement
    fields = ('id', 'items', 'origin', 'status', 'destination', 'timestamp', 'notes')

class MovementCreateSerializer(serializers.ModelSerializer):
  items = MovementItemSerializer(many=True, read_only=False)
  group_qr = serializers.CharField(default='group_qr_gen')

  class Meta:
    model = Movement
    fields = ('id', 'status', 'destination', 'notes', 'deliverable', 'group_qr', 'origin', 'items')

  def create(self, validated_data):
    print(validated_data)
    items_data = validated_data.pop('items')
    movement = Movement.objects.create(**validated_data)
    for item in items_data:
      MovementItem.objects.create(movement=movement, **item)
    return movement

def group_qr_gen():
  return "dande.li/g/" + str(uuid4())

class MovementReceiveSerializer(serializers.ModelSerializer):
  class Meta:
    model = Movement
    fields = ('id', 'status', 'destination')

class InventoryListSerializer(serializers.ModelSerializer):
  process_id=serializers.CharField(source='creating_task__process_type', read_only=True)
  output_desc=serializers.CharField(source='creating_task__process_type__output_desc', read_only=True)
  count=serializers.CharField(read_only=True)
  unit=serializers.CharField(source='creating_task__process_type__unit', read_only=True)
  team=serializers.CharField(source='creating_task__process_type__created_by__username', read_only=True)
  team_id=serializers.CharField(source='creating_task__process_type__created_by', read_only=True)
  class Meta:
    model = Item
    fields = ('process_id', 'count', 'output_desc', 'unit', 'team', 'team_id')


class InventoryDetailSerializer(serializers.ModelSerializer):
  items = serializers.SerializerMethodField('getInventoryItems')
  display = serializers.CharField(source='*', read_only=True)

  def getInventoryItems(self, task):
    return BasicItemSerializer(task.items.filter(input__isnull=True, inventory=task.team), many=True).data

  class Meta:
    model = Task
    fields = ('id', 'items', 'display')

class ActivityListSerializer(serializers.ModelSerializer):
  process_id=serializers.CharField(source='process_type', read_only=True)
  process_name=serializers.CharField(source='process_type__name', read_only=True)
  process_unit=serializers.CharField(source='process_type__unit', read_only=True)
  product_id=serializers.CharField(source='product_type', read_only=True)
  product_code=serializers.CharField(source='product_type__code', read_only=True)
  runs=serializers.CharField(read_only=True)
  outputs=serializers.CharField(read_only=True)
  flagged=serializers.CharField(read_only=True)

  class Meta:
    model=Task
    fields = ('runs', 'outputs', 'flagged', 'process_id', 'process_name', 'process_unit', 'product_id', 'product_code')

class ActivityListDetailSerializer(serializers.ModelSerializer):
  outputs=serializers.CharField(read_only=True)

  class Meta:
    model=Task
    fields = ('id', 'label', 'label_index', 'custom_display', 'outputs')


class BasicGoalSerializer(serializers.ModelSerializer):
  actual = serializers.SerializerMethodField(source='get_actual', read_only=True)
  process_name = serializers.CharField(source='process_type.name', read_only=True)
  process_unit = serializers.CharField(source='process_type.unit', read_only=True)
  product_code = serializers.CharField(source='product_type.code', read_only=True)

  def get_actual(self, goal):
    base = date.today()
    start = datetime.combine(base - timedelta(days=base.weekday()), datetime.min.time())
    end = datetime.combine(base + timedelta(days=1), datetime.min.time())

    return Item.objects.filter(
      creating_task__process_type=goal.process_type, 
      creating_task__product_type=goal.product_type,
      creating_task__is_trashed=False,
      creating_task__created_at__range=(start, end)
    ).count()

  class Meta:
    model = Goal
    fields = ('id', 'process_type', 'product_type', 'goal', 'actual', 'process_name', 'process_unit', 'product_code')
