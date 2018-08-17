from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.contrib.postgres.aggregates import StringAgg
from django.contrib.postgres.indexes import GinIndex
from uuid import uuid4
from django.db.models import Max
import constants
from django.utils import timezone
import pytz
from django.db.models.expressions import RawSQL
from django.db.models import F
# from ics.async_actions import *


# AUTH MODELS
class InviteCode(models.Model):
	invite_code = models.CharField(max_length=100, unique=True, db_index=True)
	is_used = models.BooleanField(default=False, db_index=True)

class Team(models.Model):
	TIME_FORMATS = (
		('m', 'military'),
		('n', 'normal')
	)

	name = models.CharField(max_length=50, unique=True)
	timezone = models.CharField(max_length=50, default=pytz.timezone('US/Pacific').zone)
	task_label_type = models.IntegerField(default=0)
	time_format = models.CharField(max_length=1, choices=TIME_FORMATS, default='n')

	def __str__(self):
		return self.name

class UserProfile(models.Model):
	USERTYPES = (
		('a', 'admin'),
		('w', 'worker'),
	)

	user = models.OneToOneField(User, on_delete=models.CASCADE)
	gauth_access_token = models.TextField(null=True)
	gauth_refresh_token = models.TextField(null=True)
	token_type = models.CharField(max_length=100, null=True) 
	expires_in = models.IntegerField(null=True)
	expires_at = models.FloatField(null=True)
	gauth_email = models.TextField(null=True)
	email = models.TextField(null=True)
	team = models.ForeignKey(Team, related_name='userprofiles', on_delete=models.CASCADE, null=True)
	account_type = models.CharField(max_length=1, choices=USERTYPES, default='a')
	send_emails = models.BooleanField(default=True)
	last_seen = models.DateTimeField(default=timezone.now)
	walkthrough = models.IntegerField(default=1)

	def get_username_display(self):
		print(self.user.username)
		username_pieces = self.user.username.rsplit('_', 1)
		return username_pieces[0]



############################
#                          #
#    POLYMER CORE MODELS   #
#                          #
############################

class ProcessTypeManager(models.Manager):
	def with_documents(self):
		vector = SearchVector('name') + \
		SearchVector('code') + \
		SearchVector('output_desc')
		return self.get_queryset().annotate(document=vector)


class ProcessType(models.Model):

	created_by = models.ForeignKey(User, related_name='processes', on_delete=models.CASCADE)
	team_created_by = models.ForeignKey(Team, related_name='processes', on_delete=models.CASCADE)
	name = models.CharField(max_length=50)
	code = models.CharField(max_length=20)
	category = models.CharField(max_length=50, choices=constants.CATEGORIES, default=constants.WIP)
	icon = models.CharField(max_length=50)
	created_at = models.DateTimeField(default=timezone.now, blank=True)
	description = models.CharField(max_length=1, default="", blank=True)  # SCHEDULED FOR DELETION
	output_desc = models.CharField(max_length=200, default="product")
	default_amount = models.DecimalField(default=0, max_digits=10, decimal_places=3)
	unit = models.CharField(max_length=20, default="container")

	x = models.DecimalField(default=0, max_digits=10, decimal_places=3, db_index=True)  # SCHEDULED FOR DELETION
	y = models.DecimalField(default=0, max_digits=10, decimal_places=3)  # SCHEDULED FOR DELETION

	default_amount = models.DecimalField(default=0, max_digits=10, decimal_places=3)
	is_trashed = models.BooleanField(default=False, db_index=True)
	keywords = models.CharField(max_length=200, blank=True)
	search = SearchVectorField(null=True)

	objects = ProcessTypeManager()

	class Meta:
		indexes = [
			GinIndex(fields=['search'])
		]
		ordering = ['x',]


	def __str__(self):
		return self.name

	def save(self, *args, **kwargs):
		self.refreshKeywords()
		super(ProcessType, self).save(*args, **kwargs)
		if 'update_fields' not in kwargs or 'search' not in kwargs['update_fields']:
			instance = self._meta.default_manager.with_documents().filter(pk=self.pk)[0]
			instance.search = instance.document
			instance.save(update_fields=['search'])

	def refreshKeywords(self):
		self.keywords = " ".join([
			self.code, 
			self.name, 
			self.output_desc,
		])[:200]

	def getAllAttributes(self):
		return self.attribute_set.filter(is_trashed=False)

	def get_last_used_date(self):
		last_task = Task.objects.filter(is_trashed=False, process_type=self.id).order_by('-created_at').first()
		if last_task:
			return last_task.created_at
		else:
			return None

class ProductTypeManager(models.Manager):
	def with_documents(self):
		vector = SearchVector('name') + \
		SearchVector('code') + \
		SearchVector('description')
		return self.get_queryset().annotate(document=vector)

class ProductType(models.Model):
	created_by = models.ForeignKey(User, related_name='products', on_delete=models.CASCADE)
	team_created_by = models.ForeignKey(Team, related_name='products', on_delete=models.CASCADE)
	created_at = models.DateTimeField(default=timezone.now, blank=True)
	name = models.CharField(max_length=200)
	code = models.CharField(max_length=20)
	description = models.CharField(max_length=200, default="")
	is_trashed = models.BooleanField(default=False, db_index=True)
	keywords = models.CharField(max_length=200, blank=True)
	search = SearchVectorField(null=True)

	objects = ProductTypeManager()

	class Meta:
		indexes = [
			GinIndex(fields=['search'])
		]

	def __str__(self):
		return self.name

	def save(self, *args, **kwargs):
		self.refreshKeywords()
		super(ProductType, self).save(*args, **kwargs)
		if 'update_fields' not in kwargs or 'search' not in kwargs['update_fields']:
			instance = self._meta.default_manager.with_documents().filter(pk=self.pk)[0]
			instance.search = instance.document
			instance.save(update_fields=['search'])

	def refreshKeywords(self):
		self.keywords = " ".join([
			self.code, 
			self.name, 
			self.description, 
		])[:200]

class Attribute(models.Model):
	process_type = models.ForeignKey(ProcessType, on_delete=models.CASCADE)
	name = models.CharField(max_length=20)
	rank = models.PositiveSmallIntegerField(default=0, db_index=True)
	is_trashed = models.BooleanField(default=False, db_index=True)
	datatype = models.CharField(
		max_length=4, 
		choices=constants.ATTRIBUTE_DATA_TYPES, 
		default=constants.TEXT_TYPE
	)
	required = models.BooleanField(default=True)
	is_recurrent = models.BooleanField(default=False)

	def duplicate(self, duplicate_process):
		attr = Attribute.objects.create(
			process_type=duplicate_process,
			name=self.name,
			rank=self.rank,
			is_trashed=self.is_trashed,
			datatype=self.datatype,
			required=self.required,
		)
		attr.rank = self.rank
		attr.save()
		return attr

	def __str__(self):
		return self.name

	def save(self, *args, **kwargs):
		# create the right rank
		if self.pk is None:
			prev_rank = Attribute.objects.filter(
				process_type=self.process_type, 
				is_trashed=False
			).aggregate(Max('rank'))['rank__max']
			if prev_rank is None:
				prev_rank = -1
			self.rank = prev_rank + 1
		super(Attribute, self).save(*args, **kwargs)


class Recipe(models.Model):
	product_type = models.ForeignKey(ProductType, related_name="recipes", on_delete=models.CASCADE)
	process_type = models.ForeignKey(ProcessType, related_name="recipes", on_delete=models.CASCADE)
	instructions = models.TextField(null=True)
	is_trashed = models.BooleanField(default=False, db_index=True)

class TaskManager(models.Manager):
	def with_documents(self):
		vector = SearchVector('process_type__name') + \
		SearchVector('product_type__name') + \
		SearchVector('label') + \
		SearchVector('custom_display') + \
		SearchVector('experiment') + \
		SearchVector('keywords') + \
		SearchVector('attribute_values__value') + \
		SearchVector('process_type__team_created_by__name') + \
		SearchVector(StringAgg('items__readable_qr', delimiter=' '))
		# vector = SearchVector('process_type__name', weight='D') + \
		#     SearchVector('product_type__name', weight='C') + \
		#     SearchVector('label', weight='A') + \
		#     SearchVector('custom_display', weight='B') + \
		#     SearchVector('experiment', weight='E') + \
		#     SearchVector('keywords', weight='F')
		return self.get_queryset().annotate(document=vector)


class Task(models.Model):
	recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="tasks", null=True)
	process_type = models.ForeignKey(ProcessType, on_delete=models.CASCADE, related_name="tasks")
	product_type = models.ForeignKey(ProductType, on_delete=models.CASCADE)
	label = models.CharField(max_length=50, db_index=True)  
	label_index = models.PositiveSmallIntegerField(default=0, db_index=True)
	custom_display = models.CharField(max_length=50, blank=True)
	#created_by = models.ForeignKey(User, on_delete=models.CASCADE)
	is_open = models.BooleanField(default=True)
	is_trashed = models.BooleanField(default=False, db_index=True)
	created_at = models.DateTimeField(auto_now_add=True, db_index=True)
	updated_at = models.DateTimeField(auto_now=True, db_index=True)
	is_flagged = models.BooleanField(default=False, db_index=True)
	flag_update_time = models.DateTimeField(default='2017-01-01 23:25:26.835087+00:00')
	old_is_flagged = models.BooleanField(default=False)
	was_flag_changed = models.BooleanField(default=False)
	# all our signals are getting triggered twice for some reason so the num_flagged_ancestors is incremented and decremented by 2
	num_flagged_ancestors = models.IntegerField(default=0)
	experiment = models.CharField(max_length=25, blank=True)
	keywords = models.CharField(max_length=200, blank=True)
	search = SearchVectorField(null=True)

	objects = TaskManager()

	class Meta:
		indexes = [
			GinIndex(fields=['search'])
		]

	def __init__(self, *args, **kwargs):
		super(Task, self).__init__(*args, **kwargs)
		self.old_is_flagged = self.is_flagged

	def __str__(self):
		if self.custom_display:
			return self.custom_display
		if self.label_index > 0:
			return "-".join([self.label, str(self.label_index)])
		return self.label

	def save(self, *args, **kwargs):
		self.setLabelAndDisplay()
		self.refreshKeywords()
		# update the flag_update_time if the flag is toggled
		if self.old_is_flagged != self.is_flagged:
			self.flag_update_time = timezone.now()
			self.was_flag_changed = True
		else:
			self.was_flag_changed = False

		super(Task, self).save(*args, **kwargs)
		self.old_is_flagged = self.is_flagged
		
		if 'update_fields' not in kwargs or 'search' not in kwargs['update_fields']:
			instance = self._meta.default_manager.with_documents().filter(pk=self.pk)[0]
			instance.search = instance.document
			instance.save(update_fields=['search'])

	def setLabelAndDisplay(self):
		"""
		Calculates the display text based on whether there are any other
		tasks with the same label and updates it accordingly
		----
		task.setLabelAndDisplay()
		task.save()
		"""
		if self.pk is None:
			# get the number of tasks with the same label from this year
			q = ( 
				Task.objects.filter(label=self.label)
					.filter(created_at__startswith=str(timezone.now().year))
					.order_by('-label_index')
				)
			numItems = len(q)

			# if there are other items with the same name, then get the
			# highest label_index and set our label_index to that + 1
			if numItems > 0:
				self.label_index = q[0].label_index + 1

	def getInventoryItems(self):
		return self.items.filter(input__isnull=True)

	def getTaskAttributes(self):
		return self.taskattribute_set.filter(attribute__is_trashed=False)

	def refreshKeywords(self):
		"""
		Calculates a list of keywords from the task's fields and the task's
		attributes and updates the task.
		----
		task.refreshKeywords()
		task.save()
		"""
		p1 = " ".join([
			self.process_type.code, 
			self.process_type.name, 
			self.product_type.code, 
			self.product_type.name,
			self.custom_display, 
			self.label, 
			"-".join([self.label,str(self.label_index)]),
		])

		p2 = " ".join(self.custom_display.split("-"))

		p3 = " ".join(self.label.split("-"))

		p4 = ""
		if self.pk is not None: 
			p4 = " ".join(TaskAttribute.objects.filter(task=self).values_list('value', flat=True))

		self.keywords = " ".join([p1, p2, p3, p4])[:200]
		#self.search = SearchVector('label', 'custom_display')

	def descendants_raw_query(self):
		return RawSQL(""" WITH RECURSIVE descendants AS (
	    (SELECT task.id, input.task_id as parent_id
			FROM ics_task task
		    JOIN ics_item item
		      ON item.creating_task_id = task.id
		    JOIN ics_input input
		    ON  input.input_item_id = item.id 
			WHERE task.id = %s AND task.is_trashed = false)
		    UNION ALL
		    SELECT ct.id, cin.task_id as parent_id
		    FROM ics_task ct
		    JOIN ics_item cit
		      ON cit.creating_task_id = ct.id
		    JOIN ics_input cin
		      ON cin.input_item_id = cit.id
		    JOIN descendants p ON p.parent_id = ct.id
		    WHERE ct.is_trashed = false
		  )
		 SELECT distinct parent_id
		 FROM descendants
		 WHERE parent_id <> %s""", [str(self.id), str(self.id)])

	
	def descendants(self):
		return Task.objects.filter(id__in=self.descendants_raw_query())

	def ancestors_raw_query(self):
		return RawSQL("""WITH RECURSIVE descendants AS (
			SELECT input.input_item_id as child_input_id, task.id as child_task_id
			    FROM ics_input input
			    JOIN ics_item item
			    ON item.id = input.input_item_id
			    JOIN ics_task task
			     ON task.id = item.creating_task_id
			    WHERE input.task_id = %s AND task.is_trashed = false
			  UNION ALL
			    SELECT cin.input_item_id as child_input_id, ct.id as child_task_id
			    FROM ics_input cin
			    JOIN ics_item cit
			    ON cit.id = cin.input_item_id
			    JOIN ics_task ct
			     ON ct.id = cit.creating_task_id
			    JOIN descendants d on d.child_task_id = cin.task_id
			    WHERE ct.is_trashed = false
			    )
			SELECT distinct child_task_id
			 FROM descendants
			 WHERE child_task_id <> %s""", [str(self.id), str(self.id)])


	def ancestors(self):
		return Task.objects.filter(id__in=self.ancestors_raw_query())

class TaskFile(models.Model):
	url = models.CharField(max_length=150, unique=True)
	name = models.CharField(max_length=100)
	extension = models.CharField(max_length=10, null=True)
	task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="files")

class ActiveItemsManager(models.Manager):
	def get_queryset(self):
		return super(ActiveItemsManager, self).get_queryset().filter(creating_task__is_trashed=False)

class Item(models.Model):
	item_qr = models.CharField(max_length=100, unique=True)
	creating_task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="items")
	created_at = models.DateTimeField(auto_now_add=True, db_index=True)
	inventory = models.ForeignKey(User, on_delete=models.CASCADE, related_name="items", null=True)
	team_inventory = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="items", null=True)
	readable_qr = models.CharField(max_length=50)

	amount = models.DecimalField(default=-1, max_digits=10, decimal_places=3)
	is_virtual = models.BooleanField(default=False, db_index=True)
	is_generic = models.BooleanField(default=False, db_index=True)

	objects = models.Manager()
	active_objects = ActiveItemsManager()

	def __str__(self):
		return str(self.creating_task) + " - " + self.item_qr[-6:]
	
	def save(self, *args, **kwargs):
		self.readable_qr = self.item_qr[-6:]
		if self.pk is None:
			self.inventory = self.creating_task.process_type.created_by
			self.team_inventory = self.creating_task.process_type.team_created_by
			if self.amount < 0:
				self.amount = self.creating_task.process_type.default_amount

		super(Item, self).save(*args, **kwargs)

class Input(models.Model):
	input_item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="inputs")
	task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="inputs")
	amount = models.DecimalField(null=True, max_digits=10, decimal_places=3)

	def delete(self):
		# if an input's creating task is flagged, decrement the flags on the input's task and it's descendents when it's deleted
		if self.input_item.creating_task.is_flagged or self.input_item.creating_task.num_flagged_ancestors > 0:
			Task.objects.filter(id__in=[self.task.id]).update(num_flagged_ancestors=F('num_flagged_ancestors')-2)
		
		similar_inputs = Input.objects.filter(task=self.task, \
			input_item__creating_task__product_type=self.input_item.creating_task.product_type, \
			input_item__creating_task__process_type=self.input_item.creating_task.process_type)
		task_ings = TaskIngredient.objects.filter(task=self.task, \
			ingredient__product_type=self.input_item.creating_task.product_type, \
			ingredient__process_type=self.input_item.creating_task.process_type)
		task_ings_without_recipe = task_ings.filter(ingredient__recipe=None)
		task_ings_with_recipe = task_ings.exclude(ingredient__recipe=None)
		if similar_inputs.count() <= 1:
			# if the input is the only one left for a taskingredient without a recipe, delete the taskingredient
			if task_ings_without_recipe.count() > 0:
				if task_ings_without_recipe[0].ingredient:
					if not task_ings_without_recipe[0].ingredient.recipe:
						task_ings_without_recipe.delete()
			# if the input is the only one left for a taskingredient with a recipe, reset the actual_amount of the taskingredient to 0
			if task_ings_with_recipe.count > 0:
				task_ings_with_recipe.update(actual_amount=0)
		else:
			# if there are other inputs left for a taskingredient without a recipe, decrement the actual_amount by the removed item's amount
			task_ings_without_recipe.update(actual_amount=F('actual_amount')-self.input_item.amount)

		super(Input, self).delete()

class FormulaAttribute(models.Model):
	attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
	product_type = models.ForeignKey(ProductType, on_delete=models.CASCADE)
	formula = models.TextField()
	comparator = models.CharField(max_length=2)
	is_trashed = models.BooleanField(default=False, db_index=True)




class TaskAttribute(models.Model):
	attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
	task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="attribute_values")
	value = models.CharField(max_length=104, blank=True)
	updated_at = models.DateTimeField(auto_now=True)
	created_at = models.DateTimeField(default=timezone.now)

	def getTaskPredictedAttributes(self):
		return TaskFormulaAttribute.objects.filter(task=self.task)

class TaskFormulaAttribute(models.Model):
	formula_attribute = models.ForeignKey(FormulaAttribute, on_delete=models.CASCADE)
	task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="formula_attributes")
	predicted_value = models.CharField(max_length=50, blank=True)

class FormulaDependency(models.Model):
	formula_attribute = models.ForeignKey(FormulaAttribute, on_delete=models.CASCADE, related_name="ancestors")
	dependency = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="dependencies")
	is_trashed = models.BooleanField(default=False, db_index=True)


##################################
#                                #
#    POLYMER SECOENDARY MODELS   #
#                                #
##################################



class RecommendedInputs(models.Model):
	process_type = models.ForeignKey(ProcessType, on_delete=models.CASCADE)
	recommended_input = models.ForeignKey(ProcessType, on_delete=models.CASCADE, related_name='recommended_input')






class Movement(models.Model):
	# ENUM style statuses
	IN_TRANSIT = "IT"
	RECEIVED = "RC"
	STATUS_CHOICES = ((IN_TRANSIT, "in_transit"), (RECEIVED, "received"))
	
	timestamp = models.DateTimeField(auto_now_add=True)
	group_qr = models.CharField(max_length=50, blank=True)
	origin = models.ForeignKey(User, related_name="deliveries", on_delete=models.CASCADE)
	destination = models.ForeignKey(User, related_name="intakes", on_delete=models.CASCADE, null=True)

	team_origin = models.ForeignKey(Team, related_name="deliveries", on_delete=models.CASCADE)
	team_destination = models.ForeignKey(Team, related_name="intakes", on_delete=models.CASCADE, null=True)

	
	# not in use currently
	status = models.CharField(max_length=2, choices=STATUS_CHOICES, default=IN_TRANSIT)
	intended_destination = models.CharField(max_length=50, blank=True)
	deliverable = models.BooleanField(default=False)
	notes = models.CharField(max_length=100, blank=True)


class Adjustment(models.Model):
	userprofile = models.ForeignKey(UserProfile, related_name='adjustments', on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)
	process_type = models.ForeignKey(ProcessType, related_name='adjustments', on_delete=models.CASCADE)
	product_type = models.ForeignKey(ProductType, null=True, related_name='adjustments', on_delete=models.CASCADE)
	amount = models.DecimalField(default=0, max_digits=10, decimal_places=3)
	explanation = models.CharField(max_length=200, blank=True)



class MovementItem(models.Model):
	item = models.ForeignKey(Item, on_delete=models.CASCADE)
	movement = models.ForeignKey(Movement, on_delete=models.CASCADE, related_name="items")

	def save(self, *args, **kwargs):
		if self.pk is None:
			self.item.inventory = self.movement.destination
			self.item.team_inventory = self.movement.team_destination
			self.item.save()
		super(MovementItem, self).save(*args, **kwargs)






class Goal(models.Model):
	TIMERANGES = (
		('d', 'day'),
		('w', 'week'),
		('m', 'month')
	)

	userprofile = models.ForeignKey(UserProfile, related_name="goals", on_delete=models.CASCADE, default=1)
	process_type = models.ForeignKey(ProcessType, related_name='goals', on_delete=models.CASCADE)
	product_type = models.ForeignKey(ProductType, null=True, related_name='goals', on_delete=models.CASCADE)
	product_types = models.ManyToManyField(ProductType, through='GoalProductType')
	goal = models.DecimalField(default=0, max_digits=10, decimal_places=3)
	timerange = models.CharField(max_length=1, choices=TIMERANGES, default='w', db_index=True)
	rank = models.PositiveSmallIntegerField(default=0)
	is_trashed = models.BooleanField(default=False, db_index=True)
	trashed_time = models.DateTimeField(blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	all_product_types = models.BooleanField(default=False)

	def save(self, *args, **kwargs):
		# create the right rank
		if self.is_trashed:
			self.trashed_time = timezone.now()

		if self.pk is None:
			prev_rank = Goal.objects.filter(
				userprofile=self.userprofile,
				timerange=self.timerange
			).aggregate(Max('rank'))['rank__max']
			if prev_rank is None:
				prev_rank = 0
			self.rank = prev_rank + 1
		super(Goal, self).save(*args, **kwargs)


class GoalProductType(models.Model):
	goal = models.ForeignKey(Goal, related_name="goal_product_types", on_delete=models.CASCADE)
	product_type = models.ForeignKey(ProductType, related_name="goal_product_types", on_delete=models.CASCADE)


class Pin(models.Model):
	userprofile = models.ForeignKey(UserProfile, related_name="pins", on_delete=models.CASCADE, default=1)
	process_type = models.ForeignKey(ProcessType, related_name='pins', on_delete=models.CASCADE)
	product_types = models.ManyToManyField(ProductType)
	is_trashed = models.BooleanField(default=False, db_index=True)
	created_at = models.DateTimeField(auto_now_add=True)
	all_product_types = models.BooleanField(default=False)

##################################
#                                #
#    POLYMER SECOENDARY MODELS   #
#                                #
##################################

class Account(models.Model):
	team = models.ForeignKey(Team, related_name='accounts', on_delete=models.CASCADE)
	name = models.CharField(max_length=200)
	created_at = models.DateTimeField(default=timezone.now, blank=True)

	def __str__(self):
		return self.name

class Contact(models.Model):
	account = models.ForeignKey(Account, related_name='contacts', on_delete=models.CASCADE)
	created_at = models.DateTimeField(default=timezone.now, blank=True)
	name = models.CharField(max_length=200)
	phone_number = models.CharField(max_length=15, null=True)
	email = models.EmailField(max_length=70, null= True)
	shipping_addr = models.CharField(max_length=150, null=True)
	billing_addr = models.CharField(max_length=150, null=True)

	def __str__(self):
		return self.name

class Order(models.Model):
	ORDER_STATUS_TYPES = (
		('o', 'ordered'),
		('p', 'processing'),
		('c', 'complete'),
	)

	ordered_by = models.ForeignKey(Contact, related_name='orders', on_delete=models.CASCADE)
	created_at = models.DateTimeField(default=timezone.now, blank=True)
	status = models.CharField(max_length=1, choices=ORDER_STATUS_TYPES, default='o')



class InventoryUnit(models.Model):
	process = models.ForeignKey(ProcessType, related_name='inventory_units', on_delete=models.CASCADE)
	product = models.ForeignKey(ProductType, related_name='inventory_units', on_delete=models.CASCADE)
	unit_price = models.DecimalField(max_digits=10, decimal_places=2)	
	created_at = models.DateTimeField(default=timezone.now, blank=True)
	price_updated_at = models.DateTimeField(auto_now=True)


class OrderInventoryUnit(models.Model):
	order = models.ForeignKey(Order, related_name='order_inventory_units', on_delete=models.CASCADE)
	inventory_unit = models.ForeignKey(InventoryUnit, related_name='order_inventory_units', on_delete=models.CASCADE)
	amount = models.DecimalField(default=-1, max_digits=10, decimal_places=3)
	amount_description = models.CharField(max_length=100, default="")
	created_at = models.DateTimeField(default=timezone.now, blank=True)

class OrderItem(models.Model):
	order = models.ForeignKey(Order, related_name='order_items', on_delete=models.CASCADE)
	item = models.ForeignKey(Item, related_name='order_items', on_delete=models.CASCADE)
	amount = models.DecimalField(default=-1, max_digits=10, decimal_places=3)
	created_at = models.DateTimeField(default=timezone.now, blank=True)


##################################
#                                #
#    POLYMER ALERTS MODELS   	 #
#                                #
##################################
class Alert(models.Model):

	ALERTS_TYPES = (
		('ig', 'incomplete goals'),
		('cg', 'complete goals'),
		('ai', 'anomolous inputs'),
		('ft', 'recently flagged tasks'),
		('ut', 'recently unflagged tasks'),
	)

	alert_type = models.CharField(max_length=2, choices=ALERTS_TYPES, db_index=True)
	variable_content = models.TextField(null=True)
	userprofile = models.ForeignKey(UserProfile, related_name='alerts', on_delete=models.CASCADE)
	is_displayed = models.BooleanField(default=True, db_index=True)
	created_at = models.DateTimeField(default=timezone.now, blank=True, db_index=True)


##################################
#                                #
#    POLYMER RECIPE MODELS   	   #
#                                #
##################################

class Ingredient(models.Model):
	recipe = models.ForeignKey(Recipe, related_name="ingredients", on_delete=models.CASCADE, null=True)
	product_type = models.ForeignKey(ProductType, on_delete=models.CASCADE)
	process_type = models.ForeignKey(ProcessType, on_delete=models.CASCADE)
	amount = models.DecimalField(default=1, max_digits=10, decimal_places=3)

class TaskIngredient(models.Model):
	scaled_amount = models.DecimalField(default=0, max_digits=10, decimal_places=3)
	actual_amount = models.DecimalField(default=0, max_digits=10, decimal_places=3)
	ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name="task_ingredients")
	task = models.ForeignKey(Task, related_name="task_ingredients", on_delete=models.CASCADE)
