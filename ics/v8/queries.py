from django.contrib.auth.models import User
from django.db.models import F, Q, Count, Case, When, Min, Value, Subquery, OuterRef, Sum, DecimalField
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from ics.models import *
import datetime

dateformat = "%Y-%m-%d-%H-%M-%S-%f"

def get_tasks(query_params):
  dt = datetime.datetime
  queryset = Task.objects.filter(is_trashed=False).order_by('process_type__x')

  # filter according to various parameters
  team = query_params.get('team', None)
  if team is not None:
    queryset = queryset.filter(process_type__team_created_by=team)

  label = query_params.get('label', None)
  dashboard = query_params.get('dashboard', None)
  if label is not None and dashboard is not None:
    queryset = queryset.filter(Q(keywords__icontains=label))
  elif label is not None:
    queryset = queryset.filter(Q(label__istartswith=label) | Q(custom_display__istartswith=label))

  parent = query_params.get('parent', None)
  if parent is not None:
    queryset = Task.objects.get(pk=parent).descendents()

  child = query_params.get('child', None)
  if child is not None:
      queryset = Task.objects.get(pk=child).ancestors()

  inv = query_params.get('team_inventory', None)
  if inv is not None:
    queryset = queryset.filter(items__isnull=False, items__inputs__isnull=True).distinct()

  processes = query_params.get('processes', None)
  if processes is not None:
    processes = processes.strip().split(',')
    queryset = queryset.filter(process_type__in=processes)

  products = query_params.get('products', None)
  if products is not None:
    products = products.strip().split(',')
    queryset = queryset.filter(product_type__in=products)

  # filter according to date creation, based on parameters
  start = query_params.get('start', None)
  end = query_params.get('end', None)
  if start is not None and end is not None:
    start = start.strip().split('-')
    end = end.strip().split('-')
    startDate = datetime.date(int(start[0]), int(start[1]), int(start[2]))
    endDate = datetime.date(int(end[0]), int(end[1]), int(end[2]))
    queryset = queryset.filter(created_at__date__range=(startDate, endDate))

  return annotate_with_total_amount(queryset).select_related()


def annotate_with_total_amount(queryset):
  return queryset.annotate(
    total_amount=Sum(Case(
      When(items__is_virtual=True, then=Value(0)),
      default=F('items__amount'),
      output_field=DecimalField()
    ))          
  )
