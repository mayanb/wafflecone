from rest_framework import status
from rest_framework.response import Response
from django.db.models import Q
from ics.models import *
from django.contrib.auth.models import User
from ics.serializers import *
from rest_framework import generics
from django.shortcuts import get_object_or_404, render
import django_filters
from rest_framework.filters import OrderingFilter
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from paginations import *
import datetime

class UserList(generics.ListAPIView):
  queryset = User.objects.all()
  serializer_class = UserSerializer


class TaskFilter(django_filters.rest_framework.FilterSet):
  created_at = django_filters.DateFilter(name="created_at", lookup_expr="startswith")
  class Meta:
      model = Task
      fields = ['created_at', 'is_open']

# tasks/create/
class TaskCreate(generics.CreateAPIView):
  queryset = Task.objects.filter(is_trashed=False)
  serializer_class = BasicTaskSerializer

# tasks/edit/xxx
class TaskEdit(generics.RetrieveUpdateDestroyAPIView):
  queryset = Task.objects.filter(is_trashed=False)
  serializer_class = EditTaskSerializer

# tasks/
class TaskList(generics.ListAPIView):
  serializer_class = NestedTaskSerializer
  filter_backends = (OrderingFilter, DjangoFilterBackend)
  filter_class = TaskFilter
  ordering_fields = ('updated_at', 'created_at', 'label_index', 'process_type__x')
  #pagination_class = SmallPagination

  def get_queryset(self):
        queryset = Task.objects.filter(is_trashed=False).order_by('process_type__x')

        team = self.request.query_params.get('team', None)
        if team is not None:
          queryset = queryset.filter(process_type__created_by=team)

        label = self.request.query_params.get('label', None)
        dashboard = self.request.query_params.get('dashboard', None)
        if label is not None and dashboard is not None:
          queryset = queryset.filter(Q(keywords__icontains=label))
        elif label is not None:
          queryset = queryset.filter(Q(label__istartswith=label) | Q(custom_display__istartswith=label))

        parent = self.request.query_params.get('parent', None)
        if parent is not None:
          queryset = Task.objects.get(pk=parent).descendents()

        child = self.request.query_params.get('child', None)
        if child is not None:
            queryset = Task.objects.get(pk=child).ancestors()

        inv = self.request.query_params.get('inventory', None)
        if inv is not None:
          queryset = queryset.filter(items__isnull=False, items__input__isnull=True).distinct()

        processes = self.request.query_params.get('processes', None)
        if processes is not None:
          processes = processes.strip().split(',')
          queryset = queryset.filter(process_type__in=processes)

        products = self.request.query_params.get('products', None)
        if products is not None:
          products = products.strip().split(',')
          queryset = queryset.filter(product_type__in=products)

        start = self.request.query_params.get('start', None)
        end = self.request.query_params.get('end', None)
        if start is not None and end is not None:
          start = start.strip().split('-')
          end = end.strip().split('-')
          startDate = datetime.date(int(start[0]), int(start[1]), int(start[2]))
          endDate = datetime.date(int(end[0]), int(end[1]), int(end[2]))
          queryset = queryset.filter(created_at__date__range=(startDate, endDate))

        return queryset

  def get_serializer_context(self):
    inv = self.request.query_params.get('inventory', None )
    return {"inventory": inv}

# tasks/xxx/
class TaskDetail(generics.RetrieveAPIView):
  queryset = Task.objects.filter(is_trashed=True)
  serializer_class = NestedTaskSerializer


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




class CreateInput(generics.ListCreateAPIView):
  queryset = Input.objects.all()
  serializer_class = BasicInputSerializer

class InputList(generics.ListAPIView):
  queryset = Input.objects.all()
  serializer_class = NestedInputSerializer
  filter_fields = ('task',)

class InputDetail(generics.RetrieveUpdateDestroyAPIView):
  queryset = Input.objects.all()
  serializer_class = NestedInputSerializer
  filter_fields = ('task',)


  

class ProcessList(generics.ListCreateAPIView):
  queryset = ProcessType.objects.all()
  serializer_class = ProcessTypeSerializer

class ProcessDetail(generics.RetrieveUpdateDestroyAPIView):
  queryset = ProcessType.objects.all()
  serializer_class = ProcessTypeSerializer

class ProcessMoveDetail(generics.RetrieveUpdateAPIView):
  queryset = ProcessType.objects.all()
  serializer_class = ProcessTypePositionSerializer




class ProductList(generics.ListCreateAPIView):
  queryset = ProductType.objects.all()
  serializer_class = ProductTypeSerializer

class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
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





class TaskAttributeFilter(django_filters.rest_framework.FilterSet):
    attribute = django_filters.CharFilter(name="attribute__name")

    class Meta:
        model = TaskAttribute
        fields = ['task', 'attribute']

class TaskAttributeList(generics.ListCreateAPIView):
  queryset = TaskAttribute.objects.all()
  serializer_class = BasicTaskAttributeSerializer
  filter_class = TaskAttributeFilter

class TaskAttributeDetail(generics.RetrieveUpdateDestroyAPIView):
  queryset = TaskAttribute.objects.all()
  serializer_class = NestedTaskAttributeSerializer

class RecommendedInputsList(generics.ListCreateAPIView):
  queryset = RecommendedInputs.objects.all()
  serializer_class = RecommendedInputsSerializer

class RecommendedInputsDetail(generics.RetrieveUpdateDestroyAPIView):
  queryset = RecommendedInputs.objects.all()
  serializer_class = RecommendedInputsSerializer

def index(request):
  return HttpResponse("Hello, world. You're at the ics index.")
