from __future__ import unicode_literals
from datetime import datetime  
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.contrib.auth.models import User
from django.db import models
from uuid import uuid4

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
    team = models.ForeignKey(Team, related_name='team', on_delete=models.CASCADE, null=True)
    account_type = models.CharField(max_length=1, choices=USERTYPES, default='a')



############################
#                          #
#    POLYMER CORE MODELS   #
#                          #
############################


class ProcessType(models.Model):
    created_by = models.ForeignKey(User, related_name='processes', on_delete=models.CASCADE)
    team_created_by = models.ForeignKey(Team, related_name='processes', on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=20)
    code = models.CharField(max_length=20)
    icon = models.CharField(max_length=50)
    unit = models.CharField(max_length=20, default="container")
    output_desc = models.CharField(max_length=20, default="product")
    x = models.DecimalField(default=0, max_digits=10, decimal_places=3)
    y = models.DecimalField(default=0, max_digits=10, decimal_places=3)
    is_trashed = models.BooleanField(default=False)
    default_amount = models.DecimalField(default=0, max_digits=10, decimal_places=3)
    #default_unit = models.CharField(default="kg", max_length=20)

    def __str__(self):
        return self.name

    def getAllAttributes(self):
        return self.attribute_set.filter(is_trashed=False)

    class Meta:
        ordering = ['x',]






class ProductType(models.Model):
    created_by = models.ForeignKey(User, related_name='products', on_delete=models.CASCADE)
    team_created_by = models.ForeignKey(Team, related_name='products', on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=20)
    code = models.CharField(max_length=20)
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

    def __str__(self):
        return self.name






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
    experiment = models.CharField(max_length=25, blank=True)
    keywords = models.CharField(max_length=200, blank=True)
    search = SearchVectorField(null=True)

    def __str__(self):
        if self.custom_display:
            return self.custom_display
        if self.label_index > 0:
            return "-".join([self.label, str(self.label_index)])
        return self.label

    def save(self, *args, **kwargs):
        self.setLabelAndDisplay()
        self.refreshKeywords()
        qr_code = "plmr.io/" + str(uuid4())
        newVirtualItem = Item(is_virtual=True, creating_task=self, item_qr=qr_code)
        newVirtualItem.save()
        super(Task, self).save(*args, **kwargs)

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
        parent_tasks = Task.objects.filter(items__input__task__in=curr_level_tasks)

        for t in parent_tasks:
            if t.id not in all_ancestors:
                new_level_tasks.add(t)
                all_ancestors.add(t.id)

        if new_level_tasks:
            self.ancestors_helper(all_ancestors, new_level_tasks, depth+1)






class Item(models.Model):
    item_qr = models.CharField(max_length=100, unique=True)
    creating_task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="items")
    created_at = models.DateTimeField(auto_now_add=True)
    inventory = models.ForeignKey(User, on_delete=models.CASCADE, related_name="items", null=True)
    team_inventory = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="items", null=True)

    amount = models.DecimalField(default=-1, max_digits=10, decimal_places=3)
    is_virtual = models.BooleanField(default=False)

    def __str__(self):
        return str(self.creating_task) + " - " + self.item_qr[-6:]
    
    def save(self, *args, **kwargs):
        if self.pk is None:
            self.inventory = self.creating_task.process_type.created_by
            if self.amount < 0:
                self.amount = self.creating_task.process_type.default_amount

        super(Item, self).save(*args, **kwargs)






class Input(models.Model):
    input_item = models.ForeignKey(Item, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="inputs")






class TaskAttribute(models.Model):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="attribute_values")
    value = models.CharField(max_length=50, blank=True)
    updated_at = models.DateTimeField(auto_now=True)





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

    team_origin = models.ForeignKey(Team, related_name="deliveries", on_delete=models.CASCADE, null=True)
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
            self.item.save()
        super(MovementItem, self).save(*args, **kwargs)






class Goal(models.Model):
    process_type = models.ForeignKey(ProcessType, related_name='goals', on_delete=models.CASCADE)
    product_type = models.ForeignKey(ProductType, related_name='goals', on_delete=models.CASCADE)
    goal = models.DecimalField(default=0, max_digits=10, decimal_places=3)
