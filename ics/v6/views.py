from rest_framework import status
from rest_framework.response import Response
from django.db import models
from django.db.models import F, Q, Count, Case, When, Min, Value, Subquery, OuterRef, Sum, DecimalField
from django.db.models.functions import Coalesce
from django.contrib.postgres.aggregates.general import ArrayAgg
from ics.models import *
from django.contrib.auth.models import User
from ics.v6.serializers import *
from ics.v6.order_serializers import *
from rest_framework import generics
from django.shortcuts import get_object_or_404, render
import django_filters
from rest_framework.filters import OrderingFilter
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from ics.paginations import *
import datetime
# from datetime import date, datetime, timedelta
from django.http import HttpResponse
import csv

dateformat = "%Y-%m-%d-%H-%M-%S-%f"

class UserProfileCreate(generics.CreateAPIView):
  queryset = UserProfile.objects.all()
  serializer_class = UserProfileCreateSerializer

# userprofiles/
class UserProfileList(generics.ListAPIView):
  queryset = UserProfile.objects.all()
  serializer_class = UserProfileSerializer

  def get_queryset(self):
    team = self.request.query_params.get('team', None)
    if team is not None:
      return UserProfile.objects.filter(team=team)
    return UserProfile.objects.all()

# userprofiles/[pk]/
class UserProfileGet(generics.RetrieveAPIView):
  queryset = UserProfile.objects.all()
  serializer_class = UserProfileSerializer

class UserProfileEdit(generics.UpdateAPIView):
  queryset = UserProfile.objects.all()
  serializer_class = UserProfileEditSerializer

######################
# GOAL-RELATED VIEWS #
######################
class GoalList(generics.ListAPIView):
  queryset = Goal.objects.all()
  serializer_class = BasicGoalSerializer

  def get_queryset(self):
    queryset = Goal.objects.all()
    team = self.request.query_params.get('team', None)
    userprofile = self.request.query_params.get('userprofile', None)
    timerange = self.request.query_params.get('timerange', None)

    if team is not None:
      queryset = queryset.filter(process_type__team_created_by=team)
    if userprofile is not None:
      queryset = queryset.filter(userprofile=userprofile)
    if (timerange is not None) and (timerange == 'w' or timerange == 'd' or timerange == 'm'):
      queryset = queryset.filter(timerange=timerange)
    return queryset

class GoalGet(generics.RetrieveAPIView):
  queryset = Goal.objects.all()
  serializer_class = BasicGoalSerializer
 
class GoalCreate(generics.CreateAPIView):
  queryset = Goal.objects.all()
  serializer_class = GoalCreateSerializer 

class GoalRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
  queryset = Goal.objects.all()
  serializer_class = BasicGoalSerializer

######################
# USER-RELATED VIEWS #
######################

class UserList(generics.ListAPIView):
  queryset = User.objects.all()
  serializer_class = UserSerializer

# users/[pk]/
class UserGet(generics.RetrieveAPIView):
  queryset = User.objects.all()
  serializer_class = UserSerializer

######################
# TEAM-RELATED VIEWS #
######################
# teams/
class TeamList(generics.ListAPIView):
  queryset = Team.objects.all()
  serializer_class = TeamSerializer

  def get_queryset(self):
    queryset = Team.objects.all()
    team = self.request.query_params.get('team_name', None)
    if team is not None:
      queryset = queryset.filter(name=team)
    return queryset

# teams/[pk]/
class TeamGet(generics.RetrieveAPIView):
  queryset = Team.objects.all()
  serializer_class = TeamSerializer

# teams/create/
class TeamCreate(generics.CreateAPIView):
  queryset = Team.objects.all()
  serializer_class = TeamSerializer

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
  queryset = Task.objects.filter(is_trashed=False)
  serializer_class = BasicTaskSerializer

# tasks/edit/[pk]
class TaskEdit(generics.RetrieveUpdateDestroyAPIView):
  queryset = Task.objects.filter(is_trashed=False)
  serializer_class = EditTaskSerializer

class CreateTaskFlow(generics.CreateAPIView):
  queryset = Task.objects.filter(is_trashed=False)
  serializer_class = FlowTaskSerializer


# tasks/search/?label=[str]
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
      queryset = queryset.filter(process_type__team_created_by=team)
      print(team)
    label = self.request.query_params.get('label', None)
    dashboard = self.request.query_params.get('dashboard', None)
    if label is not None and dashboard is not None:
      queryset = queryset.filter(Q(keywords__icontains=label))
    elif label is not None:
      print("hi")
      query = SearchQuery(label)
      # queryset.annotate(rank=SearchRank(F('search'), query)).filter(search=query).order_by('-rank')
      queryset = queryset.filter(Q(search=query) | Q(label__istartswith=label) | Q(custom_display__istartswith=label))
      print(queryset.query)
      # queryset = queryset.filter(Q(label__istartswith=label) | Q(custom_display__istartswith=label) | Q(items__item_qr__icontains=label))

    return queryset


# tasks/
class TaskList(generics.ListAPIView):
  serializer_class = NestedTaskSerializer
  filter_backends = (OrderingFilter, DjangoFilterBackend)
  filter_class = TaskFilter
  ordering_fields = ('updated_at', 'created_at', 'label_index', 'process_type__x')
  #pagination_class = SmallPagination

  def get_queryset(self):
        dt = datetime.datetime
        queryset = Task.objects.filter(is_trashed=False).order_by('process_type__x').annotate(
            total_amount=Sum(Case(
              When(items__is_virtual=True, then=Value(0)),
              default=F('items__amount'),
              output_field=DecimalField()
            ))          
          )

        # filter according to various parameters
        team = self.request.query_params.get('team', None)
        if team is not None:
          queryset = queryset.filter(process_type__team_created_by=team)

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

        inv = self.request.query_params.get('team_inventory', None)
        if inv is not None:
          queryset = queryset.filter(items__isnull=False, items__inputs__isnull=True).distinct()

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
    inv = self.request.query_params.get('team_inventory', None )
    return {"team_inventory": inv}

# tasks/[pk]/
class TaskDetail(generics.RetrieveAPIView):
  queryset = Task.objects.filter(
    is_trashed=False
  ).annotate(
    total_amount=Sum(Case(
      When(items__is_virtual=True, then=Value(0)),
      default=F('items__amount'),
      output_field=DecimalField()
    ))
  )
  
  serializer_class = NestedTaskSerializer





######################
# ITEM-RELATED VIEWS #
######################

#items/create/
class CreateItem(generics.ListCreateAPIView):
  queryset = Item.objects.all()
  serializer_class = BasicItemSerializer

# items/
class ItemList(generics.ListAPIView):
  queryset = Item.objects.all()
  serializer_class = NestedItemSerializer
  filter_fields = ('item_qr', 'creating_task')

# items/[pk]/
class ItemDetail(generics.RetrieveUpdateDestroyAPIView):
  queryset = Item.objects.all()
  serializer_class = NestedItemSerializer
  filter_fields = ('item_qr', 'creating_task')




#######################
# INPUT-RELATED VIEWS #
#######################

# inputs/create/
class CreateInput(generics.ListCreateAPIView):
  queryset = Input.objects.all()
  serializer_class = BasicInputSerializer

# inputs/
class InputList(generics.ListAPIView):
  queryset = Input.objects.all()
  serializer_class = NestedInputSerializer
  filter_fields = ('task',)

# inputs/[pk]/
class InputDetail(generics.RetrieveUpdateDestroyAPIView):
  queryset = Input.objects.all()
  serializer_class = NestedInputSerializer
  filter_fields = ('task',)
  



#########################
# PROCESS-RELATED VIEWS #
#########################

# processes/
class ProcessList(generics.ListCreateAPIView):
  queryset = ProcessType.objects.filter(is_trashed=False)
  serializer_class = ProcessTypeSerializer
  filter_fields = ('created_by', 'team_created_by')

# processes/[pk]/
class ProcessDetail(generics.RetrieveUpdateDestroyAPIView):
  queryset = ProcessType.objects.all()
  serializer_class = ProcessTypeSerializer

# processes/move/[pk]
class ProcessMoveDetail(generics.RetrieveUpdateAPIView):
  queryset = ProcessType.objects.all()
  serializer_class = ProcessTypePositionSerializer




###################
# INVENTORY VIEWS #
###################

# inventory/
class InventoryList(generics.ListAPIView):
  serializer_class = InventoryListSerializer

  def get_queryset(self):
    queryset = Item.objects.filter(inputs__isnull=True, creating_task__is_trashed=False, is_virtual=False).exclude(creating_task__process_type__code__in=['SH','D'])

    # filter by team
    team = self.request.query_params.get('team', None)
    if team is not None:
      queryset = queryset.filter(team_inventory=team)

    # filter by products
    products = self.request.query_params.get('products', None)
    if products is not None:
      products = products.strip().split(',')
      queryset = queryset.filter(creating_task__product_type__code__in=products)

    # filter by process
    processes = self.request.query_params.get('processes', None)
    if processes is not None:
      processes = processes.strip().split(',')
      queryset = queryset.filter(creating_task__process_type__in=processes) 
      return queryset.values(
        'creating_task__process_type__unit').annotate(
          count=Sum('amount')
        ).annotate(oldest=Min('creating_task__created_at'))

    return queryset.values(
      'creating_task__process_type__code',
      'creating_task__process_type__icon',
      'creating_task__process_type', 
      'creating_task__process_type__output_desc', 
      'creating_task__process_type__unit', 
      'creating_task__process_type__team_created_by',
      'creating_task__process_type__team_created_by__name',
      'creating_task__process_type__created_by__username',
      'creating_task__process_type__created_by',).annotate(
        count=Sum('amount'),
      ).annotate(oldest=Min('creating_task__created_at'))

# inventory/detail-test/
class InventoryDetailTest2(generics.ListAPIView):
  serializer_class = InventoryDetailSerializer
  pagination_class = SmallPagination

  def get_queryset(self):
    item_query = Item.objects.filter(inputs__isnull=True)
    
    team = self.request.query_params.get('team', None)
    if team is not None:
      item_query = item_query.filter(team_inventory=team).distinct()


    queryset = Task.objects.filter(is_trashed=False) 

     # filter by products
    products = self.request.query_params.get('products', None)
    if products is not None:
      products = products.strip().split(',')
      queryset = queryset.filter(product_type__code__in=products)

    # filter by output type
    process = self.request.query_params.get('process', '')
    if process is not None:
      queryset = queryset.filter(process_type=process)


    queryset = queryset.filter(items__in=item_query).distinct()

    return queryset.annotate(team=Value(team, output_field=models.CharField()))
    #return queryset.filter(creating_task__process_type=process).values('creating_task').annotate(Value('creating_task'))


    '''
    item_query = Item.objects.filter(input__isnull=True)
    
    team = self.request.query_params.get('team', None)
    if team is not None:
      item_query = item_query.filter(inventory=team).distinct()


    queryset = Task.objects.filter(is_trashed=False) 

     # filter by products
    products = self.request.query_params.get('products', None)
    if products is not None:
      products = products.strip().split(',')
      queryset = queryset.filter(creating_task__product_type__code__in=products)

    # filter by output type
    process = self.request.query_params.get('process', '')
    if process is not None:
      queryset = queryset.filter(process_type=process)


    queryset = queryset.filter(items__in=item_query).distinct()

    return queryset.annotate(team=Value(team, output_field=models.CharField()))
    #return queryset.filter(creating_task__process_type=process).values('creating_task').annotate(Value('creating_task'))
    '''

# inventory/detail/
class InventoryDetail(generics.ListAPIView):
  queryset = Item.objects.filter(creating_task=533)
  serializer_class = NestedItemSerializer
  pagination_class = SmallPagination

  def get_queryset(self):
    queryset = Item.objects.filter(inputs__isnull=True, creating_task__is_trashed=False)

    # filter by team
    team = self.request.query_params.get('team', None)
    if team is not None:
      queryset = queryset.filter(team_inventory=team)

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

# activity/
class ActivityList(generics.ListAPIView):
  serializer_class = ActivityListSerializer

  def get_queryset(self):
    dt = datetime.datetime
    queryset = Task.objects.filter(is_trashed=False)

    team = self.request.query_params.get('team', None)
    if team is not None:
      queryset = queryset.filter(process_type__team_created_by=team)

    start = self.request.query_params.get('start', None)
    end = self.request.query_params.get('end', None)
    if start is not None and end is not None:

      # start = start.strip().split('-')
      # end = end.strip().split('-')
      # startDate = date(int(start[0]), int(start[1]), int(start[2]))
      # endDate = date(int(end[0]), int(end[1]), int(end[2]))
      startDate = dt.strptime(start, dateformat)
      endDate = dt.strptime(end, dateformat)
      queryset = queryset.filter(created_at__range=(startDate, endDate))

    sum_query = Case(
                  When(items__is_virtual=True, then=Value(0)),
                  default=F('items__amount'),
                  output_field=DecimalField()
                )

    # separate by process type
    return queryset.values(
      'process_type',
      'product_type',
      'process_type__name',
      'process_type__code',
      'product_type__code',
      'process_type__unit').annotate(
      runs=Count('id', distinct=True)
    ).annotate(outputs=Coalesce(Sum(sum_query), 0))

# activity/detail/
class ActivityListDetail(generics.ListAPIView):
  serializer_class = ActivityListDetailSerializer

  def get_queryset(self):
    dt = datetime.datetime
    queryset = Task.objects.filter(is_trashed=False)

    team = self.request.query_params.get('team', None)
    if team is not None:
      queryset = queryset.filter(process_type__team_created_by=team)

    process_type = self.request.query_params.get('process_type', None)
    if process_type is not None:
      queryset = queryset.filter(process_type=process_type)

    product_type = self.request.query_params.get('product_type', None)
    if product_type is not None:
      queryset = queryset.filter(product_type=product_type)

    sum_query = Case(
                  When(items__is_virtual=True, then=Value(0)),
                  default=F('items__amount'),
                  output_field=DecimalField()
                )


    start = self.request.query_params.get('start', None)
    end = self.request.query_params.get('end', None)
    if start is not None and end is not None:
      startDate = dt.strptime(start, dateformat)
      endDate = dt.strptime(end, dateformat)
      queryset = queryset.filter(created_at__range=(startDate, endDate))

    return queryset.annotate(outputs=Coalesce(Sum(sum_query), 0))



#########################
# PRODUCT-RELATED VIEWS #
#########################

class ProductCodes(generics.ListAPIView):
  queryset = ProductType.objects.all().distinct('code')
  serializer_class = ProductCodeSerializer


class ProductList(generics.ListCreateAPIView):
  queryset = ProductType.objects.filter(is_trashed=False).annotate(last_used=Max('task__created_at'))
  serializer_class = ProductTypeSerializer
  filter_fields = ('created_by', 'team_created_by')

class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
  queryset = ProductType.objects.filter(is_trashed=False)
  serializer_class = ProductTypeBasicSerializer




###########################
# ATTRIBUTE-RELATED VIEWS #
###########################

class AttributeList(generics.ListCreateAPIView):
  queryset = Attribute.objects.all()
  serializer_class = AttributeSerializer
  filter_fields = ('process_type',)

class AttributeDetail(generics.RetrieveUpdateDestroyAPIView):
  queryset = Attribute.objects.all()
  serializer_class = AttributeDetailSerializer
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
    team = self.request.query_params.get('team_created_by', None)
    if team is not None:
      return RecommendedInputs.objects.filter(process_type__team_created_by=team).filter(recommended_input__team_created_by=team)
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

  pulled_melangers = Task.objects.filter(is_trashed=False, process_type__team_created_by=1, process_type__code="MP")
  melanger_attr = Attribute.objects.filter(name__icontains="melanger", process_type__team_created_by=1, process_type__code="MS")

  for pulled_melanger in pulled_melangers:
    melange_input = pulled_melanger.inputs.first()
    if melange_input:
      melange_start = melange_input.input_item.creating_task
      start_time = melange_start.created_at.strptime(easy_format)
      end_time = pulled_melanger.created_at.strptime(easy_format)
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

  easy_format = '%Y-%m-%d %H:%M'
  dt = datetime.datetime

  process = request.GET.get('process', None)
  start = request.GET.get('start', None)
  end = request.GET.get('end', None)
  team = request.GET.get('team', None)
  if not process or not start or not end or not team:
    return response

  # start = start.strip().split('-')
  # end = end.strip().split('-')
  # startDate = date(int(start[0]), int(start[1]), int(start[2]))
  # endDate = date(int(end[0]), int(end[1]), int(end[2]))
  startDate = dt.strptime(start, dateformat)
  endDate = dt.strptime(end, dateformat)

  fields = ['id', 'display', 'product type', 'inputs', 'outputs', 'creation date', 'close date', 'first use date']
  attrs = Attribute.objects.filter(process_type=process).order_by('rank')
  attrVals = attrs.values_list('name', flat=True)
  fields = fields + [str(x) for x in attrVals]

  writer = csv.writer(response)
  writer.writerow(fields)

  tasks = Task.objects.filter(is_trashed=False, 
    process_type__team_created_by=team, process_type=process, 
    created_at__range=(startDate, endDate)).annotate(
    inputcount=Count('inputs', distinct=True)).annotate(
    outputcount=Count('items', distinct=True)).annotate(
    first_use_date=Min('items__inputs__task__created_at'))

  for t in tasks:
    tid = t.id
    display = str(t)
    product_type = t.product_type.code
    inputs = t.inputcount
    outputs = t.outputcount
    creation_date = t.created_at.strftime(easy_format)
    close_date = t.updated_at.strftime(easy_format)
    first_use_date = t.first_use_date
    if first_use_date is not None:
      first_use_date = first_use_date.strftime(easy_format)
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
  filter_backends = (OrderingFilter, DjangoFilterBackend)
  filter_fields=('group_qr', 'destination', 'origin', 'team_destination', 'team_origin')
  ordering_fields = ('timestamp', )

class MovementReceive(generics.RetrieveUpdateDestroyAPIView):
  queryset = Movement.objects.all()
  serializer_class = MovementReceiveSerializer

  

######################
# ACCOUNT-RELATED VIEWS #
######################
class AccountList(generics.ListAPIView):
  queryset = Account.objects.all()
  serializer_class = AccountDetailSerializer

  def get_queryset(self):
    queryset = Account.objects.all()
    team = self.request.query_params.get('team', None)

    if team is not None:
      queryset = queryset.filter(team=team)
    return queryset

class AccountGet(generics.RetrieveAPIView):
  queryset = Account.objects.all()
  serializer_class = AccountDetailSerializer
 
class AccountCreate(generics.CreateAPIView):
  queryset = Account.objects.all()
  serializer_class = BasicAccountSerializer 

class AccountEdit(generics.RetrieveUpdateDestroyAPIView):
  queryset = Account.objects.all()
  serializer_class = BasicAccountSerializer


######################
# CONTACT-RELATED VIEWS #
######################
class ContactList(generics.ListAPIView):
  queryset = Contact.objects.all()
  serializer_class = BasicContactSerializer

  def get_queryset(self):
    queryset = Contact.objects.all()
    team = self.request.query_params.get('team', None)

    if team is not None:
      queryset = queryset.filter(account__team=team)
    return queryset

class ContactGet(generics.RetrieveAPIView):
  queryset = Contact.objects.all()
  serializer_class = BasicContactSerializer
 
class ContactCreate(generics.CreateAPIView):
  queryset = Contact.objects.all()
  serializer_class = EditContactSerializer

class ContactEdit(generics.RetrieveUpdateDestroyAPIView):
  queryset = Contact.objects.all()
  serializer_class = EditContactSerializer

######################
# ORDER-RELATED VIEWS #
######################
class OrderList(generics.ListAPIView):
  queryset = Order.objects.all()
  serializer_class = BasicOrderSerializer

  def get_queryset(self):
    queryset = Order.objects.all()
    team = self.request.query_params.get('team', None)
    status = self.request.query_params.get('status', None)

    if team is not None:
      queryset = queryset.filter(ordered_by__account__team=team)
    if status is not None:
      queryset = queryset.filter(status=status)
    return queryset

class OrderGet(generics.RetrieveAPIView):
  queryset = Order.objects.all()
  serializer_class = OrderDetailSerializer
 
class OrderCreate(generics.CreateAPIView):
  queryset = Order.objects.all()
  serializer_class = EditOrderSerializer

class OrderEdit(generics.RetrieveUpdateDestroyAPIView):
  queryset = Order.objects.all()
  serializer_class = EditOrderSerializer

######################
# INVENTORYUNIT-RELATED VIEWS #
######################
class InventoryUnitList(generics.ListAPIView):
  queryset = InventoryUnit.objects.all()
  serializer_class = BasicInventoryUnitSerializer

  def get_queryset(self):
    queryset = InventoryUnit.objects.all()
    team = self.request.query_params.get('team', None)

    if team is not None:
      queryset = queryset.filter(process__team_created_by=team)
    return queryset

class InventoryUnitGet(generics.RetrieveAPIView):
  queryset = InventoryUnit.objects.all()
  serializer_class = BasicInventoryUnitSerializer
 
class InventoryUnitCreate(generics.CreateAPIView):
  queryset = InventoryUnit.objects.all()
  serializer_class = EditInventoryUnitSerializer

class InventoryUnitEdit(generics.RetrieveUpdateDestroyAPIView):
  queryset = InventoryUnit.objects.all()
  serializer_class = EditInventoryUnitSerializer

######################
# ORDERINVENTORYUNIT-RELATED VIEWS #
######################
class OrderInventoryUnitList(generics.ListAPIView):
  queryset = OrderInventoryUnit.objects.all()
  serializer_class = BasicOrderInventoryUnitSerializer

  def get_queryset(self):
    queryset = OrderInventoryUnit.objects.all()
    team = self.request.query_params.get('team', None)

    if team is not None:
      queryset = queryset.filter(order__ordered_by__account__team=team)
    return queryset

class OrderInventoryUnitGet(generics.RetrieveAPIView):
  queryset = OrderInventoryUnit.objects.all()
  serializer_class = BasicOrderInventoryUnitSerializer
 
class OrderInventoryUnitCreate(generics.CreateAPIView):
  queryset = OrderInventoryUnit.objects.all()
  serializer_class = EditOrderInventoryUnitSerializer

class OrderInventoryUnitEdit(generics.RetrieveUpdateDestroyAPIView):
  queryset = OrderInventoryUnit.objects.all()
  serializer_class = EditOrderInventoryUnitSerializer


######################
# ORDERITEM-RELATED VIEWS #
######################
class OrderItemList(generics.ListAPIView):
  queryset = OrderItem.objects.all()
  serializer_class = BasicOrderItemSerializer

  def get_queryset(self):
    queryset = OrderItem.objects.all()
    team = self.request.query_params.get('team', None)
    order = self.request.query_params.get('order', None)

    if team is not None:
      queryset = queryset.filter(order__ordered_by__account__team=team)
    if order is not None:
      queryset = queryset.filter(order=order)
    return queryset

class OrderItemGet(generics.RetrieveAPIView):
  queryset = OrderItem.objects.all()
  serializer_class = BasicOrderItemSerializer
 
class OrderItemCreate(generics.CreateAPIView):
  queryset = OrderItem.objects.all()
  serializer_class = EditOrderItemSerializer

class OrderItemEdit(generics.RetrieveUpdateDestroyAPIView):
  queryset = OrderItem.objects.all()
  serializer_class = EditOrderItemSerializer

######################
# PACKING ORDER-RELATED VIEWS #
######################
 
class CreatePackingOrder(generics.CreateAPIView):
  queryset = Order.objects.all()
  serializer_class = CreatePackingOrderSerializer



