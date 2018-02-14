import datetime
import pytz
from django.db import models
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from rest_framework.response import Response
from rest_framework.decorators import api_view
from ics.models import *
from graphs.v2.serializers import *

dateformat = "%Y-%m-%d-%H-%M-%S-%f"

mock_data = {
	'process_type': 17,
	'start': '2018-01-01-08-00-00-000000',
	'end': '2018-02-15-08-00-00-000000',
}

@api_view(['GET'])
def production_actuals(request):
	process_type = request.GET.get('process_type', mock_data['process_type'])
	start = request.GET.get('start', mock_data['start'])
	end = request.GET.get('end', mock_data['end'])

	queryset = get_output_by_month(start, end, process_type)
	serializer = ProductionActualsSerializer(queryset, many=True)
	return Response(serializer.data)

def get_output_by_month(start, end, process_type):
	dt = datetime
	tz = pytz.timezone('America/Los_Angeles')
	startDate = dt.strptime(start, dateformat)
	endDate = dt.strptime(end, dateformat)

	return Task.objects.filter(
		is_trashed=False,
		process_type=process_type,
		created_at__range=(startDate, endDate)
	).annotate(
		bucket=TruncMonth('created_at', tzinfo=tz)
	).values('bucket').annotate(
		total_amount=Sum('items__amount')
	).annotate(
		num_tasks=Count('id', distinct=True)
	).order_by('bucket')

	return t