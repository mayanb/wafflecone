from __future__ import unicode_literals
from datetime import datetime  
from django.db import models

# Create your models here.

class User(models.Model):
  name = models.CharField(max_length=20)

  def __str__(self):
    return self.name


class ProcessType(models.Model):
  name = models.CharField(max_length=20)
  code = models.CharField(max_length=20)
  icon = models.CharField(max_length=50)

  def __str__(self):
    return self.name

class ProductType(models.Model):
  name = models.CharField(max_length=20)
  code = models.CharField(max_length=20)

  def __str__(self):
    return self.name


class Task(models.Model):
  process_type = models.ForeignKey(ProcessType, on_delete=models.CASCADE)
  product_type = models.ForeignKey(ProductType, on_delete=models.CASCADE)
  label = models.CharField(max_length=20)  
  label_index = models.PositiveSmallIntegerField(default=0)
  display = models.CharField(max_length=25, blank=True)
  custom_display = models.CharField(max_length=25, blank=True)
  created_by = models.ForeignKey(User, on_delete=models.CASCADE)
  is_open = models.BooleanField(default=True)

  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    if not self.custom_display:
      return self.display
    else:
      return self.custom_display

  def save(self, *args, **kwargs):
    
    # get the # of tasks with the same name & made on the same date this year
    q = ( 
      Task.objects.filter(label=self.label)
        .filter(created_at__startswith=str(datetime.now().year))
        .order_by('-label_index')
      )

    # tentatively, label_index is the # of items with same name
    self.label_index = len(q)

    # if there are other items with the same name, then actually get the highest label_index 
    # and set our label index to that + 1
    if self.label_index > 0:
      self.label_index = q[0].label_index + 1
      self.display = "-".join([self.label, str(self.label_index)])
    else:
      self.display = self.label
      
    super(Task, self).save(*args, **kwargs)




class Item(models.Model):
  item_qr = models.CharField(max_length=100)
  creating_task = models.ForeignKey(Task, on_delete=models.CASCADE)
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return self.item_qr

class Input(models.Model):
  input_item = models.ForeignKey(Item, on_delete=models.CASCADE)
  task = models.ForeignKey(Task, on_delete=models.CASCADE)

#  def __str__(self):
#    return self.input_item

class Attribute(models.Model):
  process_type = models.ForeignKey(ProcessType, on_delete=models.CASCADE)
  name = models.CharField(max_length=20)
  rank = models.PositiveSmallIntegerField(default=0)

  def __str__(self):
    return self.name

class TaskAttribute(models.Model):
  attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
  task = models.ForeignKey(Task, on_delete=models.CASCADE)
  value = models.CharField(max_length=50, blank=True)
  updated_at = models.DateTimeField(auto_now=True)
