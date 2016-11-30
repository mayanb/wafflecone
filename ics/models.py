from __future__ import unicode_literals

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
  label = models.CharField(max_length=200)
  notes = models.CharField(max_length=200)
  created_by = models.ForeignKey(User, on_delete=models.CASCADE)
  is_open = models.BooleanField()
  created_on = models.DateTimeField()
  last_edited = models.DateTimeField()

  def __str__(self):
    return self.label

class Item(models.Model):
  item_qr = models.CharField(max_length=50)
  creating_task = models.ForeignKey(Task, on_delete=models.CASCADE)

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

  def __str__(self):
    return self.name

class TaskAttribute(models.Model):
  attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
  task = models.ForeignKey(Task, on_delete=models.CASCADE)
  value = models.CharField(max_length=50)

  def __str__(self):
    return self.value
