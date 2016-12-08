from rest_framework import status
from rest_framework.response import Response
from ics.models import *
from ics.serializers import *
from rest_framework import generics
from django.shortcuts import get_object_or_404, render
import django_filters
from rest_framework.filters import OrderingFilter
from rest_framework.views import APIView

class CreateTask(generics.ListCreateAPIView):
  queryset = Task.objects.all()
  serializer_class=BasicTaskSerializer
 
class TaskList(generics.ListCreateAPIView):
  queryset = Task.objects.all()
  serializer_class = NestedTaskSerializer
  filter_fields = ('label', 'is_open',)
  filter_backends = (OrderingFilter,)
  ordering_fields = ('updated_at',)

class TaskDetail(generics.RetrieveUpdateDestroyAPIView):
  queryset = Task.objects.all()
  serializer_class = NestedTaskSerializer
  filter_fields = ('label', 'is_open',)

class CreateInput(generics.ListCreateAPIView):
  queryset = Input.objects.all()
  serializer_class = BasicInputSerializer

class CreateItem(generics.ListCreateAPIView):
  queryset = Item.objects.all()
  serializer_class = BasicItemSerializer

class ItemList(generics.ListAPIView):
  queryset = Item.objects.all()
  serializer_class = NestedItemSerializer
  filter_fields = ('item_qr', 'creating_task')

class ItemDetail(generics.RetrieveUpdateDestroyAPIView):
  queryset = Item.objects.all()
  serializer_class = NestedItemSerializer
  filter_fields = ('item_qr', 'creating_task')

class InputList(generics.ListAPIView):
  queryset = Input.objects.all()
  serializer_class = NestedInputSerializer
  filter_fields = ('task',)

class ProcessList(generics.ListCreateAPIView):
  queryset = ProcessType.objects.all()
  serializer_class = ProcessTypeSerializer

class ProductList(generics.ListCreateAPIView):
  queryset = ProductType.objects.all()
  serializer_class = ProductTypeSerializer





class AttributeList(generics.ListCreateAPIView):
  queryset = Attribute.objects.all()
  serializer_class = AttributeSerializer
  filter_fields = ('process_type',)

class AttributeDetail(generics.RetrieveUpdateDestroyAPIView):
  queryset = Attribute.objects.all()
  serializer_class = AttributeSerializer
  filter_fields = ('process_type',)




class TaskAttributeList(generics.ListCreateAPIView):
  queryset = TaskAttribute.objects.all()
  serializer_class = BasicTaskAttributeSerializer
  filter_fields = ('task',)

class TaskAttributeDetail(generics.RetrieveUpdateDestroyAPIView):
  queryset = TaskAttribute.objects.all()
  serializer_class = NestedTaskAttributeSerializer
  filter_fields = ('task',)




def index(request):
  return HttpResponse("Hello, world. You're at the ics index.")
