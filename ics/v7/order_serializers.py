from rest_framework import serializers
from ics.models import *
from ics.v7.serializers import *
from django.contrib.auth.models import User
from uuid import uuid4
from django.db.models import F, Sum, Max
from datetime import date, datetime, timedelta

class BasicAccountSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)

	class Meta:
		model = Account
		fields = ('id', 'team', 'name', 'created_at',)

class BasicInventoryUnitSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)
	price_updated_at = serializers.DateTimeField(read_only=True)
	process = ProcessTypeSerializer()
	product = ProductTypeWithUserSerializer()

	class Meta:
		model = InventoryUnit
		fields = ('id', 'process', 'product', 'unit_price', 'created_at', 'price_updated_at')

class NestedOrderInventoryUnitSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)
	inventory_unit = BasicInventoryUnitSerializer()

	class Meta:
		model = OrderInventoryUnit
		fields = ('id', 'inventory_unit', 'amount', 'amount_description', 'created_at')

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

class SuperBasicContactSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)
	account = BasicAccountSerializer()

	class Meta:
		model = Contact
		fields = ('id', 'account', 'name', 'phone_number', 'email', 'shipping_addr', 'billing_addr', 'created_at')


class BasicOrderSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)
	# ordered_by = BasicContactSerializer()
	order_inventory_units = serializers.SerializerMethodField('getOrderInventoryUnits')
	ordered_by_name = serializers.CharField(source='ordered_by.name', read_only=True)
	order_items = serializers.SerializerMethodField('getOrderItems')

	def getOrderInventoryUnits(self, order):
		return NestedOrderInventoryUnitSerializer(order.order_inventory_units.all(), many=True).data

	def getOrderItems(self, order):
		return SuperBasicOrderItemSerializer(order.order_items.all(), many=True).data

	class Meta:
		model = Order
		fields = ('id', 'status', 'ordered_by', 'created_at', 'order_inventory_units', 'order_items', 'ordered_by_name')

class OrderDetailSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)
	ordered_by = SuperBasicContactSerializer()
	order_inventory_units = serializers.SerializerMethodField('getOrderInventoryUnits')
	ordered_by_name = serializers.CharField(source='ordered_by.name', read_only=True)
	order_items = serializers.SerializerMethodField('getOrderItems')

	def getOrderInventoryUnits(self, order):
		return NestedOrderInventoryUnitSerializer(order.order_inventory_units.all(), many=True).data

	def getOrderItems(self, order):
		return SuperBasicOrderItemSerializer(order.order_items.all(), many=True).data

	class Meta:
		model = Order
		fields = ('id', 'status', 'ordered_by', 'created_at', 'order_inventory_units', 'order_items', 'ordered_by_name', 'ordered_by')

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
		fields = ('id', 'order', 'inventory_unit', 'amount', 'amount_description', 'created_at')

class EditOrderInventoryUnitSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)

	class Meta:
		model = OrderInventoryUnit
		fields = ('id', 'order', 'inventory_unit', 'amount', 'amount_description', 'created_at')

class CreateOrderOrderInventoryUnitSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)

	class Meta:
		model = OrderInventoryUnit
		fields = ('id', 'inventory_unit', 'amount', 'amount_description', 'created_at')

class CreatePackingOrderSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)
	order_inventory_unit_data = CreateOrderOrderInventoryUnitSerializer(many=True, write_only=True)
	ordered_by_name = serializers.CharField(source='ordered_by.name', read_only=True)
	order_inventory_units = serializers.SerializerMethodField('getOrderInventoryUnits')

	def getOrderInventoryUnits(self, order):
		return NestedOrderInventoryUnitSerializer(order.order_inventory_units.all(), many=True).data


	class Meta:
		model = Order
		fields = ('id', 'status', 'ordered_by', 'created_at', 'order_inventory_unit_data', 'ordered_by_name', 'order_inventory_units')
		# extra_kwargs = {'order_inventory_unit_data': {'write_only': True},}

	def create(self, validated_data):
		print(validated_data)
		order_inventory_unit_data = validated_data.pop('order_inventory_unit_data')
		order = Order.objects.create(**validated_data)

		for order_inventory_unit in order_inventory_unit_data:
			OrderInventoryUnit.objects.create(order=order, **order_inventory_unit)
		return order

class SuperBasicOrderItemSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)
	item = BasicItemSerializer()

	class Meta:
		model = OrderItem
		fields = ('id', 'order', 'item', 'created_at', 'amount')

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