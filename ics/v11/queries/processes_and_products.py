from django.contrib.auth.models import User
from django.db.models import F, Q, Count, Case, When, Min, Value, Subquery, OuterRef, Sum, DecimalField
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from ics.models import *
import datetime

def process_search(query_params):
	return filter_results(
		ProcessType.objects.all(), 
		query_params
	).select_related(
		'created_by', 'team_created_by'
	).prefetch_related('attribute_set')

def product_search(query_params):
	return filter_results(
		ProductType.objects.all(), 
		query_params
	).annotate(
		last_used=Max('task__created_at')
	).select_related('created_by')

def filter_results(queryset, query_params):
	queryset = queryset.filter(is_trashed=False)
	team = query_params.get('team', None)
	if team is not None:
		queryset = queryset.filter(team_created_by=team)

	f = query_params.get('filter', None)
	if f is not None:
		queryset = queryset.filter(Q(search=SearchQuery(f)) | Q(name__icontains=f) | Q(code__icontains=f))
	return queryset
