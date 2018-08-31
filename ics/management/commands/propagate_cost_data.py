from django.contrib.postgres.aggregates import ArrayAgg
from django.core.management.base import BaseCommand
from django.db.models import Count, Sum, F
from ics.models import *
from django.db.models.functions import Coalesce
from datetime import datetime, timedelta, date


class Command(BaseCommand):
    help = 'Propagates data to tasks'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('team_name', nargs='+', type=str)
        parser.add_argument('days_ago', nargs='+', type=int)

    def handle(self, *args, **options):
        team_id = 24
        days_ago = 100
        if options['team_name']:
          team_name = options['team_name'][0]
          team_id = Team.objects.filter(name=team_name)[0].id
        if options['days_ago']:
          days_ago = options['days_ago'][0]

        print("Propagating costs for team: " + team_name + " (id=" + str(team_id) + ") for trees that began in the last " + str(days_ago) + " days.")
        # To reset before re-seeding:
        Task.objects.filter(process_type__team_created_by__id=team_id).update(cost=0.000, remaining_worth=0.000)
        Task.objects.filter(process_type__team_created_by__id=team_id, cost_set_by_user__isnull=False) \
            .update(cost=F('cost_set_by_user'), remaining_worth=F('cost_set_by_user'))
        print(top_sort(team_id, days_ago))


def make_unique(myList):
  newList = []
  for item in myList:
    if item not in newList:
      newList.append(item)
  return newList


def top_sort(team_id, days_ago):
  cachedTaskSizeRemaining = {}
  level = 0
  CUTOFF = 200
  start = datetime.utcnow() - timedelta(days=days_ago)
  possibleNextLevel = set(list(Task.objects.filter(is_trashed=False, process_type__team_created_by__id=team_id, created_at__gte=start).annotate(num_parents=Count(F('inputs__input_item__creating_task__id'))).filter(num_parents__lte=0).values_list('id', flat=True).distinct()))
  nextLevel = set()
  # only propagate the DAG's that don't have cycles
  print("removing graphs with cycles")
  for x in possibleNextLevel:
    if not check_for_cycles(x):
        nextLevel.add(x)
  path = []
  while len(nextLevel) > 0:
    currLevel = nextLevel
    nextLevel = set()
    print("level: " + str(level))
    for node in currLevel:
      if node:
        if node not in path:
          path.append(node)
        else:
          path.remove(node)
          path.append(node)
        matching_task = Task.objects.filter(pk=node).annotate(children_list=ArrayAgg('items__inputs__task__id'))
        if matching_task.count() > 0:
          children = set(matching_task[0].children_list)
        else:
          children = set()
        nextLevel = nextLevel.union(children)
        print("updating costs for children of " + str(node))
        currTask = Task.objects.filter(pk=node).annotate(batch_size=Coalesce(Sum('items__amount'), 0))[0]
        # get the children in order
        childrenInOrder =  Input.objects.filter(task__in=list(children)).order_by('id').values_list('task', flat=True)
        childrenInOrder = make_unique(childrenInOrder)
        print("children: ")
        print(childrenInOrder)
        if currTask.id not in cachedTaskSizeRemaining:
          cachedTaskSizeRemaining[currTask.id] = currTask.batch_size
        currTaskRemainingWorth = currTask.remaining_worth
        for child in childrenInOrder:
          childTaskObj = Task.objects.get(pk=child)
          task_ing = TaskIngredient.objects.filter(task__id=child, ingredient__process_type=currTask.process_type, ingredient__product_type=currTask.product_type)
          if task_ing.count() > 0:
            task_ing = task_ing[0]
            # get the parents of the child that have the same ingredient type as currTask to get the number of matching parent tasks
            matchingParents = set(Input.objects.filter(task__id=child, input_item__creating_task__process_type=currTask.process_type, input_item__creating_task__product_type=currTask.product_type).values_list('input_item__creating_task__id', flat=True))
            amountToGive = task_ing.actual_amount/len(matchingParents)
            amountGiven = min(cachedTaskSizeRemaining[currTask.id], amountToGive)
            # keep track of how much this task actually has left to give
            cachedTaskSizeRemaining[currTask.id] -= amountGiven
            costGiven = 0
            if currTask.batch_size != 0:
              costGiven = (amountGiven/currTask.batch_size)*currTask.cost
            # add to the child's cost and remaining worth
            childTaskObj.cost = childTaskObj.cost + costGiven
            childTaskObj.remaining_worth = childTaskObj.remaining_worth + costGiven
            childTaskObj.save()
            # subtract from the current tasks's remaining worth
            currTask.remaining_worth = currTask.remaining_worth - costGiven
            currTask.save()
    level += 1
    if CUTOFF <= level:
      print("oh-no")
      break
  return(path)


def has_cycle(time, u, low, disc, stackMember, st):
  disc[u] = time
  low[u] = time
  time += 1
  stackMember[u] = True
  st.append(u)
  matching_task = Task.objects.filter(pk=u).annotate(children_list=ArrayAgg('items__inputs__task__id'))
  if matching_task.count() > 0:
    children = list(set(matching_task[0].children_list))
  else:
    children = []
  for v in children:
    if v not in disc:
      disc[v] = -1
    if u not in low:
      low[u] = -1
    if v not in low:
      low[v] = -1
    if u not in disc:
      disc[u] = -1
    if v not in stackMember:
      stackMember[v] = False
    if disc[v] == -1:
      has_cycle(time, v, low, disc, stackMember, st)
      low[u] = min(low[u], low[v])
    elif stackMember[v] == True:
      low[u] = min(low[u], disc[v])
  w = -1
  if low[u] == disc[u]:
    count = 0
    while w != u:
      if count > 0:
        return True
      w = st.pop()
      stackMember[w] = False
      count += 1
  return False


def check_for_cycles(root):
  disc = {}
  low = {}
  stackMember = {}
  st = []
  disc[root] = -1
  return has_cycle(0, root, low, disc, stackMember, st)