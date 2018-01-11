from __future__ import unicode_literals
from datetime import datetime  
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.contrib.postgres.aggregates import StringAgg
from django.db.models.signals import post_save, m2m_changed
from django.contrib.postgres.indexes import GinIndex
from django.dispatch import receiver
from uuid import uuid4
from django.db.models import Max
import constants




# AUTH MODELS
class Team(models.Model):
	name = models.CharField(max_length=50, unique=True)

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
	last_seen = models.DateTimeField(default=datetime.now)

	def get_username_display(self):
		print(self.user.username)
		username_pieces = self.user.username.rsplit('_', 1)
		return username_pieces[0]



############################
#                          #
#    POLYMER CORE MODELS   #
#                          #
############################


class ProcessType(models.Model):
	created_by = models.ForeignKey(User, related_name='processes', on_delete=models.CASCADE)
	team_created_by = models.ForeignKey(Team, related_name='processes', on_delete=models.CASCADE)
	name = models.CharField(max_length=20)
	code = models.CharField(max_length=20)
	icon = models.CharField(max_length=50)
	created_at = models.DateTimeField(default=datetime.now, blank=True)

	description = models.CharField(max_length=100, default="")
	output_desc = models.CharField(max_length=20, default="product")
	default_amount = models.DecimalField(default=0, max_digits=10, decimal_places=3)
	unit = models.CharField(max_length=20, default="container")


	x = models.DecimalField(default=0, max_digits=10, decimal_places=3)
	y = models.DecimalField(default=0, max_digits=10, decimal_places=3)

	default_amount = models.DecimalField(default=0, max_digits=10, decimal_places=3)
	is_trashed = models.BooleanField(default=False)

	def __str__(self):
		return self.name

	def getAllAttributes(self):
		return self.attribute_set.filter(is_trashed=False)

	class Meta:
		ordering = ['x',]






class ProductType(models.Model):
	created_by = models.ForeignKey(User, related_name='products', on_delete=models.CASCADE)
	team_created_by = models.ForeignKey(Team, related_name='products', on_delete=models.CASCADE)
	created_at = models.DateTimeField(default=datetime.now, blank=True)
	name = models.CharField(max_length=30)
	code = models.CharField(max_length=20)
	description = models.CharField(max_length=100, default="")
	is_trashed = models.BooleanField(default=False)

	def __str__(self):
		return self.name






class Attribute(models.Model):
	process_type = models.ForeignKey(ProcessType, on_delete=models.CASCADE)
	name = models.CharField(max_length=20)
	rank = models.PositiveSmallIntegerField(default=0)
	is_trashed = models.BooleanField(default=False)
	datatype = models.CharField(
		max_length=4, 
		choices=constants.ATTRIBUTE_DATA_TYPES, 
		default=constants.TEXT_TYPE
	)
	required = models.BooleanField(default=True)

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
				prev_rank = 0
			self.rank = prev_rank + 1
		super(Attribute, self).save(*args, **kwargs)




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
	process_type = models.ForeignKey(ProcessType, on_delete=models.CASCADE, related_name="tasks")
	product_type = models.ForeignKey(ProductType, on_delete=models.CASCADE)
	label = models.CharField(max_length=20, db_index=True)  
	label_index = models.PositiveSmallIntegerField(default=0, db_index=True)
	custom_display = models.CharField(max_length=25, blank=True)
	#created_by = models.ForeignKey(User, on_delete=models.CASCADE)
	is_open = models.BooleanField(default=True)
	is_trashed = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True, db_index=True)
	updated_at = models.DateTimeField(auto_now=True, db_index=True)
	is_flagged = models.BooleanField(default=False)
	flag_update_time = models.DateTimeField(auto_now_add=True)
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
			self.flag_update_time = datetime.now()
		self.old_is_flagged = self.is_flagged
		qr_code = "plmr.io/" + str(uuid4())
		super(Task, self).save(*args, **kwargs)
		if 'update_fields' not in kwargs or 'search' not in kwargs['update_fields']:
			instance = self._meta.default_manager.with_documents().filter(pk=self.pk)[0]
			instance.search = instance.document
			instance.save(update_fields=['search'])
		# if self.pk is None:
		#     newVirtualItem = Item(is_virtual=True, creating_task=self, item_qr=qr_code)
		#     newVirtualItem.save()

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
					.filter(created_at__startswith=str(datetime.now().year))
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

	
	def descendents(self):
		"""
		Finds all the descendent tasks of this task and returns them as a Queryset
		----
		descendents = task.descendents()
		"""
		all_descendents = set([self.id])
		root_tasks = set([self])
		self.descendents_helper(all_descendents, root_tasks, 0)

		# convert set of IDs to Queryset & return
		return Task.objects.filter(id__in=all_descendents)

	def descendents_helper(self, all_descendents, curr_level_tasks, depth):
		"""
		Recursive helper function for descendents(). Recursively travels through the
		graph of trees to update all_descendents to contain the IDs of descendent tasks.
		
		Keyword arguments:
		all_descendents  -- set of already found descendent IDs
		curr_level_tasks -- set of descendent IDs at the current depth of traversal
		depth            -- integer depth of traversal
		----
		(see descendents() for usage)
		"""
		new_level_tasks = set()

		# get all the items that were created by a task in curr_level_tasks
		child_items = Item.objects.filter(creating_task__in=curr_level_tasks)

		# get all the tasks these items were input into
		child_task_rel = Input.objects.filter(input_item__in=child_items).select_related()

		for i in child_task_rel:
			t = i.task
			if t.id not in all_descendents:
				new_level_tasks.add(i.task)
				all_descendents.add(i.task.id)

		if new_level_tasks:
			self.descendents_helper(all_descendents, new_level_tasks, depth+1)


	def ancestors(self):
		"""
		Finds all the ancestor tasks of this task and returns them as a Queryset
		----
		ancestors = task.ancestors()
		"""
		all_ancestors = set([self.id])
		curr_level_tasks = set([self])
		self.ancestors_helper(all_ancestors, curr_level_tasks, 0)

		# convert set of IDs to Queryset & return
		return Task.objects.filter(id__in=all_ancestors)

	def ancestors_helper(self, all_ancestors, curr_level_tasks, depth):
		"""
		Recursive helper function for ancestors(). Recursively travels through the
		graph of trees to update all_ancestors to contain the IDs of ancestor tasks.

		Keyword arguments: 
		all_ancestors    -- set of already found ancestor IDs
		curr_level_tasks -- set of ancestor IDs at the current depth of traversal
		depth            -- integer depth of traversal
		----
		(see ancestors() for usage)
		"""
		new_level_tasks = set()

		# get all tasks where any of its items were used as inputs into a task 
		# that is in curr_level_tasks
		parent_tasks = Task.objects.filter(items__inputs__task__in=curr_level_tasks)

		for t in parent_tasks:
			if t.id not in all_ancestors:
				new_level_tasks.add(t)
				all_ancestors.add(t.id)

		if new_level_tasks:
			self.ancestors_helper(all_ancestors, new_level_tasks, depth+1)

	def getAllPredictedAttributes(self):
		return TaskFormulaAttribute.objects.filter(task=self)


class Item(models.Model):
	item_qr = models.CharField(max_length=100, unique=True)
	creating_task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="items")
	created_at = models.DateTimeField(auto_now_add=True)
	inventory = models.ForeignKey(User, on_delete=models.CASCADE, related_name="items", null=True)
	team_inventory = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="items", null=True)
	readable_qr = models.CharField(max_length=50)

	amount = models.DecimalField(default=-1, max_digits=10, decimal_places=3)
	is_virtual = models.BooleanField(default=False)

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



class FormulaAttribute(models.Model):
	attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
	product_type = models.ForeignKey(ProductType, on_delete=models.CASCADE)
	formula = models.TextField()
	comparator = models.CharField(max_length=2)
	is_trashed = models.BooleanField(default=False)




class TaskAttribute(models.Model):
	attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
	task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="attribute_values")
	value = models.CharField(max_length=50, blank=True)
	updated_at = models.DateTimeField(auto_now=True)


class TaskFormulaAttribute(models.Model):
	formula_attribute = models.ForeignKey(FormulaAttribute, on_delete=models.CASCADE)
	task = models.ForeignKey(Task, on_delete=models.CASCADE)
	predicted_value = models.CharField(max_length=50, blank=True)

class FormulaDependency(models.Model):
	formula_attribute = models.ForeignKey(FormulaAttribute, on_delete=models.CASCADE, related_name="ancestors")
	dependency = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="dependencies")
	is_trashed = models.BooleanField(default=False)


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
	goal = models.DecimalField(default=0, max_digits=10, decimal_places=3)
	timerange = models.CharField(max_length=1, choices=TIMERANGES, default='w')
	rank = models.PositiveSmallIntegerField(default=0)
	is_trashed = models.BooleanField(default=False)
	trashed_time = models.DateTimeField(blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	all_product_types = models.BooleanField(default=False)

	def save(self, *args, **kwargs):
		# create the right rank
		if self.is_trashed:
			self.trashed_time = datetime.now()

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

##################################
#                                #
#    POLYMER SECOENDARY MODELS   #
#                                #
##################################

class Account(models.Model):
	team = models.ForeignKey(Team, related_name='accounts', on_delete=models.CASCADE)
	name = models.CharField(max_length=200)
	created_at = models.DateTimeField(default=datetime.now, blank=True)

	def __str__(self):
		return self.name

class Contact(models.Model):
	account = models.ForeignKey(Account, related_name='contacts', on_delete=models.CASCADE)
	created_at = models.DateTimeField(default=datetime.now, blank=True)
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
	created_at = models.DateTimeField(default=datetime.now, blank=True)
	status = models.CharField(max_length=1, choices=ORDER_STATUS_TYPES, default='o')



class InventoryUnit(models.Model):
	process = models.ForeignKey(ProcessType, related_name='inventory_units', on_delete=models.CASCADE)
	product = models.ForeignKey(ProductType, related_name='inventory_units', on_delete=models.CASCADE)
	unit_price = models.DecimalField(max_digits=10, decimal_places=2)	
	created_at = models.DateTimeField(default=datetime.now, blank=True)
	price_updated_at = models.DateTimeField(auto_now=True)


class OrderInventoryUnit(models.Model):
	order = models.ForeignKey(Order, related_name='order_inventory_units', on_delete=models.CASCADE)
	inventory_unit = models.ForeignKey(InventoryUnit, related_name='order_inventory_units', on_delete=models.CASCADE)
	amount = models.DecimalField(default=-1, max_digits=10, decimal_places=3)
	amount_description = models.CharField(max_length=100, default="")
	created_at = models.DateTimeField(default=datetime.now, blank=True)

class OrderItem(models.Model):
	order = models.ForeignKey(Order, related_name='order_items', on_delete=models.CASCADE)
	item = models.ForeignKey(Item, related_name='order_items', on_delete=models.CASCADE)
	amount = models.DecimalField(default=-1, max_digits=10, decimal_places=3)
	created_at = models.DateTimeField(default=datetime.now, blank=True)


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

	alert_type = models.CharField(max_length=2, choices=ALERTS_TYPES)
	variable_content = models.TextField(null=True)
	userprofile = models.ForeignKey(UserProfile, related_name='alerts', on_delete=models.CASCADE)
	is_displayed = models.BooleanField(default=True)
	created_at = models.DateTimeField(default=datetime.now, blank=True)



