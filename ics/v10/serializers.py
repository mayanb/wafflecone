from rest_framework import serializers
from ics.models import *
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from smtplib import SMTPException
from uuid import uuid4
from django.db.models import F, Q, Sum, Max, When, Case, Count
from django.db.models.functions import Coalesce
from datetime import date, datetime, timedelta
from django.core.mail import send_mail
from ics.utilities import *
import operator
import pytz
import re
from ics.v10.queries.inventory import inventory_amounts, old_inventory_created_amount, old_inventory_used_amount
from django.contrib.postgres.aggregates.general import ArrayAgg


class InviteCodeSerializer(serializers.ModelSerializer):
	invite_code = serializers.CharField(read_only=True)
	is_used = serializers.BooleanField(read_only=True)

	# def update(self, instance, validated_data):	
	# 	code = validated_data.get('code')
	# 	invitecode = InviteCode.objects.get(invite_code=code)
	# 	invitecode.is_used = True
	# 	invitecode.save()
	# 	return invitecode

	class Meta:
		model = InviteCode
		fields = ('id', 'invite_code', 'is_used')


class AttributeSerializer(serializers.ModelSerializer):
	rank = serializers.IntegerField(read_only=True)
	process_name = serializers.CharField(source='process_type.name', read_only=True)

	class Meta:
		model = Attribute
		fields = ('id', 'process_type', 'process_name', 'name', 'rank', 'datatype')


class ProcessTypeWithUserSerializer(serializers.ModelSerializer):
	attributes = serializers.SerializerMethodField()
	created_by_name = serializers.CharField(source='created_by.username', read_only=True)
	username = serializers.SerializerMethodField(source='get_username', read_only=True)
	last_used = serializers.DateTimeField(source='get_last_used_date', read_only=True)
	team_created_by_name = serializers.CharField(source='team_created_by.name', read_only=True)
	created_at = serializers.DateTimeField(read_only=True)
	default_amount = serializers.DecimalField(max_digits=10, decimal_places=3, coerce_to_string=False)

	def get_attributes(self, process_type):
		return AttributeSerializer(process_type.attribute_set.filter(is_trashed=False).order_by('rank'), many=True).data

	def get_username(self, product):
		username = product.created_by.username
		return re.sub('_\w+$', '', username)

	class Meta:
		model = ProcessType
		fields = ('id', 'username', 'name', 'code', 'icon', 'attributes', 'unit', 'created_by', 'output_desc', 'created_by_name', 'default_amount', 'team_created_by', 'team_created_by_name', 'is_trashed', 'created_at', 'last_used', 'search')


class ProcessTypeSerializer(serializers.ModelSerializer):
	default_amount = serializers.DecimalField(max_digits=10, decimal_places=3, coerce_to_string=False)

	class Meta:
		model = ProcessType
		fields = ('id', 'name', 'code', 'icon', 'unit', 'created_by', 'output_desc', 'default_amount', 'team_created_by', 'is_trashed', 'created_at', 'search')


class AttributeDetailSerializer(serializers.ModelSerializer):
	last_five_values = serializers.SerializerMethodField(read_only=True)

	def get_last_five_values(self, attribute):
		#need to fix in the future to return only non empty values, and very distinct vals
		return TaskAttribute.objects.filter(attribute=attribute.id).order_by('-updated_at').values('task').distinct().values('value')[:5]

	class Meta:
		model = Attribute
		fields = ('id', 'process_type', 'name', 'rank', 'datatype', 'is_trashed', 'last_five_values')
		read_only_fields = ('id', 'process_type', 'rank', 'last_five_values')


class ProductTypeWithUserSerializer(serializers.ModelSerializer):
	username = serializers.SerializerMethodField(source='get_username', read_only=True)

	def get_username(self, product):
		username = product.created_by.username
		return re.sub('_\w+$', '', username)

	class Meta:
		model = ProductType
		fields = ('id', 'name', 'code', 'created_by', 'is_trashed', 'team_created_by', 'username', 'created_at', 'description', 'search')


class ProductTypeSerializer(serializers.ModelSerializer):
	class Meta:
		model = ProductType
		fields = ('id', 'name', 'code', 'created_by', 'is_trashed', 'team_created_by', 'created_at', 'description', 'search')


class ProductCodeSerializer(serializers.ModelSerializer):
	class Meta:
		model=ProductType
		fields = ('code',)


class UserSerializer(serializers.ModelSerializer):
	processes = ProcessTypeWithUserSerializer(many=True, read_only=True)
	products = ProductTypeWithUserSerializer(many=True, read_only=True)
	class Meta:
		model = User
		fields = ('id', 'username', 'processes', 'products')


# serializes only post-editable fields of task
class EditTaskSerializer(serializers.ModelSerializer):
	#id = serializers.IntegerField(read_only=True)
	created_at = serializers.DateTimeField(read_only=True)
	display = serializers.CharField(source='*', read_only=True)
	process_type = serializers.IntegerField(source='process_type.id', read_only=True)
	product_type = serializers.IntegerField(source='product_type.id', read_only=True)
	num_flagged_ancestors = serializers.IntegerField(read_only=True)
	class Meta:
		model = Task
		fields = ('id', 'is_open', 'custom_display', 'is_trashed', 'is_flagged', 'num_flagged_ancestors', 'flag_update_time', 'display', 'process_type', 'product_type', 'created_at')


class DeleteTaskSerializer(serializers.ModelSerializer):
	class Meta:
		model = Task
		fields = ('id', 'is_trashed')


class BasicItemSerializer(serializers.ModelSerializer):
	is_used = serializers.CharField(read_only=True)

	class Meta:
		model = Item
		fields = ('id', 'item_qr', 'creating_task', 'inventory', 'is_used', 'amount', 'is_virtual', 'team_inventory', 'is_generic')

class BasicInputSerializer(serializers.ModelSerializer):
	input_task_display = serializers.CharField(source='input_item.creating_task', read_only=True)
	input_task = serializers.CharField(source='input_item.creating_task.id', read_only=True)
	input_qr = serializers.CharField(source='input_item.item_qr', read_only=True)
	input_task_n = EditTaskSerializer(source='input_item.creating_task', read_only=True)
	input_item_virtual = serializers.BooleanField(source='input_item.is_virtual', read_only=True)
	input_item_amount = serializers.DecimalField(source='input_item.amount', read_only=True, max_digits=10, decimal_places=3)
	task_display = serializers.CharField(source='task', read_only=True)

	class Meta:
		model = Input
		fields = ('id', 'input_item', 'task', 'amount', 'task_display', 'input_task', 'input_task_display', 'input_qr', 'input_task_n', 'input_item_virtual', 'input_item_amount')


class BasicInputSerializerWithoutAmount(serializers.ModelSerializer):
	input_task_display = serializers.CharField(source='input_item.creating_task', read_only=True)
	input_task = serializers.CharField(source='input_item.creating_task.id', read_only=True)
	input_qr = serializers.CharField(source='input_item.item_qr', read_only=True)
	input_task_n = EditTaskSerializer(source='input_item.creating_task', read_only=True)
	input_item_virtual = serializers.BooleanField(source='input_item.is_virtual', read_only=True)
	input_item_amount = serializers.DecimalField(source='input_item.amount', read_only=True, max_digits=10, decimal_places=3)
	amount = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=3)
	task_display = serializers.CharField(source='task', read_only=True)
	input_task_ingredients = serializers.SerializerMethodField()

	def get_input_task_ingredients(self, input):
		return BasicTaskIngredientSerializer(TaskIngredient.objects.filter(task=input.task), many=True, read_only=True).data

	def create(self, validated_data):
		# can fix this when we remove the amount field from inputs later
		new_input = Input.objects.create(**validated_data)
		input_creating_product = new_input.input_item.creating_task.product_type
		input_creating_process = new_input.input_item.creating_task.process_type
		matching_task_ings = TaskIngredient.objects.filter(task=new_input.task, ingredient__product_type=input_creating_product, ingredient__process_type=input_creating_process)
		if matching_task_ings.count() == 0:
			# if there isn't already a taskIngredient and ingredient for this input's creating task, then make a new one
			ing_query = Ingredient.objects.filter(product_type=input_creating_product, process_type=input_creating_process, recipe=None)
			if(ing_query.count() == 0):
				new_ing = Ingredient.objects.create(recipe=None, product_type=input_creating_product, process_type=input_creating_process, amount=0)
			else:
				new_ing = ing_query[0]
			TaskIngredient.objects.create(ingredient=new_ing, task=new_input.task, actual_amount=new_input.input_item.amount)
		else:
			# when creating an input, if there is already a corresponding task ingredient
			# if the task ingredient has a recipe, set the ingredient's actual_amount to its scaled_amount
			matching_task_ings.exclude(ingredient__recipe=None).update(actual_amount=F('scaled_amount'))
			# if the task ingredient doesn't have a recipe, add the new input's amount to the actual_amount
			matching_task_ings.filter(ingredient__recipe=None).update(actual_amount=F('actual_amount')+new_input.input_item.amount)
		return new_input

	class Meta:
		model = Input
		fields = ('id', 'input_item', 'task', 'amount', 'task_display', 'input_task', 'input_task_display', 'input_qr', 'input_task_n', 'input_item_virtual', 'input_item_amount', 'input_task_ingredients')



# serializes all fields of task
class BasicTaskSerializer(serializers.ModelSerializer):
	display = serializers.CharField(source='*', read_only=True)
	items = BasicItemSerializer(many=True, read_only=True)
	inputs = BasicInputSerializer(many=True, read_only=True)
	num_flagged_ancestors = serializers.IntegerField(read_only=True)

	class Meta:
		model = Task
		fields = ('id', 'process_type', 'product_type', 'label', 'is_open', 'is_flagged', 'num_flagged_ancestors', 'flag_update_time', 'created_at', 'updated_at', 'label_index', 'custom_display', 'is_trashed', 'display', 'items', 'inputs')

	def create(self, validated_data):
		new_task = Task.objects.create(**validated_data)
		return new_task

class BasicTaskSerializerWithOutput(serializers.ModelSerializer):
	display = serializers.CharField(source='*', read_only=True)
	items = BasicItemSerializer(many=True, read_only=True)
	inputs = BasicInputSerializer(many=True, read_only=True)
	task_ingredients = serializers.SerializerMethodField()
	batch_size = serializers.DecimalField(max_digits=10, decimal_places=3, write_only=True, required=True)
	num_flagged_ancestors = serializers.IntegerField(read_only=True)
	recipe_instructions = serializers.SerializerMethodField()

	def get_recipe_instructions(self, task):
		if task.recipe:
			return task.recipe.instructions
		return None

	def get_task_ingredients(self, task):
		return BasicTaskIngredientSerializer(TaskIngredient.objects.filter(task=task), many=True, read_only=True).data

	class Meta:
		model = Task
		extra_kwargs = {'batch_size': {'write_only': True}}
		fields = ('id', 'process_type', 'product_type', 'label', 'is_open', 'is_flagged', 'num_flagged_ancestors', 'flag_update_time', 'created_at', 'updated_at', 'label_index', 'custom_display', 'is_trashed', 'display', 'items', 'inputs', 'task_ingredients', 'batch_size', 'recipe_instructions')

	def create(self, validated_data):
		actual_batch_size = validated_data.pop('batch_size')
		# get all the recipes with the same product type and process type as the task
		# for all the ingredients in all of these recipes, create a taskingredient with the correct scaled_amount
		new_task = Task.objects.create(**validated_data)
		recipes = Recipe.objects.filter(is_trashed=False, product_type=new_task.product_type, process_type=new_task.process_type)
		if recipes.count() > 0:
			new_task.recipe=recipes[0]
			new_task.save()
		qr_code = generateQR()
		new_item = Item.objects.create(creating_task=new_task, item_qr=qr_code, amount=actual_batch_size, is_generic=True)
		ingredients = Ingredient.objects.filter(recipe__is_trashed=False, recipe__product_type=new_task.product_type, recipe__process_type=new_task.process_type)
		default_batch_size = new_task.process_type.default_amount
		if default_batch_size == 0:
			default_batch_size = 1
		for ingredient in ingredients:
			scaled_amount = actual_batch_size*ingredient.amount/default_batch_size
			TaskIngredient.objects.create(task=new_task, ingredient=ingredient, scaled_amount=scaled_amount)
		return new_task


class AlertInputSerializer(serializers.ModelSerializer):
	input_task_display = serializers.CharField(source='task', read_only=True)
	input_task = serializers.CharField(source='task.id', read_only=True)
	input_task_process_icon = serializers.CharField(source='task.process_type.icon', read_only=True)
	input_task_process_name = serializers.CharField(source='task.process_type.name', read_only=True)
	input_task_product_name = serializers.CharField(source='task.product_type.name', read_only=True)
	input_qr = serializers.CharField(source='input_item.item_qr', read_only=True)
	input_task_n = EditTaskSerializer(source='task', read_only=True)
	input_item_virtual = serializers.BooleanField(source='input_item.is_virtual', read_only=True)
	input_item_amount = serializers.DecimalField(source='input_item.amount', read_only=True, max_digits=10, decimal_places=3)
	task_display = serializers.CharField(source='task', read_only=True)

	class Meta:
		model = Input
		fields = ('id', 'input_item', 'task', 'task_display', 'input_task', 'input_task_display', 'input_qr', 'input_task_n', 'input_item_virtual', 'input_item_amount', 'input_task_process_icon', 'input_task_process_name', 'input_task_product_name')


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
	process_type = serializers.SerializerMethodField()
	product_types = serializers.SerializerMethodField()
	runs = serializers.IntegerField()
	amount = serializers.DecimalField(max_digits=10, decimal_places=3, coerce_to_string=False)

	def get_process_type(self, activity):
		return {
			'id': activity['process_type'],
			'name': activity['process_type__name'],
			'code': activity['process_type__code'],
			'unit': activity['process_type__unit'],
			'icon': activity['process_type__icon'],
			'is_trashed': activity['process_type__is_trashed'],
		}

	def get_product_types(self, activity):
		product_types_dict = {}
		for i, id in enumerate(activity['product_type_ids']):
			product_types_dict[id] = {
				'id': id,
				'name': activity['product_type_names'][i],
				'code': activity['product_type_codes'][i],
			}
		return product_types_dict.values()

	class Meta:
		model = Task
		fields = ('runs', 'amount', 'process_type', 'product_types')


class ActivityListDetailSerializer(serializers.ModelSerializer):
	outputs=serializers.CharField(read_only=True)

	class Meta:
		model=Task
		fields = ('id', 'label', 'label_index', 'custom_display', 'outputs')


## ONLY USED AS LOGINSERIALIZER ##
class UserDetailSerializer(serializers.ModelSerializer):
	team_name = serializers.CharField(source='userprofile.team.name')
	team = serializers.CharField(source='userprofile.team.id', read_only=True)
	account_type = serializers.CharField(source='userprofile.account_type', read_only=True)
	profile_id = serializers.CharField(source='userprofile.id')
	user_id = serializers.CharField(source='userprofile.user.id')
	has_gauth_token = serializers.SerializerMethodField('hasGauthToken')
	gauth_email = serializers.CharField(source='userprofile.gauth_email')
	email = serializers.CharField(source='userprofile.email')
	username_display = serializers.CharField(source='userprofile.get_username_display')
	send_emails = serializers.BooleanField(source='userprofile.send_emails')
	last_seen = serializers.DateTimeField(source='userprofile.last_seen', read_only=True)
	walkthrough = serializers.IntegerField(source='userprofile.walkthrough', read_only=True)

	def hasGauthToken(self, user):
		return bool(user.userprofile.gauth_access_token)

	class Meta:
		model = User
		fields = ('user_id', 'profile_id', 'username', 'username_display', 'first_name', 'last_name', 'team', 'account_type', 'team_name', 'has_gauth_token', 'gauth_email', 'email', 'send_emails', 'last_seen', 'walkthrough')


class UserProfileEditSerializer(serializers.ModelSerializer):
	class Meta:
		model = UserProfile
		fields = ('id', 'account_type', 'send_emails', 'email')


class UserProfileSerializer(serializers.ModelSerializer):
	team_name = serializers.CharField(source='team.name', read_only=True)
	team = serializers.CharField(source='team.id', read_only=True)
	profile_id = serializers.CharField(source='id', read_only=True)
	user_id = serializers.CharField(source='user.id', read_only=True)
	username = serializers.CharField(source='user.username', read_only=True)
	username_display = serializers.CharField(source='get_username_display', read_only=True)
	first_name = serializers.CharField(source='user.first_name')
	last_name = serializers.CharField(source='user.last_name')
	walkthrough = serializers.IntegerField(read_only=True)

	class Meta:
		model = UserProfile
		fields = ('user_id', 'id', 'profile_id', 'username', 'username_display', 'first_name', 'last_name', 'team', 'account_type', 'team_name', 'gauth_access_token', 'gauth_email', 'email', 'send_emails', 'last_seen', 'walkthrough')


def sendEmail(userprofile_id):
  userprofile = UserProfile.objects.get(pk=userprofile_id)
  team_name = userprofile.team.name
  email = userprofile.email

  link = "https://dashboard.usepolymer.com/join/" + str(userprofile_id) + "/"

  subject = "You're invited to team " + team_name + " on Polymer!"
  message = ""
  html_message = "You have been invited to join team: <b>" + team_name + '</b> on Polymer. Click the link to accept your invitation and set your username/password. ' + link
  try:
    send_mail(
        subject,
        message,
        'admin@polymerize.co',
        [email],
        fail_silently=False,
        html_message=html_message,
    )
  except SMTPException as e:
    print('send_mail failed: ', e)


class UserProfileCreateSerializer(serializers.ModelSerializer):
	username = serializers.CharField(source='user.username')
	password = serializers.CharField(source='user.password')
	first_name = serializers.CharField(source='user.first_name')
	last_name = serializers.CharField(source='user.last_name')
	team_name = serializers.CharField(source='team.name', read_only=True)
	profile_id = serializers.CharField(source='id', read_only=True)
	username_display = serializers.CharField(source='get_username_display', read_only=True)
	walkthrough = serializers.IntegerField(read_only=True)
	email = serializers.CharField()
	invited = serializers.BooleanField(write_only=True)

	def create(self, validated_data):
		team = validated_data['team']
		data = validated_data['user']
		long_username = data['username'] + '_' + team.name

		# create the user 
		user = User.objects.create(username=long_username, first_name=data['first_name'], last_name=data['last_name'])
		user.set_password(data.get('password'))
		user.save()

		# create the userprofile
		account_type = validated_data.get('account_type', 'a')
		email = validated_data.get('email', '')
		invited = validated_data.get('invited', False)

		print(invited)

		walkthrough_num = 1
		if invited:
			walkthrough_num = -1

		userprofile = UserProfile.objects.create(
			user=user,
			gauth_access_token="",
			gauth_refresh_token="",
			token_type="",
			team=team,
			account_type=account_type,
			email=email,
			walkthrough=walkthrough_num
		)

		if invited:
			sendEmail(userprofile.id)

		return userprofile

	class Meta:
		model = UserProfile
		extra_kwargs = {'account_type': {'write_only': True}, 'password': {'write_only': True}, 'invited': {'write_only': True}}
		fields = ('id', 'profile_id', 'username', 'password', 'first_name', 'last_name', 'team', 'account_type', 'team_name', 'gauth_email', 'email', 'username_display', 'walkthrough', 'email', 'invited')


class TeamSerializer(serializers.ModelSerializer):
	processes = serializers.SerializerMethodField('getProcesses')
	products = serializers.SerializerMethodField('getProducts')
	users = UserProfileSerializer(source='userprofiles', many=True, read_only=True)

	def getProcesses(self, team):
		return ProcessTypeWithUserSerializer(team.processes.filter(is_trashed=False), many=True).data

	def getProducts(self, team):
		return ProductTypeWithUserSerializer(team.products.filter(is_trashed=False), many=True).data


	class Meta:
		model = Team
		fields = ('id', 'name', 'users', 'products', 'processes')
# 

class BasicPinSerializer(serializers.ModelSerializer):
	process_name = serializers.CharField(source='process_type.name', read_only=True)
	process_unit = serializers.CharField(source='process_type.unit', read_only=True)
	product_code = serializers.SerializerMethodField('get_product_types')
	process_icon = serializers.CharField(source='process_type.icon', read_only=True)
	input_products = serializers.CharField(write_only=True, required=False)

	def get_product_types(self, goal):
		return ProductTypeSerializer(goal.product_types, many=True).data

	def create(self, validated_data):
		product_types = validated_data.get('input_products', '')

		pin = Pin.objects.create(
			userprofile=validated_data.get('userprofile', ''),
			process_type=validated_data.get('process_type', ''),
			all_product_types=(product_types == "ALL"),
		)

		if product_types != 'ALL':
			for product_type in product_types.split(','):
				pin.product_types.add(product_type)
			pin.save()

		return pin

	class Meta:
		model = Pin
		fields = ('id', 'all_product_types', 'input_products', 'process_type', 'process_name', 'process_unit', 'product_code', 'is_trashed', 'userprofile', 'created_at', 'process_icon')
		extra_kwargs = {'input_products': {'write_only': True} }

class BasicGoalSerializer(serializers.ModelSerializer):
	actual = serializers.SerializerMethodField(source='get_actual', read_only=True)
	process_name = serializers.CharField(source='process_type.name', read_only=True)
	process_unit = serializers.CharField(source='process_type.unit', read_only=True)
	process_icon = serializers.CharField(source='process_type.icon', read_only=True)
	product_code = serializers.SerializerMethodField('get_product_types')
	userprofile_name = serializers.SerializerMethodField()

	def get_userprofile_name(self, goal):
		user = goal.userprofile.user
		if user.first_name and user.last_name:
			return user.first_name + ' ' + user.last_name[0] + '.'
		else:
			return user.username.split('_')[0]

	def get_product_types(self, goal):
		return ProductTypeSerializer(goal.product_types, many=True).data

	def get_actual(self, goal):
		base = date.today()
		min_time = pytz.utc.localize(datetime.min.time())
		start = datetime.combine(base - timedelta(days=base.weekday()), min_time)
		end = datetime.combine(base + timedelta(days=1), min_time)

		if goal.timerange == 'w':
			start = datetime.combine(base - timedelta(days=base.weekday()), min_time)
		elif goal.timerange == 'd':
			start = datetime.combine(base, min_time)
		elif goal.timerange == 'm':
			start = datetime.combine(base.replace(day=1), min_time)

		product_types = ProductType.objects.filter(goal_product_types__goal=goal)
		if goal.all_product_types:
			product_types = ProductType.objects.filter(team_created_by=goal.userprofile.team)

		#TODO Optimize "actual" calculation into fewer queries
		return Item.objects.filter(
			creating_task__process_type=goal.process_type,
			creating_task__product_type__in=product_types,
			creating_task__is_trashed=False,
			creating_task__created_at__range=(start, end),
			is_virtual=False,
		).aggregate(amount_sum=Sum('amount'))['amount_sum']

	class Meta:
		model = Goal
		fields = ('id', 'all_product_types', 'process_type', 'goal', 'actual', 'process_name', 'process_unit', 'process_icon', 'product_code', 'timerange', 'rank', 'is_trashed', 'trashed_time', 'userprofile_name', 'userprofile')


class GoalCreateSerializer(serializers.ModelSerializer):
	process_name = serializers.CharField(source='process_type.name', read_only=True)
	process_unit = serializers.CharField(source='process_type.unit', read_only=True)
	process_icon = serializers.CharField(source='process_type.icon', read_only=True)
	product_code = serializers.SerializerMethodField('get_product_types')
	input_products = serializers.CharField(write_only=True, required=False)
	rank = serializers.IntegerField(read_only=True)
	userprofile_name = serializers.SerializerMethodField()
	all_product_types = serializers.BooleanField(read_only=True)

	def get_userprofile_name(self, goal):
		user = goal.userprofile.user
		if user.first_name and user.last_name:
			return user.first_name + ' ' + user.last_name[0] + '.'
		else:
			return user.username.split('_')[0]

	def get_product_types(self, goal):
		return ProductTypeWithUserSerializer(ProductType.objects.filter(goal_product_types__goal=goal), many=True).data

	def create(self, validated_data):
		validation_error_msg = {'process_type': 'A goal already exists for this Time Frame, Product Type, and Process Type(s) combination'}
		userprofile = validated_data.get('userprofile', '')
		inputprods = validated_data.get('input_products', '')
		process_type = validated_data.get('process_type', '')
		goals_goal = validated_data.get('goal', '')
		timerange = validated_data.get('timerange', '')
		all_product_types = (inputprods == "ALL")
		goal_product_types = []

		# if we didn't mean to put all product types in this goal:
		if (inputprods and not all_product_types):
			goal_product_types = inputprods.strip().split(',')

		# 1. Reject Duplicate Goal (if needed):
		# Filter for duplicates using all properties except Product Types
		possible_duplicates = Goal.objects.filter(
			is_trashed=False,
			all_product_types=all_product_types,
			timerange=timerange,
			process_type=process_type,
			userprofile__team=userprofile.team
		)

		# Filter for duplicate Product Types
		if not all_product_types: # we need to check product_ids
			product_clauses = (Q(arr__contains=product_id) for product_id in goal_product_types)
			has_all_products = reduce(operator.or_, product_clauses)
			annotated_possible_duplicates = possible_duplicates.annotate(
				arr=ArrayAgg('goal_product_types__product_type__id', order_by='goal_product_types__product_type__id'),
				count=Count('goal_product_types__product_type__id')
			) \
				.values_list('id', 'arr', 'count')
			# Count prevents [1,2] from matching [1,2,3]:
			possible_duplicates = annotated_possible_duplicates.filter(has_all_products).filter(count=len(goal_product_types))

		if possible_duplicates.count() is not 0:
			raise serializers.ValidationError(validation_error_msg)

		# 2. All Clear: Create Goal
		goal = Goal.objects.create(
			userprofile=userprofile,
			process_type=process_type,
			goal=goals_goal,
			timerange=timerange,
			all_product_types=all_product_types
		)

		# Create many-to-many relationships between Goal and Product Types
		for gp in goal_product_types:
			GoalProductType.objects.create(product_type=ProductType.objects.get(pk=gp), goal=goal)
		return goal

	class Meta:
		model = Goal
		fields = ('id', 'all_product_types', 'process_type', 'input_products', 'goal', 'process_name', 'process_unit', 'process_icon', 'product_code', 'userprofile', 'timerange', 'rank', 'is_trashed', 'trashed_time', 'userprofile_name', 'created_at')
		extra_kwargs = {'input_products': {'write_only': True} }


def reorder(instance, validated_data, dataset):
	old_rank = instance.rank
	new_rank = validated_data.get('new_rank', instance.rank)
	if old_rank <= new_rank:
		values = range(old_rank+1, new_rank+1)
		attrs = dataset.filter(rank__in=values)
		attrs.update(rank=F('rank') - 1)
	else:
		values = range(new_rank, old_rank)
		attrs = dataset.filter(rank__in=values)
		attrs.update(rank=F('rank') + 1)
	instance.rank = new_rank
	instance.save()
	return instance


class ReorderAttributeSerializer(serializers.ModelSerializer):
	new_rank = serializers.IntegerField(write_only=True)

	def update(self, instance, validated_data):
		return reorder(
			instance,
			validated_data,
			Attribute.objects.filter(is_trashed=False, process_type=instance.process_type)
		)

	class Meta:
		model = Attribute
		fields = ('id', 'new_rank')
		extra_kwargs = {'new_rank': {'write_only': True} }


class ReorderGoalSerializer(serializers.ModelSerializer):
	new_rank = serializers.IntegerField(write_only=True)

	def update(self, instance, validated_data):
		return reorder(
			instance,
			validated_data,
			Goal.objects.filter(userprofile=instance.userprofile, timerange=instance.timerange)
		)

	class Meta:
		model = Goal
		fields = ('id', 'new_rank')
		extra_kwargs = {'new_rank': {'write_only': True} }


class AlertSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)

	class Meta:
		model = Alert
		fields = ('id', 'alert_type', 'variable_content', 'is_displayed', 'userprofile', 'created_at')


class UserProfileChangePasswordSerializer(serializers.ModelSerializer):
	team_name = serializers.CharField(source='team.name', read_only=True)
	team = serializers.CharField(source='team.id', read_only=True)
	profile_id = serializers.CharField(source='id', read_only=True)
	user_id = serializers.CharField(source='user.id', read_only=True)
	username = serializers.CharField(source='user.username', read_only=True)
	username_display = serializers.CharField(source='get_username_display', read_only=True)
	first_name = serializers.CharField(source='user.first_name', read_only=True)
	last_name = serializers.CharField(source='user.last_name', read_only=True)
	walkthrough = serializers.IntegerField(read_only=True)
	new_password = serializers.CharField(write_only=True, required=True)
	new_username = serializers.CharField(write_only=True, required=True)

	def update(self, instance, validated_data):
		new_pass = validated_data.get('new_password', None)
		new_uname = validated_data.get('new_username', None)
		user = instance.user
		if(new_pass):
			user.set_password(new_pass)
		if(new_uname):
			try:
				user.username = new_uname + "_" + instance.team.name
				user.full_clean()
			except ValidationError:
				raise serializers.ValidationError({"username": "Username already exists"})
			else:
				user.save()
		user.save()
		return instance

	class Meta:
		model = UserProfile
		extra_kwargs = {'new_password': {'write_only': True}, 'new_username': {'write_only': True}}
		fields = ('user_id', 'id', 'profile_id', 'username', 'username_display', 'first_name', 'last_name', 'team', 'account_type', 'team_name', 'gauth_access_token', 'gauth_email', 'email', 'send_emails', 'last_seen', 'walkthrough', 'new_password', 'new_username')


class UpdateUserProfileLastSeenSerializer(serializers.ModelSerializer):
	team_name = serializers.CharField(source='team.name', read_only=True)
	team = serializers.CharField(source='team.id', read_only=True)
	profile_id = serializers.CharField(source='id', read_only=True)
	user_id = serializers.CharField(source='user.id', read_only=True)
	username = serializers.CharField(source='user.username', read_only=True)
	username_display = serializers.CharField(source='get_username_display', read_only=True)
	first_name = serializers.CharField(source='user.first_name', read_only=True)
	last_name = serializers.CharField(source='user.last_name', read_only=True)
	walkthrough = serializers.IntegerField(read_only=True)

	def update(self, instance, validated_data):
		instance.last_seen = datetime.now()
		instance.save()
		return instance

	class Meta:
		model = UserProfile
		fields = ('user_id', 'id', 'profile_id', 'username', 'username_display', 'first_name', 'last_name', 'team', 'account_type', 'team_name', 'gauth_access_token', 'gauth_email', 'email', 'send_emails', 'last_seen', 'walkthrough')

class IncrementUserProfileWalkthroughSerializer(serializers.ModelSerializer):
	team_name = serializers.CharField(source='team.name', read_only=True)
	team = serializers.CharField(source='team.id', read_only=True)
	profile_id = serializers.CharField(source='id', read_only=True)
	user_id = serializers.CharField(source='user.id', read_only=True)
	username = serializers.CharField(source='user.username', read_only=True)
	username_display = serializers.CharField(source='get_username_display', read_only=True)
	first_name = serializers.CharField(source='user.first_name', read_only=True)
	last_name = serializers.CharField(source='user.last_name', read_only=True)
	last_seen = serializers.DateTimeField(read_only=True)
	walkthrough = serializers.IntegerField(read_only=True)

	def update(self, instance, validated_data):
		current_walkthrough_screen = instance.walkthrough
		instance.walkthrough = current_walkthrough_screen + 1
		instance.save()
		return instance

	class Meta:
		model = UserProfile
		fields = ('user_id', 'id', 'profile_id', 'username', 'username_display', 'first_name', 'last_name', 'team', 'account_type', 'team_name', 'gauth_access_token', 'gauth_email', 'email', 'send_emails', 'last_seen', 'walkthrough')


class CompleteUserProfileWalkthroughSerializer(serializers.ModelSerializer):
	team_name = serializers.CharField(source='team.name', read_only=True)
	team = serializers.CharField(source='team.id', read_only=True)
	profile_id = serializers.CharField(source='id', read_only=True)
	user_id = serializers.CharField(source='user.id', read_only=True)
	username = serializers.CharField(source='user.username', read_only=True)
	username_display = serializers.CharField(source='get_username_display', read_only=True)
	first_name = serializers.CharField(source='user.first_name', read_only=True)
	last_name = serializers.CharField(source='user.last_name', read_only=True)
	last_seen = serializers.DateTimeField(read_only=True)
	# walkthrough = serializers.IntegerField(read_only=True)

	def update(self, instance, validated_data):
		instance.walkthrough = -1
		instance.save()
		return instance

	class Meta:
		model = UserProfile
		fields = ('user_id', 'id', 'profile_id', 'username', 'username_display', 'first_name', 'last_name', 'team', 'account_type', 'team_name', 'gauth_access_token', 'gauth_email', 'email', 'send_emails', 'last_seen', 'walkthrough')


class ClearUserProfileTokenSerializer(serializers.ModelSerializer):
	team_name = serializers.CharField(source='team.name', read_only=True)
	team = serializers.CharField(source='team.id', read_only=True)
	profile_id = serializers.CharField(source='id', read_only=True)
	user_id = serializers.CharField(source='user.id', read_only=True)
	username = serializers.CharField(source='user.username', read_only=True)
	username_display = serializers.CharField(source='get_username_display', read_only=True)
	first_name = serializers.CharField(source='user.first_name', read_only=True)
	last_name = serializers.CharField(source='user.last_name', read_only=True)
	last_seen = serializers.DateTimeField(read_only=True)
	# walkthrough = serializers.IntegerField(read_only=True)

	def update(self, instance, validated_data):
		instance.gauth_email = ""
		instance.gauth_access_token = ""
		instance.gauth_refresh_token = ""
		instance.expires_in = 0
		instance.expires_at = 0
		instance.save()
		return instance

	class Meta:
		model = UserProfile
		fields = ('user_id', 'id', 'profile_id', 'username', 'username_display', 'first_name', 'last_name', 'team', 'account_type', 'team_name', 'gauth_access_token', 'gauth_email', 'email', 'send_emails', 'last_seen', 'walkthrough')


class AdjustmentSerializer(serializers.ModelSerializer):
	created_at = serializers.DateTimeField(read_only=True)
	amount = serializers.DecimalField(max_digits=10, decimal_places=3, coerce_to_string=False)

	class Meta:
		model = Adjustment
		fields = ('userprofile', 'created_at', 'process_type', 'product_type', 'amount', 'explanation')


class InventoryList2Serializer(serializers.Serializer):
	process_id = serializers.CharField(source='creating_task__process_type')
	process_name = serializers.CharField(source='creating_task__process_type__name')
	process_unit = serializers.CharField(source='creating_task__process_type__unit')
	process_code = serializers.CharField(source='creating_task__process_type__code')
	process_icon = serializers.CharField(source='creating_task__process_type__icon')
	product_id = serializers.CharField(source='creating_task__product_type')
	product_name = serializers.CharField(source='creating_task__product_type__name')
	product_code = serializers.CharField(source='creating_task__product_type__code')
	adjusted_amount = serializers.SerializerMethodField(source='get_adjusted_amount')

	def old_get_adjusted_amount(self, item_summary):
		process_type = item_summary['creating_task__process_type']
		product_type = item_summary['creating_task__product_type']

		starting_total = 0

		latest_adjustment = Adjustment.objects \
			.filter(process_type=process_type, product_type=product_type, userprofile__team=item_summary['team_inventory']) \
			.order_by('-created_at').first()

		items_query = Item.active_objects.exclude(creating_task__process_type__code__in=['SH','D']).filter(
			creating_task__process_type=process_type,
			creating_task__product_type=product_type,
			team_inventory=item_summary['team_inventory'],
		)

		if latest_adjustment:
			start_time = latest_adjustment.created_at
			items_query = items_query.filter(created_at__gt=start_time)
			starting_total = latest_adjustment.amount

		created_amount = old_inventory_created_amount(items_query)
		used_amount = old_inventory_used_amount(items_query)

		return starting_total + created_amount - used_amount

	def get_adjusted_amount(self, item_summary):
		process_type = item_summary['creating_task__process_type']
		product_type = item_summary['creating_task__product_type']
		start_time = None
		starting_amount = 0

		latest_adjustment = Adjustment.objects \
			.filter(process_type=process_type, product_type=product_type, userprofile__team=item_summary['team_inventory']) \
			.order_by('-created_at').first()

		if latest_adjustment:
			start_time = latest_adjustment.created_at
			starting_amount = latest_adjustment.amount

		data = inventory_amounts(process_type, product_type, start_time, None)
		return starting_amount + data['created_amount'] - data['used_amount']


class ItemSummarySerializer(serializers.Serializer):
	date = serializers.SerializerMethodField()
	type = serializers.SerializerMethodField()
	data = serializers.SerializerMethodField()

	def get_date(self, obj):
		return self.context.get('date')

	def get_type(self, obj):
		return 'item_summary'

	def get_data(self, obj):
		return obj


class AdjustmentHistorySerializer(serializers.Serializer):
	date = serializers.SerializerMethodField()
	type = serializers.SerializerMethodField()
	data = serializers.SerializerMethodField()

	def get_date(self, obj):
		return obj.created_at

	def get_type(self, obj):
		return 'adjustment'

	def get_data(self, obj):
		return AdjustmentSerializer(obj).data

class IngredientSerializer(serializers.ModelSerializer):
	process_type = ProcessTypeWithUserSerializer(read_only=True)
	process_type_id = serializers.PrimaryKeyRelatedField(source='process_type', queryset=ProcessType.objects.all(), write_only=True)
	product_type = ProductTypeWithUserSerializer(read_only=True)
	product_type_id = serializers.PrimaryKeyRelatedField(source='product_type', queryset=ProductType.objects.all(), write_only=True)
	amount = serializers.DecimalField(max_digits=10, decimal_places=3)
	recipe_id = serializers.PrimaryKeyRelatedField(source='recipe', queryset=Recipe.objects.all())

	class Meta:
		model = Ingredient
		fields = ('id', 'product_type', 'process_type', 'process_type_id', 'product_type_id', 'amount', 'recipe_id')

class RecipeSerializer(serializers.ModelSerializer):
	process_type = ProcessTypeWithUserSerializer(read_only=True)
	process_type_id = serializers.PrimaryKeyRelatedField(source='process_type', queryset=ProcessType.objects.all(), write_only=True)
	product_type = ProductTypeWithUserSerializer(read_only=True)
	product_type_id = serializers.PrimaryKeyRelatedField(source='product_type', queryset=ProductType.objects.all(), write_only=True)
	ingredients = serializers.SerializerMethodField(read_only=True)
	has_task_ingredients = serializers.SerializerMethodField(read_only=True)

	def get_has_task_ingredients(self, recipe):
		return TaskIngredient.objects.filter(ingredient__recipe=recipe).count() > 0

	def get_ingredients(self, recipe):
		return IngredientSerializer(Ingredient.objects.filter(recipe=recipe), many=True).data

	class Meta:
		model = Recipe
		fields = ('id', 'instructions', 'product_type', 'process_type', 'process_type_id', 'product_type_id', 'ingredients', 'is_trashed', 'has_task_ingredients')

class BasicTaskIngredientSerializer(serializers.ModelSerializer):
	ingredient = IngredientSerializer(read_only=True)
	ingredient_id = serializers.PrimaryKeyRelatedField(source='ingredient', queryset=Ingredient.objects.all(), write_only=True)

	class Meta:
		model = TaskIngredient
		fields = ('id', 'ingredient', 'ingredient_id', 'task', 'scaled_amount', 'actual_amount')
