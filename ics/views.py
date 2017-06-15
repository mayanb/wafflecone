from rest_framework import status
from rest_framework.response import Response
from django.db import models
from django.db.models import F, Q, Count, Case, When, Min, Value, Subquery, OuterRef
from django.contrib.postgres.aggregates.general import ArrayAgg
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
from datetime import date, datetime, timedelta
from django.http import HttpResponse
import csv

######################
# GOAL-RELATED VIEWS #
######################

class GoalListCreate(generics.ListCreateAPIView):
  queryset = Goal.objects.all()
  serializer_class = BasicGoalSerializer

  # def get_queryset(self):
  #   queryset = Goal.objects.all()

  #   team = self.request.query_params.get('team', None)
  #   if team is not None:
  #     queryset = queryset.filter(process_type__created_by=team)

  #   # ok so for each goal
  #   # get all the outputs of that product & process type from this week (just say last 5 days for now)
  #   # sum up all of their amount values

  #   i = Input.objects.filter(task=OuterRef('id')).order_by('id')
  #   queryset = queryset.annotate(input_unit=Subquery(i.values('input_item__creating_task__process_type__unit')[:1]))
  #   return queryset.select_related().prefetch_related('items', 'attribute_values')


  #   today = datetime.today()
  #   i = Item.objects.filter(
  #     creating_task__created_at__date__range=(today, today - 5), 
  #     creating_task__is_trashed=False,
  #     creating_task__process_type=OuterRef('process_type'),
  #     creating_task__product_type=OuterRef('product_type')
  #   ).

  #   queryset.annotate(actual=SubQuery(i.values()))

  #   return queryset


######################
# USER-RELATED VIEWS #
######################

class UserList(generics.ListAPIView):
  queryset = User.objects.all()
  serializer_class = UserSerializer




######################
# TASK-RELATED VIEWS #
######################

class TaskFilter(django_filters.rest_framework.FilterSet):
  created_at = django_filters.DateFilter(name="created_at", lookup_expr="startswith")
  class Meta:
      model = Task
      fields = ['created_at', 'is_open']

# tasks/create/
class TaskCreate(generics.CreateAPIView):
  """
  Create a new task.
  """
  queryset = Task.objects.filter(is_trashed=False)
  serializer_class = BasicTaskSerializer

# tasks/edit/xxx
class TaskEdit(generics.RetrieveUpdateDestroyAPIView):
  queryset = Task.objects.filter(is_trashed=False)
  serializer_class = EditTaskSerializer

class TaskSearch(generics.ListAPIView):
  serializer_class = EditTaskSerializer
  pagination_class = SmallPagination
  filter_backends = (OrderingFilter, DjangoFilterBackend)
  filter_class = TaskFilter
  ordering_fields = ('created_at', 'updated_at')

  def get_queryset(self):
    queryset = Task.objects.filter(is_trashed=False).order_by('-updated_at')

    team = self.request.query_params.get('team', None)
    if team is not None:
      queryset = queryset.filter(process_type__created_by=team)

    label = self.request.query_params.get('label', None)
    dashboard = self.request.query_params.get('dashboard', None)
    if label is not None and dashboard is not None:
      queryset = queryset.filter(Q(keywords__icontains=label))
    elif label is not None:
      queryset = queryset.filter(Q(label__istartswith=label) | Q(custom_display__istartswith=label))

    return queryset


# tasks/
class TaskList(generics.ListAPIView):
  serializer_class = NestedTaskSerializer
  filter_backends = (OrderingFilter, DjangoFilterBackend)
  filter_class = TaskFilter
  ordering_fields = ('updated_at', 'created_at', 'label_index', 'process_type__x')
  #pagination_class = SmallPagination

  def get_queryset(self):
        queryset = Task.objects.filter(is_trashed=False).order_by('process_type__x')

        # filter according to various parameters
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

        # filter according to date creation, based on parameters
        start = self.request.query_params.get('start', None)
        end = self.request.query_params.get('end', None)
        if start is not None and end is not None:
          start = start.strip().split('-')
          end = end.strip().split('-')
          startDate = datetime.date(int(start[0]), int(start[1]), int(start[2]))
          endDate = datetime.date(int(end[0]), int(end[1]), int(end[2]))
          queryset = queryset.filter(created_at__date__range=(startDate, endDate))


        # make sure that we get at least one input unit and return it along with the task
        i = Input.objects.filter(task=OuterRef('id')).order_by('id')
        queryset = queryset.annotate(input_unit=Subquery(i.values('input_item__creating_task__process_type__unit')[:1]))
        return queryset.select_related().prefetch_related('items', 'attribute_values')

  def get_serializer_context(self):
    inv = self.request.query_params.get('inventory', None )
    return {"inventory": inv}

# tasks/xxx/
class TaskDetail(generics.RetrieveAPIView):
  queryset = Task.objects.filter(is_trashed=False)
  serializer_class = NestedTaskSerializer





######################
# ITEM-RELATED VIEWS #
######################

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




#######################
# INPUT-RELATED VIEWS #
#######################

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
  



#########################
# PROCESS-RELATED VIEWS #
#########################

class ProcessList(generics.ListCreateAPIView):
  queryset = ProcessType.objects.filter(is_trashed=False)
  serializer_class = ProcessTypeSerializer
  filter_fields = ('created_by',)

class ProcessDetail(generics.RetrieveUpdateDestroyAPIView):
  queryset = ProcessType.objects.all()
  serializer_class = ProcessTypeSerializer

class ProcessMoveDetail(generics.RetrieveUpdateAPIView):
  queryset = ProcessType.objects.all()
  serializer_class = ProcessTypePositionSerializer




###################
# INVENTORY VIEWS #
###################

class InventoryList(generics.ListAPIView):
  serializer_class = InventoryListSerializer

  def get_queryset(self):
    queryset = Item.objects.filter(input__isnull=True, creating_task__is_trashed=False)

    # filter by team
    team = self.request.query_params.get('team', None)
    if team is not None:
      queryset = queryset.filter(inventory=team)

    # filter by products
    products = self.request.query_params.get('products', None)
    if products is not None:
      products = products.strip().split(',')
      queryset = queryset.filter(creating_task__product_type__code__in=products)

    return queryset.values(
      'creating_task__process_type', 
      'creating_task__process_type__output_desc', 
      'creating_task__process_type__unit', 
      'creating_task__process_type__created_by__username',
      'creating_task__process_type__created_by').annotate(
        count=Count('creating_task__process_type'),
    )


class InventoryDetailTest(generics.ListAPIView):
  serializer_class = InventoryDetailSerializer
  pagination_class = SmallPagination

  def get_queryset(self):
    queryset = Task.objects.filter(is_trashed=False, items__isnull=False, items__input__isnull=True)

    # filter by team
    team = self.request.query_params.get('team', None)
    if team is not None:
      queryset = queryset.filter(items__inventory=team).distinct()

    # filter by products
    products = self.request.query_params.get('products', None)
    if products is not None:
      products = products.strip().split(',')
      queryset = queryset.filter(product_type__code__in=products)

    # filter by output type
    process = self.request.query_params.get('process', '')
    return queryset.filter(process_type=process).annotate(team=Value(team, output_field=models.CharField()))



class InventoryDetail(generics.ListAPIView):
  queryset = Item.objects.filter(creating_task=533)
  serializer_class = NestedItemSerializer
  pagination_class = SmallPagination

  def get_queryset(self):
    queryset = Item.objects.filter(input__isnull=True, creating_task__is_trashed=False)

    # filter by team
    team = self.request.query_params.get('team', None)
    if team is not None:
      queryset = queryset.filter(inventory=team)

    # filter by products
    products = self.request.query_params.get('products', None)
    if products is not None:
      products = products.strip().split(',')
      queryset = queryset.filter(creating_task__product_type__code__in=products)

    # filter by output type
    process = self.request.query_params.get('process', '')
    return queryset.filter(creating_task__process_type=process).order_by('creating_task__created_at')



##################
# ACTIVITY VIEWS #
##################

class ActivityList(generics.ListAPIView):
  serializer_class = ActivityListSerializer

  def get_queryset(self):
    queryset = Task.objects.filter(is_trashed=False)

    team = self.request.query_params.get('team', None)
    if team is not None:
      queryset = queryset.filter(process_type__created_by=team)

    start = self.request.query_params.get('start', None)
    end = self.request.query_params.get('end', None)
    if start is not None and end is not None:
      startDate = datetime.strptime(start, "%Y-%m-%d-%H-%M-%S-%f")
      endDate = datetime.strptime(end, "%Y-%m-%d-%H-%M-%S-%f")
      # startDate = date(int(start[0]), int(start[1]), int(start[2]))
      # endDate = date(int(end[0]), int(end[1]), int(end[2]))
      queryset = queryset.filter(created_at__range=(startDate, endDate))

    # separate by process type
    return queryset.values(
      'process_type',
      'product_type',
      'process_type__name',
      'product_type__code',
      'process_type__unit').annotate(
      runs=Count('id', distinct=True)
    ).annotate(outputs=Count('items', distinct=True))

class ActivityListDetail(generics.ListAPIView):
  serializer_class = ActivityListDetailSerializer

  def get_queryset(self):
    queryset = Task.objects.filter(is_trashed=False)

    team = self.request.query_params.get('team', None)
    if team is not None:
      queryset = queryset.filter(process_type__created_by=team)

    process_type = self.request.query_params.get('process_type', None)
    if process_type is not None:
      queryset = queryset.filter(process_type=process_type)

    product_type = self.request.query_params.get('product_type', None)
    if product_type is not None:
      queryset = queryset.filter(product_type=product_type)


    start = self.request.query_params.get('start', None)
    end = self.request.query_params.get('end', None)
    if start is not None and end is not None:
      startDate = datetime.strptime(start, "%Y-%m-%d-%H-%M-%S-%f")
      endDate = datetime.strptime(end, "%Y-%m-%d-%H-%M-%S-%f")
      # startDate = date(int(start[0]), int(start[1]), int(start[2]))
      # endDate = date(int(end[0]), int(end[1]), int(end[2]))
      queryset = queryset.filter(created_at__range=(startDate, endDate))

    return queryset.annotate(outputs=Count('items'))



#########################
# PRODUCT-RELATED VIEWS #
#########################

class ProductCodes(generics.ListAPIView):
  queryset = ProductType.objects.all().distinct('code')
  serializer_class = ProductCodeSerializer


class ProductList(generics.ListCreateAPIView):
  queryset = ProductType.objects.filter(is_trashed=False)
  serializer_class = ProductTypeSerializer

class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
  queryset = ProductType.objects.all()
  serializer_class = ProductTypeSerializer




###########################
# ATTRIBUTE-RELATED VIEWS #
###########################

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
  #queryset = RecommendedInputs.objects.all()
  serializer_class = RecommendedInputsSerializer

  def get_queryset(self):
    team = self.request.query_params.get('created_by', None)
    if team is not None:
      return RecommendedInputs.objects.filter(process_type__created_by=team).filter(recommended_input__created_by=team)
    return RecommendedInputs.objects.all()

class RecommendedInputsDetail(generics.RetrieveUpdateDestroyAPIView):
  queryset = RecommendedInputs.objects.all()
  serializer_class = RecommendedInputsSerializer

def index(request):
  return HttpResponse("Hello, world. You're at the ics index.")

def potatoes(request):
 # Create the HttpResponse object with the appropriate CSV header.
  response = HttpResponse(content_type='text/csv')
  response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'

  writer = csv.writer(response)
  writer.writerow(['id', 'melanger name', 'origin', 'start time', 'end time', 'time delta'])

  pulled_melangers = Task.objects.filter(is_trashed=False, process_type__created_by=1, process_type__code="MP")
  melanger_attr = Attribute.objects.filter(name__icontains="melanger", process_type__created_by=1, process_type__code="MS")

  for pulled_melanger in pulled_melangers:
    melange_input = pulled_melanger.inputs.first()
    if melange_input:
      melange_start = melange_input.input_item.creating_task
      start_time = melange_start.created_at
      end_time = pulled_melanger.created_at
      delta = end_time - start_time
      origin = pulled_melanger.product_type.code
      melanger_name = melange_start.attribute_values.filter(attribute=melanger_attr)
      if melanger_name.count():
        melanger_name = melanger_name[0].value
      else:
        melanger_name = ""

      writer.writerow([pulled_melanger.id, melanger_name, origin, start_time, end_time, delta])

  return response

def activityCSV(request):
  response = HttpResponse(content_type='text/csv')
  response['Content-Disposition'] = 'attachment; filename="logs.csv"'

  process = request.GET.get('process', None)
  start = request.GET.get('start', None)
  end = request.GET.get('end', None)
  team = request.GET.get('team', None)
  if not process or not start or not end or not team:
    return response

  startDate = datetime.strptime(start, "%Y-%m-%d-%H-%M-%S-%f")
  endDate = datetime.strptime(end, "%Y-%m-%d-%H-%M-%S-%f")
  # start = start.strip().split('-')
  # end = end.strip().split('-')
  # startDate = date(int(start[0]), int(start[1]), int(start[2]))
  # endDate = date(int(end[0]), int(end[1]), int(end[2]))

  fields = ['id', 'display', 'product type', 'inputs', 'outputs', 'creation date', 'close date', 'first use date']
  attrs = Attribute.objects.filter(process_type=process).order_by('rank')
  attrVals = attrs.values_list('name', flat=True)
  fields = fields + [str(x) for x in attrVals]

  writer = csv.writer(response)
  writer.writerow(fields)

  tasks = Task.objects.filter(is_trashed=False, 
    process_type__created_by=team, process_type=process, 
    created_at__date__range=(startDate, endDate)).annotate(
    inputcount=Count('inputs', distinct=True)).annotate(
    outputcount=Count('items', distinct=True)).annotate(
    first_use_date=Min('items__input__task__created_at'))

  for t in tasks:
    tid = t.id
    display = str(t)
    product_type = t.product_type.code
    inputs = t.inputcount
    outputs = t.outputcount
    creation_date = t.created_at
    close_date = t.updated_at
    first_use_date = t.first_use_date
    results = [tid, display, product_type, inputs, outputs, creation_date, close_date, first_use_date]
    vals = dict(TaskAttribute.objects.filter(task=t).values_list('attribute__id', 'value'))
    for attr in attrs:
      results = results + [vals.get(attr.id, '')]
    writer.writerow(results)

  return response

class MovementCreate(generics.CreateAPIView):
  #queryset = Movement.objects.all()
  serializer_class=MovementCreateSerializer

  def get_queryset(self):
    print("Hello")
    print(self.request.stream)
    return Movement.objects.all()


class MovementList(generics.ListAPIView):
  queryset = Movement.objects.all()
  serializer_class=MovementListSerializer
  pagination_class = SmallPagination
  filter_backends = (OrderingFilter, )
  filter_fields=('group_qr', 'destination', 'origin')
  ordering_fields = ('timestamp', )

class MovementReceive(generics.RetrieveUpdateDestroyAPIView):
  queryset = Movement.objects.all()
  serializer_class = MovementReceiveSerializer
