from rest_framework.response import Response
from django.db.models.functions import Coalesce
from ics.v9.calculated_fields_serializers import *
from rest_framework import generics
import django_filters
from rest_framework.filters import OrderingFilter
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from ics.paginations import *
from ics.v9.queries.tasks import *
import datetime
from django.http import HttpResponse
import pytz
from django.utils import timezone
from ics import constants


class IsCodeAvailable(generics.ListAPIView):
  queryset = InviteCode.objects.filter(is_used=False)
  serializer_class = InviteCodeSerializer

  def get_queryset(self):
    code = self.request.query_params.get('code', None)
    return InviteCode.objects.filter(is_used=False, invite_code=code)

class InviteCodeList(generics.ListAPIView):
  queryset = InviteCode.objects.all()
  serializer_class = InviteCodeSerializer

class UseCode(generics.ListAPIView):
  queryset = InviteCode.objects.all()
  serializer_class = InviteCodeSerializer

  def get_queryset(self):
    code = self.request.query_params.get('code', None)
    print(code)
    invitecode = InviteCode.objects.filter(invite_code=code, is_used=False)
    print(invitecode)
    if invitecode.count() == 0:
      print("none")
      return InviteCode.objects.none()
    invitecode.update(is_used=True)
    print(InviteCode.objects.filter(invite_code=code))
    return InviteCode.objects.filter(invite_code=code)

class ReorderAttribute(generics.UpdateAPIView):
  queryset = Attribute.objects.all()
  serializer_class = ReorderAttributeSerializer

class ReorderGoal(generics.UpdateAPIView):
  queryset = Goal.objects.filter(is_trashed=False)
  serializer_class = ReorderGoalSerializer

class UserProfileCreate(generics.CreateAPIView):
  queryset = UserProfile.objects.all()
  serializer_class = UserProfileCreateSerializer

class UserChangeUsernamePassword(generics.UpdateAPIView):
  queryset = UserProfile.objects.all()
  serializer_class = UserProfileChangePasswordSerializer

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
  queryset = UserProfile.objects.all()\
    .select_related('team', 'user')
  serializer_class = UserProfileSerializer

class UserProfileEdit(generics.UpdateAPIView):
  queryset = UserProfile.objects.all()
  serializer_class = UserProfileEditSerializer

class UserProfileLastSeenUpdate(generics.UpdateAPIView):
  queryset = UserProfile.objects.all()
  serializer_class = UpdateUserProfileLastSeenSerializer

class UserProfileIncrementWalkthroughUpdate(generics.UpdateAPIView):
  queryset = UserProfile.objects.all()
  serializer_class = IncrementUserProfileWalkthroughSerializer

class UserProfileCompleteWalkthroughUpdate(generics.UpdateAPIView):
  queryset = UserProfile.objects.all()
  serializer_class = CompleteUserProfileWalkthroughSerializer

class UserProfileClearToken(generics.UpdateAPIView):
  queryset = UserProfile.objects.all()
  serializer_class = ClearUserProfileTokenSerializer

######################
# GOAL-RELATED VIEWS #
######################
class GoalList(generics.ListAPIView):
  queryset = Goal.objects.filter(is_trashed=False)
  serializer_class = BasicGoalSerializer

  def get_queryset(self):
    queryset = Goal.objects.filter(is_trashed=False)
    team = self.request.query_params.get('team', None)
    userprofile = self.request.query_params.get('userprofile', None)
    timerange = self.request.query_params.get('timerange', None)

    if team is not None:
      queryset = queryset.filter(process_type__team_created_by=team)
    if userprofile is not None:
      queryset = queryset.filter(userprofile=userprofile)
    if (timerange is not None) and (timerange == 'w' or timerange == 'd' or timerange == 'm'):
      queryset = queryset.filter(timerange=timerange)
    return queryset.select_related('process_type').prefetch_related('product_types')

class GoalGet(generics.RetrieveAPIView):
  queryset = Goal.objects.filter(is_trashed=False)
  serializer_class = BasicGoalSerializer

class GoalCreate(generics.CreateAPIView):
  queryset = Goal.objects.filter(is_trashed=False)
  serializer_class = GoalCreateSerializer

class GoalRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
  queryset = Goal.objects.filter(is_trashed=False)
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

class DeleteTask(generics.UpdateAPIView):
  queryset = Task.objects.filter(is_trashed=False)
  serializer_class = DeleteTaskSerializer


# tasks/search/?label=[str]
class TaskSearch(generics.ListAPIView):
  serializer_class = NestedTaskSerializer
  pagination_class = SmallPagination
  filter_backends = (OrderingFilter, DjangoFilterBackend)
  filter_class = TaskFilter
  ordering_fields = ('created_at', 'updated_at')

  def get_queryset(self):
    return taskSearch(self.request.query_params)

# tasks/simple/
class SimpleTaskSearch(generics.ListAPIView):
  serializer_class = FlatTaskSerializer
  pagination_class = SmallPagination
  filter_backends = (OrderingFilter, DjangoFilterBackend)
  filter_class = TaskFilter
  ordering_fields = ('created_at', 'updated_at')

  def get_queryset(self):
    return simpleTaskSearch(self.request.query_params)


# tasks/
class TaskList(generics.ListAPIView):
  serializer_class = NestedTaskSerializer
  filter_backends = (OrderingFilter, DjangoFilterBackend)
  filter_class = TaskFilter
  ordering_fields = ('updated_at', 'created_at', 'label_index', 'process_type__x')
  #pagination_class = SmallPagination

  def get_queryset(self):
    return tasks(self.request.query_params)

  def get_serializer_context(self):
    inv = self.request.query_params.get('team_inventory', None )
    return {"team_inventory": inv}

# tasks/[pk]/
class TaskDetail(generics.RetrieveAPIView):
  queryset = taskDetail()
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


#########################
# PROCESS-RELATED VIEWS #
#########################

# processes/
class ProcessList(generics.ListCreateAPIView):
  queryset = ProcessType.objects.filter(is_trashed=False)\
    .select_related('created_by', 'team_created_by')\
    .prefetch_related('attribute_set')
  serializer_class = ProcessTypeWithUserSerializer
  filter_fields = ('created_by', 'team_created_by', 'id')

# processes/[pk]/ ...where pk = 'primary key' == 'the id'
class ProcessDetail(generics.RetrieveUpdateDestroyAPIView):
  queryset = ProcessType.objects.all()
  serializer_class = ProcessTypeWithUserSerializer

# processes/move/[pk]
class ProcessMoveDetail(generics.RetrieveUpdateAPIView):
  queryset = ProcessType.objects.all()
  serializer_class = ProcessTypePositionSerializer


# processes/duplicate
class ProcessDuplicate(generics.CreateAPIView):
  serializer_class = ProcessTypeWithUserSerializer

  def post(self, request, *args, **kwargs):
    process_to_duplicate = ProcessType.objects.get(pk=request.data.get('duplicate_id'))
    duplicate_process = ProcessType.objects.create(
      created_by=User.objects.get(id=request.data.get('created_by')),
      team_created_by=Team.objects.get(id=request.data.get('team_created_by')),
      name=request.data.get('name'),
      code=request.data.get('code'),
      icon=request.data.get('icon'),
      output_desc=request.data.get('output_desc'),
      default_amount=request.data.get('default_amount'),
      unit=request.data.get('unit'),
      is_trashed=False,
    )

    for attribute in process_to_duplicate.attribute_set.filter(is_trashed=False):
      attribute.duplicate(duplicate_process)

    serializer = ProcessTypeWithUserSerializer(duplicate_process)
    return Response(data=serializer.data, status=201)


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
  pagination_class = ExtraLargePagination

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
      startDate = dt.strptime(start, constants.DATE_FORMAT)
      endDate = dt.strptime(end, constants.DATE_FORMAT)
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
      startDate = dt.strptime(start, constants.DATE_FORMAT)
      endDate = dt.strptime(end, constants.DATE_FORMAT)
      queryset = queryset.filter(created_at__range=(startDate, endDate))

    return queryset.annotate(outputs=Coalesce(Sum(sum_query), 0))



#########################
# PRODUCT-RELATED VIEWS #
#########################

class ProductCodes(generics.ListAPIView):
  queryset = ProductType.objects.all().distinct('code')
  serializer_class = ProductCodeSerializer


class ProductList(generics.ListCreateAPIView):
  queryset = ProductType.objects.filter(is_trashed=False).annotate(last_used=Max('task__created_at'))\
    .select_related('created_by')
  serializer_class = ProductTypeWithUserSerializer
  filter_fields = ('created_by', 'team_created_by', 'id')

class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
  queryset = ProductType.objects.filter(is_trashed=False)\
    .select_related('created_by')
  serializer_class = ProductTypeWithUserSerializer




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

class TaskAttributeList(generics.ListAPIView):
  queryset = TaskAttribute.objects.all()
  serializer_class = BasicTaskAttributeSerializer
  filter_class = TaskAttributeFilter

class TaskAttributeCreate(generics.CreateAPIView):
  queryset = TaskAttribute.objects.all()
  serializer_class = CreateTaskAttributeSerializer


class TaskAttributeDetail(generics.RetrieveUpdateDestroyAPIView):
  queryset = TaskAttribute.objects.all()
  serializer_class = NestedTaskAttributeSerializer


def index(request):
  return HttpResponse("Hello, world. You're at the ics index.")


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
# ALERTS-RELATED VIEWS #
######################
class GetRecentlyFlaggedTasks(generics.ListAPIView):
  queryset = Task.objects.filter(is_flagged=True)
  serializer_class = NestedTaskSerializer

  def get_queryset(self):
    queryset = Task.objects.filter(is_flagged=True)
    team = self.request.query_params.get('team', None)
    dt = datetime.datetime
    if team is not None:
      queryset = queryset.filter(process_type__team_created_by=team)

    endDate = dt.today() + timedelta(days=1)
    startDate = dt.today() - timedelta(days=2)
    queryset = queryset.filter(flag_update_time__date__range=(startDate, endDate))
    return queryset

class GetRecentlyUnflaggedTasks(generics.ListAPIView):
  queryset = Task.objects.filter(is_flagged=False)
  serializer_class = NestedTaskSerializer

  def get_queryset(self):
    queryset = Task.objects.filter(is_flagged=False)
    team = self.request.query_params.get('team', None)
    dt = datetime.datetime
    if team is not None:
      queryset = queryset.filter(process_type__team_created_by=team)

    endDate = dt.today() + timedelta(days=1)
    startDate = dt.today() - timedelta(days=2)
    queryset = queryset.filter(flag_update_time__date__range=(startDate, endDate))
    return queryset

class GetIncompleteGoals(generics.ListAPIView):
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

    # TODO: for now we are just getting incomplete weekly goals from the last week
    # for the future - make an endpoint that gets the incomplete goals from the last month
    queryset = queryset.filter(timerange='w')

    incomplete_goals = []
    # get the goals that were active during that time period
    # get the goals that are either not trashed and were created before the start time
    # are trashed and were created before the start time and trashed after the end time
    # that were not fulfilled during that time period
    dt = datetime.datetime
    base = dt.utcnow() - timedelta(days=7)

    start = dt.combine(base - timedelta(days=base.weekday()), dt.min.time())
    end = dt.combine(start + timedelta(days=7), dt.min.time())
    for goal in queryset:
      if goal.timerange == 'w':
        start = dt.combine(base - timedelta(days=base.weekday()), dt.min.time())
      elif goal.timerange == 'd':
        start = dt.combine(base, dt.min.time())
      elif goal.timerange == 'm':
        start = dt.combine(base.replace(day=1), dt.min.time())

      start_aware = pytz.utc.localize(start)
      end_aware = pytz.utc.localize(end)

      if goal.created_at <= start_aware:
        if (not goal.is_trashed) or (goal.is_trashed and goal.trashed_time >= end_aware):
          product_types = ProductType.objects.filter(goal_product_types__goal=goal)
          amount = Item.objects.filter(
            creating_task__process_type=goal.process_type,
            creating_task__product_type__in=product_types,
            creating_task__is_trashed=False,
            creating_task__created_at__range=(start_aware, end_aware),
            is_virtual=False,
          ).aggregate(amount_sum=Sum('amount'))['amount_sum']
          if amount < goal.goal:
            incomplete_goals.append(goal.id)
          print amount
    queryset = queryset.filter(pk__in=incomplete_goals)
    return queryset

class GetRecentAnomolousInputs(generics.ListAPIView):
  queryset = Input.objects.filter(task__is_trashed=False, input_item__creating_task__is_trashed=False)
  serializer_class = AlertInputSerializer

  def get_queryset(self):
    queryset = Input.objects.filter(task__is_trashed=False, input_item__creating_task__is_trashed=False)
    team = self.request.query_params.get('team', None)
    dt = datetime.datetime
    if team is not None:
      queryset = queryset.filter(task__process_type__team_created_by=team)

    endDate = dt.today() + timedelta(days=1)
    startDate = dt.today() - timedelta(days=5)
    queryset = queryset.filter(input_item__created_at__date__range=(startDate, endDate))


    # for each input, if any of the items' creating tasks have a different product type from the input task
    queryset = queryset.exclude(Q(input_item__creating_task__product_type__id=F('task__product_type__id')))

    return queryset


class GetCompleteGoals(generics.ListAPIView):
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

    # TODO: for now we are just getting incomplete weekly goals from the last week
    # for the future - make an endpoint that gets the incomplete goals from the last month
    queryset = queryset.filter(timerange='w')

    complete_goals = []
    dt = datetime.datetime
    base = dt.utcnow() - timedelta(days=7)

    start = dt.combine(base - timedelta(days=base.weekday()), dt.min.time())
    end = dt.combine(start + timedelta(days=7), dt.min.time())
    for goal in queryset:
      if goal.timerange == 'w':
        start = dt.combine(base - timedelta(days=base.weekday()), dt.min.time())
      elif goal.timerange == 'd':
        start = dt.combine(base, dt.min.time())
      elif goal.timerange == 'm':
        start = dt.combine(base.replace(day=1), dt.min.time())

      start_aware = pytz.utc.localize(start)
      end_aware = pytz.utc.localize(end)

      if goal.created_at <= start_aware:
        if (not goal.is_trashed) or (goal.is_trashed and goal.trashed_time >= end_aware):
          product_types = ProductType.objects.filter(goal_product_types__goal=goal)
          amount = Item.objects.filter(
            creating_task__process_type=goal.process_type,
            creating_task__product_type__in=product_types,
            creating_task__is_trashed=False,
            creating_task__created_at__range=(start_aware, end_aware),
            is_virtual=False,
          ).aggregate(amount_sum=Sum('amount'))['amount_sum']
          if amount >= goal.goal:
            complete_goals.append(goal.id)
    queryset = queryset.filter(pk__in=complete_goals)
    return queryset


class AlertCreate(generics.CreateAPIView):
  queryset = Alert.objects.all()
  serializer_class = AlertSerializer

class AlertList(generics.ListAPIView):
  queryset = Alert.objects.filter(is_displayed=True)
  serializer_class = AlertSerializer

  def get_queryset(self):
    team = self.request.query_params.get('team', None)
    userprofile = self.request.query_params.get('userprofile', None)
    queryset = Alert.objects.filter(is_displayed=True)
    if team is not None:
      queryset = queryset.filter(userprofile__team=team)
    if userprofile is not None:
      queryset = queryset.filter(userprofile=userprofile)

    dt = datetime.datetime

    endDate = dt.today() + timedelta(days=1)
    startDate = dt.today() - timedelta(days=1)
    queryset = queryset.filter(created_at__date__range=(startDate, endDate))
    queryset = queryset.order_by('alert_type', '-created_at').distinct('alert_type')

    # get the unique alert_type and userprofile entries with the latest created_by
    return queryset

class AlertGet(generics.RetrieveAPIView):
  queryset = Alert.objects.all()
  serializer_class = AlertSerializer

class AlertEdit(generics.UpdateAPIView):
  queryset = Alert.objects.all()
  serializer_class = AlertSerializer

class AlertsMarkAsRead(generics.ListAPIView):
  queryset = Alert.objects.all()
  serializer_class = AlertSerializer

  def get_queryset(self):
    alert_ids = self.request.query_params.get('alert_ids', None)
    alert_ids = alert_ids.split(',')
    queryset = Alert.objects.filter(pk__in=alert_ids)
    queryset.update(is_displayed=False)
    return queryset


###################################
# CALCULATED FIELDS RELATED VIEWS #
###################################


class CreateAdjustment(generics.CreateAPIView):
  queryset = Adjustment.objects.all()
  serializer_class = AdjustmentSerializer


class InventoryList2(generics.ListAPIView):
  pagination_class = SmallPagination
  serializer_class = InventoryList2Serializer

  def get_queryset(self):
    queryset = Item.active_objects

    team = self.request.query_params.get('team', None)
    if team is None:
      raise serializers.ValidationError('Request must include "team" query param')

    # filter by team
    queryset = queryset.filter(team_inventory=team)

    process_types = self.request.query_params.get('process_types', None)
    if process_types is not None:
      process_ids = process_types.strip().split(',')
      queryset = queryset.filter(creating_task__process_type__in=process_ids)

    product_types = self.request.query_params.get('product_types', None)
    if product_types is not None:
      product_ids = product_types.strip().split(',')
      queryset = queryset.filter(creating_task__product_type__in=product_ids)

    return queryset.values(
      'creating_task__process_type',
      'creating_task__process_type__name',
      'creating_task__process_type__unit',
      'creating_task__process_type__code',
      'creating_task__process_type__icon',
      'creating_task__product_type',
      'creating_task__product_type__name',
      'creating_task__product_type__code',
      'team_inventory'
    ).annotate(
      total_amount=Sum('amount'),
    ).order_by('creating_task__process_type__name', 'creating_task__product_type__name')


class AdjustmentHistory(APIView):
  def set_params(self):
    self.team = self.request.query_params.get('team', None)
    if self.team is None:
      raise serializers.ValidationError('Request must include "team" query param')

    self.process_type = self.request.query_params.get('process_type', None)
    if self.process_type is None:
      raise serializers.ValidationError('Request must include "process_type" query param')

    self.product_type = self.request.query_params.get('product_type', None)
    if self.product_type is None:
      raise serializers.ValidationError('Request must include "product_type" query param')

  def get_adjustments(self):
    queryset = Adjustment.objects.filter(process_type=self.process_type, product_type=self.product_type)\
      .order_by('-created_at')
    return queryset.all()

  def get_item_summary(self, start, end):
    data = Item.active_objects.filter(
      creating_task__process_type=self.process_type,
      creating_task__product_type=self.product_type,
      team_inventory=self.team,
      created_at__range=(start, end)
    ) \
      .aggregate(
      created_count=Count('amount'),
      created_amount=Coalesce(Sum('amount'), 0),
      used_count=Coalesce(Sum(
        Case(
          When(inputs__isnull=False, then=1),
          default=0,
          output_field=models.IntegerField()
        )
      ), 0),
      used_amount=Coalesce(Sum(
        Case(
          When(inputs__isnull=False, then=Case(
            When(inputs__amount__isnull=False, then=F('inputs__amount')),
            When(inputs__amount__isnull=True, then=F('amount')),
            default=0,
            output_field=models.IntegerField()
          )
               ),
          default=0,
          output_field=models.IntegerField()
        )
      ), 0),
    )
    return ItemSummarySerializer(data, context={'date': end}).data

  def get(self, request):
    self.set_params()
    adjustments = self.get_adjustments()

    objects = []

    BEGINNING_OF_TIME = timezone.make_aware(datetime.datetime(1, 1, 1), timezone.utc)
    END_OF_TIME = timezone.make_aware(datetime.datetime(3000, 1, 1), timezone.utc)

    end_date = END_OF_TIME

    for adjustment in adjustments:
      objects.append(self.get_item_summary(adjustment.created_at, end_date))
      objects.append(AdjustmentHistorySerializer(adjustment).data)
      end_date = adjustment.created_at

    objects.append(self.get_item_summary(BEGINNING_OF_TIME, end_date))

    return Response(objects)


###################################
# RECIPES RELATED VIEWS #
###################################

class RecipeList(generics.ListCreateAPIView):
  queryset = Recipe.objects.all()
  serializer_class = RecipeSerializer
  filter_fields = ('product_type', 'process_type', 'id')

  def get_queryset(self):
    team = self.request.query_params.get('team', None)
    if team is not None:
      return Recipe.objects.filter(product_type__team_created_by=team)
    return Recipe.objects.all()

class RecipeDetail(generics.RetrieveUpdateDestroyAPIView):
  queryset = Recipe.objects.all()
  serializer_class = RecipeSerializer

class IngredientList(generics.ListCreateAPIView):
  queryset = Ingredient.objects.all()
  serializer_class = IngredientSerializer
  filter_fields = ('product_type', 'process_type', 'id', 'recipe')

  def get_queryset(self):
    team = self.request.query_params.get('team', None)
    if team is not None:
      return Ingredient.objects.filter(product_type__team_created_by=team)
    return Ingredient.objects.all()

class IngredientDetail(generics.RetrieveUpdateDestroyAPIView):
  queryset = Ingredient.objects.all()
  serializer_class = IngredientSerializer

class TaskIngredientList(generics.ListCreateAPIView):
  queryset = TaskIngredient.objects.all()
  serializer_class = TaskIngredientSerializer
  filter_fields = ('task', 'ingredient', 'id')

  def get_queryset(self):
    team = self.request.query_params.get('team', None)
    if team is not None:
      return TaskIngredient.objects.filter(task__product_type__team_created_by=team)
    return TaskIngredient.objects.all()

class TaskIngredientDetail(generics.RetrieveUpdateDestroyAPIView):
  queryset = TaskIngredient.objects.all()
  serializer_class = TaskIngredientSerializer

