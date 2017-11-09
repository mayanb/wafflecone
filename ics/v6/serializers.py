from rest_framework import serializers
from ics.models import *
from django.contrib.auth.models import User
from uuid import uuid4
from django.db.models import F, Sum, Max
from datetime import date, datetime, timedelta

easy_format = '%Y-%m-%d %H:%M'

class AttributeSerializer(serializers.ModelSerializer):
	rank = serializers.IntegerField(read_only=True)

	class Meta:
		model = Attribute
		fields = ('id', 'process_type', 'name', 'rank', 'datatype')

class ProcessTypeSerializer(serializers.ModelSerializer):
	attributes = AttributeSerializer(source='getAllAttributes', read_only=True, many=True)
	created_by_name = serializers.CharField(source='created_by.username', read_only=True)
	team_created_by_name = serializers.CharField(source='team_created_by.name', read_only=True)
	icon = serializers.CharField(read_only=True)
	x = serializers.CharField(read_only=True)
	y = serializers.CharField(read_only=True)
	
	class Meta:
		model = ProcessType
		fields = ('id', 'name', 'code', 'icon', 'attributes', 'unit', 'x', 'y', 'created_by', 'output_desc', 'created_by_name', 'default_amount', 'team_created_by', 'team_created_by_name', 'is_trashed')


class AttributeDetailSerializer(serializers.ModelSerializer):
	class Meta:
		model = Attribute
		fields = ('id', 'process_type', 'name', 'rank', 'datatype', 'is_trashed')
		read_only_fields = ('id', 'process_type', 'name', 'rank', 'datatype')


class ProcessTypePositionSerializer(serializers.ModelSerializer):
	class Meta:
		model = ProcessType
		fields = ('id','x','y')


class ProductTypeSerializer(serializers.ModelSerializer):
	#last_used = serializers.SerializerMethodField(source='get_last_used', read_only=True)

	def get_last_used(self, product):
		if product.last_used is not None:
			return product.last_used.strftime(easy_format)
		else:
			return ""

	class Meta:
		model = ProductType
		fields = ('id', 'name', 'code', 'created_by', 'is_trashed', 'team_created_by')


class ProductTypeBasicSerializer(serializers.ModelSerializer):
	#last_used = serializers.SerializerMethodField(source='get_last_used', read_only=True)
	class Meta:
		model = ProductType
		fields = ('id', 'name', 'code', 'created_by', 'is_trashed', 'team_created_by')

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
		fields = ('id', 'is_open', 'custom_display', 'is_trashed', 'is_flagged', 'display', 'process_type', 'created_at', 'search')

class BasicItemSerializer(serializers.ModelSerializer):
	is_used = serializers.CharField(read_only=True)

	class Meta:
		model = Item
		fields = ('id', 'item_qr', 'creating_task', 'inventory', 'is_used', 'amount', 'is_virtual', 'team_inventory')


# serializes all fields of task
class BasicTaskSerializer(serializers.ModelSerializer):
	display = serializers.CharField(source='*', read_only=True)
	items = BasicItemSerializer(many=True, read_only=True)

	class Meta:
		model = Task
		fields = ('id', 'process_type', 'product_type', 'label', 'is_open', 'is_flagged', 'created_at', 'updated_at', 'label_index', 'custom_display', 'is_trashed', 'display', 'items')

class NestedItemSerializer(serializers.ModelSerializer):
	creating_task = BasicTaskSerializer(many=False, read_only=True)
	#inventory = serializers.CharField(source='getInventory')

	class Meta:
		model = Item
		fields = ('id', 'item_qr', 'creating_task', 'inventory', 'amount', 'is_virtual', 'team_inventory')
		read_only_fields = ('id', 'item_qr', 'creating_task', 'inventory', 'team_inventory')

class BasicInputSerializer(serializers.ModelSerializer):
	input_task_display = serializers.CharField(source='input_item.creating_task', read_only=True)
	input_task = serializers.CharField(source='input_item.creating_task.id', read_only=True)
	input_qr = serializers.CharField(source='input_item.item_qr', read_only=True)
	input_task_n = EditTaskSerializer(source='input_item.creating_task', read_only=True)
	input_item_virtual = serializers.BooleanField(source='input_item.is_virtual', read_only=True)
	input_item_amount = serializers.DecimalField(source='input_item.amount', read_only=True, max_digits=10, decimal_places=3)

	class Meta:
		model = Input
		fields = ('id', 'input_item', 'task', 'input_task', 'input_task_display', 'input_qr', 'input_task_n', 'input_item_virtual', 'input_item_amount')

class NestedInputSerializer(serializers.ModelSerializer):
	input_item = NestedItemSerializer(many=False, read_only=True)

	class Meta:
		model = Input
		fields = ('id', 'input_item', 'task')

class BasicTaskAttributeSerializer(serializers.ModelSerializer):
	att_name = serializers.CharField(source='attribute.name', read_only=True)
	datatype = serializers.CharField(source='attribute.datatype', read_only=True)
	
	class Meta:
		model = TaskAttribute
		fields = ('id', 'attribute', 'task', 'value', 'att_name', 'datatype')

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
			'created_at', 
			'updated_at', 
			'label_index', 
			'custom_display', 
			'items', 
			'inputs', 
			'attribute_values', 
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
	origin = serializers.CharField(source='team_origin.name')
	destination = serializers.CharField(source='team_destination.name')
	team_origin = serializers.CharField(source='team_origin.name')
	team_destination = serializers.CharField(source='team_destination.name')

	class Meta:
		model = Movement
		fields = ('id', 'items', 'origin', 'status', 'destination', 'timestamp', 'notes', 'team_origin', 'team_destination')

class MovementCreateSerializer(serializers.ModelSerializer):
	items = MovementItemSerializer(many=True, read_only=False)
	group_qr = serializers.CharField(default='group_qr_gen')

	class Meta:
		model = Movement
		fields = ('id', 'status', 'destination', 'notes', 'deliverable', 'group_qr', 'origin', 'items', 'team_origin', 'team_destination')

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
		fields = ('id', 'status', 'destination', 'team_destination')

class InventoryListSerializer(serializers.ModelSerializer):
	process_id=serializers.CharField(source='creating_task__process_type', read_only=True)
	process_code=serializers.CharField(source='creating_task__process_type__code', read_only=True)
	process_icon=serializers.CharField(source='creating_task__process_type__icon', read_only=True)
	output_desc=serializers.CharField(source='creating_task__process_type__output_desc', read_only=True)
	count=serializers.CharField(read_only=True)
	unit=serializers.CharField(source='creating_task__process_type__unit', read_only=True)
	team=serializers.CharField(source='creating_task__process_type__team_created_by__name', read_only=True)
	team_id=serializers.CharField(source='creating_task__process_type__team_created_by', read_only=True)
	product_code=serializers.CharField(source='creating_task__product_type__code', read_only=True)
	product_name=serializers.CharField(source='creating_task__product_type__name', read_only=True)
	oldest = serializers.CharField(read_only=True)
	class Meta:
		model = Item
		fields = ('oldest', 'process_id', 'count', 'output_desc', 'unit', 'team', 'team_id', 'product_name', 'product_code', 'process_code', 'process_icon')


class InventoryDetailSerializer(serializers.ModelSerializer):
	items = serializers.SerializerMethodField('getInventoryItems')
	display = serializers.CharField(source='*', read_only=True)

	def getInventoryItems(self, task):
		return BasicItemSerializer(task.items.filter(inputs__isnull=True, team_inventory=task.team), many=True).data

	class Meta:
		model = Task
		fields = ('id', 'items', 'display')

class ActivityListSerializer(serializers.ModelSerializer):
	process_id=serializers.CharField(source='process_type', read_only=True)
	process_name=serializers.CharField(source='process_type__name', read_only=True)
	process_code = serializers.CharField(source='process_type__code', read_only=True)
	process_unit=serializers.CharField(source='process_type__unit', read_only=True)
	product_id=serializers.CharField(source='product_type', read_only=True)
	product_code=serializers.CharField(source='product_type__code', read_only=True)
	runs=serializers.CharField(read_only=True)
	outputs=serializers.CharField(read_only=True)
	flagged=serializers.CharField(read_only=True)

	class Meta:
		model=Task
		fields = ('runs', 'outputs', 'flagged', 'process_id', 'process_name', 'process_unit', 'product_id', 'product_code', 'process_code')

class ActivityListDetailSerializer(serializers.ModelSerializer):
	outputs=serializers.CharField(read_only=True)

	class Meta:
		model=Task
		fields = ('id', 'label', 'label_index', 'custom_display', 'outputs')


class UserDetailSerializer(serializers.ModelSerializer):
	team_name = serializers.CharField(source='userprofile.team.name')
	team = serializers.CharField(source='userprofile.team.id', read_only=True)
	account_type = serializers.CharField(source='userprofile.account_type', read_only=True)
	profile_id = serializers.CharField(source='userprofile.id')
	user_id = serializers.CharField(source='userprofile.user.id')
	has_gauth_token = serializers.SerializerMethodField('hasGauthToken')
	gauth_email = serializers.CharField(source='userprofile.gauth_email')
	username_display = serializers.CharField(source='userprofile.get_username_display')

	def hasGauthToken(self, user):
		return bool(user.userprofile.gauth_access_token)

	class Meta:
		model = User
		fields = ('user_id', 'profile_id', 'username', 'username_display', 'first_name', 'last_name', 'team', 'account_type', 'team_name', 'has_gauth_token', 'gauth_email')

class UserProfileSerializer(serializers.ModelSerializer):
	team_name = serializers.CharField(source='team.name')
	team = serializers.CharField(source='team.id', read_only=True)
	profile_id = serializers.CharField(source='id')
	username = serializers.CharField(source='user.username')
	username_display = serializers.CharField(source='get_username_display')
	first_name = serializers.CharField(source='user.first_name')
	last_name = serializers.CharField(source='user.last_name')

	class Meta:
		model = UserProfile
		fields = ('id', 'profile_id', 'username', 'username_display', 'first_name', 'last_name', 'team', 'account_type', 'team_name', 'gauth_access_token', 'gauth_email')

class UserProfileCreateSerializer(serializers.ModelSerializer):
	username = serializers.CharField(source='user.username')
	password = serializers.CharField(source='user.password')
	first_name = serializers.CharField(source='user.first_name')
	team_name = serializers.CharField(source='team.name', read_only=True)
	profile_id = serializers.CharField(source='id', read_only=True)
	username_display = serializers.CharField(source='get_username_display', read_only=True)

	def create(self, validated_data):
		team = validated_data['team']
		data = validated_data['user']
		long_username = data['username'] + '_' + team.name

		# create the user 
		user = User.objects.create(username=long_username, first_name=data['first_name'])
		user.set_password(data.get('password'))
		user.save()

		# create the userprofile
		account_type = validated_data.get('account_type', '')
		userprofile = UserProfile.objects.create(
			user=user, 
			gauth_access_token="", 
			gauth_refresh_token="", 
			token_type="", 
			team=team,
			account_type=account_type,
		)
		return userprofile

	class Meta:
		model = UserProfile
		extra_kwargs = {'account_type': {'write_only': True}, 'password': {'write_only': True}}
		fields = ('id', 'profile_id', 'username', 'password', 'first_name', 'team', 'account_type', 'team_name', 'gauth_email', 'username_display')


class TeamSerializer(serializers.ModelSerializer):
	processes = serializers.SerializerMethodField('getProcesses')
	products = serializers.SerializerMethodField('getProducts')
	users = UserProfileSerializer(source='userprofiles', many=True, read_only=True)


	def getProcesses(self, team):
		return ProcessTypeSerializer(team.processes.filter(is_trashed=False), many=True).data

	def getProducts(self, team):
		return ProductTypeSerializer(team.products.filter(is_trashed=False), many=True).data


	class Meta:
		model = Team
		fields = ('id', 'name', 'users', 'products', 'processes')



class BasicGoalSerializer(serializers.ModelSerializer):
	actual = serializers.SerializerMethodField(source='get_actual', read_only=True)
	process_name = serializers.CharField(source='process_type.name', read_only=True)
	process_unit = serializers.CharField(source='process_type.unit', read_only=True)
	product_code = serializers.CharField(source='product_type.code', read_only=True)
	userprofile = UserProfileSerializer(many=False, read_only=True)

	def get_actual(self, goal):
		base = date.today()
		start = datetime.combine(base - timedelta(days=base.weekday()), datetime.min.time())
		end = datetime.combine(base + timedelta(days=1), datetime.min.time())

		if goal.timerange == 'w':
			start = datetime.combine(base - timedelta(days=base.weekday()), datetime.min.time())
		elif goal.timerange == 'd':
			start = datetime.combine(base, datetime.min.time())
		elif goal.timerange == 'm':
			start = datetime.combine(base.replace(day=1), datetime.min.time())
		
		return Item.objects.filter(
			creating_task__process_type=goal.process_type, 
			creating_task__product_type=goal.product_type,
			creating_task__is_trashed=False,
			creating_task__created_at__range=(start, end),
			is_virtual=False,
		).aggregate(amount_sum=Sum('amount'))['amount_sum']

	class Meta:
		model = Goal
		fields = ('id', 'process_type', 'product_type', 'goal', 'actual', 'process_name', 'process_unit', 'product_code', 'userprofile', 'timerange')

class GoalCreateSerializer(serializers.ModelSerializer):
	process_name = serializers.CharField(source='process_type.name', read_only=True)
	process_unit = serializers.CharField(source='process_type.unit', read_only=True)
	product_code = serializers.CharField(source='product_type.code', read_only=True)

	def create(self, validated_data):
		userprofile = validated_data.get('userprofile', '')
		goal = Goal.objects.create(
			userprofile=validated_data.get('userprofile', ''),
			process_type=validated_data.get('process_type', ''),
			product_type=validated_data.get('product_type', ''),
			goal=validated_data.get('goal', ''),
			timerange=validated_data.get('timerange', '')
		)
		return goal

	class Meta:
		model = Goal
		fields = ('id', 'process_type', 'product_type', 'goal', 'process_name', 'process_unit', 'product_code', 'userprofile', 'timerange')


class BasicAccountSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)

	class Meta:
		model = Account
		fields = ('id', 'team', 'name', 'created_at',)

class BasicInventoryUnitSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)
	price_updated_at = serializers.DateTimeField(read_only=True)
	process = ProcessTypeSerializer()
	product = ProductTypeSerializer()

	class Meta:
		model = InventoryUnit
		fields = ('id', 'process', 'product', 'unit_price', 'created_at', 'price_updated_at')

class NestedOrderInventoryUnitSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)
	inventory_unit = BasicInventoryUnitSerializer()

	class Meta:
		model = OrderInventoryUnit
		fields = ('id', 'inventory_unit', 'amount', 'created_at')

class NestedOrderSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)
	order_inventory_units = serializers.SerializerMethodField('getOrderInventoryUnits')

	def getOrderInventoryUnits(self, order):
		return NestedOrderInventoryUnitSerializer(order.order_inventory_units.all(), many=True).data

	class Meta:
		model = Order
		fields = ('id', 'status', 'created_at', 'order_inventory_units')

class BasicContactSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)
	account = BasicAccountSerializer()
	orders = serializers.SerializerMethodField('getOrders')

	def getOrders(self, contact):
		return NestedOrderSerializer(contact.orders.all(), many=True).data

	class Meta:
		model = Contact
		fields = ('id', 'account', 'name', 'phone_number', 'email', 'shipping_addr', 'billing_addr', 'created_at', 'orders')

class BasicOrderSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)
	ordered_by = BasicContactSerializer()
	order_inventory_units = serializers.SerializerMethodField('getOrderInventoryUnits')

	def getOrderInventoryUnits(self, order):
		return NestedOrderInventoryUnitSerializer(order.order_inventory_units.all(), many=True).data

	class Meta:
		model = Order
		fields = ('id', 'status', 'ordered_by', 'created_at', 'order_inventory_units')

class EditContactSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)

	class Meta:
		model = Contact
		fields = ('id', 'account', 'name', 'phone_number', 'email', 'shipping_addr', 'billing_addr', 'created_at',)

class AccountDetailSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)
	contacts = BasicContactSerializer(many=True, read_only=True)

	class Meta:
		model = Account
		fields = ('id', 'team', 'name', 'created_at', 'contacts')


class EditOrderSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)

	class Meta:
		model = Order
		fields = ('id', 'status', 'ordered_by', 'created_at',)


class EditInventoryUnitSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)
	price_updated_at = serializers.DateTimeField(read_only=True)

	class Meta:
		model = InventoryUnit
		fields = ('id', 'process', 'product', 'unit_price', 'created_at', 'price_updated_at')


class BasicOrderInventoryUnitSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)
	order = BasicOrderSerializer()
	inventory_unit = BasicInventoryUnitSerializer()

	class Meta:
		model = OrderInventoryUnit
		fields = ('id', 'order', 'inventory_unit', 'amount', 'created_at')

class EditOrderInventoryUnitSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)

	class Meta:
		model = OrderInventoryUnit
		fields = ('id', 'order', 'inventory_unit', 'amount', 'created_at')

class CreateOrderOrderInventoryUnitSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)

	class Meta:
		model = OrderInventoryUnit
		fields = ('id', 'inventory_unit', 'amount', 'created_at')

class CreatePackingOrderSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)
	order_inventory_unit_data = CreateOrderOrderInventoryUnitSerializer(many=True, write_only=True)


	class Meta:
		model = Order
		fields = ('id', 'status', 'ordered_by', 'created_at', 'order_inventory_unit_data')
		extra_kwargs = {'order_inventory_unit_data': {'write_only': True},}

	def create(self, validated_data):
		print(validated_data)
		order_inventory_unit_data = validated_data.pop('order_inventory_unit_data')
		order = Order.objects.create(**validated_data)

		for order_inventory_unit in order_inventory_unit_data:
			OrderInventoryUnit.objects.create(order=order, **order_inventory_unit)
		return order


class BasicOrderItemSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)
	order = BasicOrderSerializer()
	item = BasicItemSerializer()

	class Meta:
		model = OrderItem
		fields = ('id', 'order', 'item', 'created_at', 'amount')

class EditOrderItemSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)

	class Meta:
		model = OrderItem
		fields = ('id', 'order', 'item', 'created_at', 'amount')
