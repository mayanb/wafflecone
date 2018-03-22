import pytz
import datetime
from datetime import datetime
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth, TruncDate
from ics.models import *
import pytz

dateformat = "%Y-%m-%d-%H-%M-%S-%f"

def get_output_by_bucket(bucket, start, end, process_type, product_types):
	tz = pytz.timezone('America/Los_Angeles')
	startDate = get_date_from_string(start)
	endDate = get_date_from_string(end)

	bucketFilter = None
	if bucket == 'month':
		bucketFilter = TruncMonth('created_at', tzinfo=tz)
	elif bucket == 'day':
		bucketFilter = TruncDate('created_at', tzinfo=tz)

	t = filter_tasks(
		daterange=(startDate, endDate), 
		process_type=process_type, 
		product_types=product_types
	)

	return t.annotate(
		bucket=bucketFilter
	).values('bucket').annotate(
		total_amount=Sum('items__amount')
	).annotate(
		num_tasks=Count('id', distinct=True)
	).order_by('bucket')

def get_date_from_string(date):
	return pytz.utc.localize(datetime.strptime(date, dateformat))

def filter_tasks(daterange=None, process_type=None, product_types=None):
	t = Task.objects.filter(is_trashed=False)
	if range is not None:
		t = t.filter(created_at__range=daterange)
	if process_type is not None:
		t = t.filter(process_type=process_type)
	if product_types is not None:
		product_types = product_types.split(',')
		t = t.filter(product_type__in=product_types)
	return t


