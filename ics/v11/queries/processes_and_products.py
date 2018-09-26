from django.db.models import Q
from django.contrib.postgres.search import SearchQuery
from ics.models import *
from django.db.models import Case, When, Value, IntegerField

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
		queryset = queryset.filter(Q(search=SearchQuery(f)) | Q(name__icontains=f) | Q(code__icontains=f) | Q(tags__name__icontains=f))

	process = query_params.get('process', None)
	if process is not None:
		queryset = queryset.filter(task__process_type=process)

	tags = query_params.get('tags', None)
	suggest_tags = stringToBoolean(query_params.get('suggestTags', None))
	if tags is not None:
		tag_names = tags.strip().split(',')
		if suggest_tags is None or not suggest_tags:
			queryset = queryset.filter(tags__name__in=tag_names)
		else:
			queryset = queryset.annotate(
				suggested=Case(
					When(tags__name__in=tag_names, then=Value(1)),
					default=Value(0),
					output_field=IntegerField()
				),
			).order_by('-suggested')
	return queryset

def stringToBoolean(boolStr):
	if boolStr is None:
		return None
	if boolStr.lower() == 'true':
		return True
	elif boolStr.lower() == 'false':
		return False
	return None
