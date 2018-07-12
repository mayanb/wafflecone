# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import csv

from ics.models import *
from graphs.v2.queries import get_output_by_bucket
from django.http import HttpResponse
from requests_oauthlib import OAuth2Session, TokenUpdated
from django.conf import settings
from rest_framework.decorators import api_view
import requests
import datetime
from django.db.models import Q, Count, Min, Sum
from django.db.models.functions import Coalesce
from django.core import serializers
from django.contrib.postgres.search import SearchQuery
import pytz
import inflect
from django.utils import dateparse

#Use simplejson to handle serializing Decimal objects
import simplejson as json

dateformat = "%Y-%m-%d-%H-%M-%S-%f"
readable_dateformat = '%Y-%m-%d'
REFRESH_URL = 'https://accounts.google.com/o/oauth2/token'

# @csrf_exempt
@api_view(['POST'])
def test(request):
  test_param = request.POST.get('test_param')
  print("test Param")
  print(test_param)
  r = requests.post("http://bugs.python.org", data={'number': 12524, 'type': 'issue', 'action': 'show'})
  print("response")
  print(r.status_code, r.reason)
  return HttpResponse(r);


def createAuthURL(request):
  user_id = request.GET.get('user_id')
  user_profile = UserProfile.objects.get(user=user_id)
  oauth = OAuth2Session(settings.GOOGLE_OAUTH2_CLIENT_ID, redirect_uri=settings.GOOGLEAUTH_CALLBACK_DOMAIN, scope=settings.GOOGLEAUTH_SCOPE)
  authorization_url, state = oauth.authorization_url( 'https://accounts.google.com/o/oauth2/auth', access_type="offline", prompt="consent")
  response = HttpResponse(authorization_url, content_type="text/plain")
  return response


# @csrf_exempt
@api_view(['POST'])
def createAuthToken(request):
  auth_response = request.POST.get('auth_response')
  user_id = request.POST.get('user_id')
  oauth = OAuth2Session(settings.GOOGLE_OAUTH2_CLIENT_ID,
    redirect_uri=settings.GOOGLEAUTH_CALLBACK_DOMAIN,
    scope=settings.GOOGLEAUTH_SCOPE)
  token = oauth.fetch_token('https://accounts.google.com/o/oauth2/token',
    authorization_response=auth_response,
    client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET)

  # get information about this google user
  google_user_data = oauth.get('https://www.googleapis.com/plus/v1/people/me')
  google_user = google_user_data.json()
  google_user_email = google_user.get("emails")[0].get("value")
  token['user_id'] = user_id

  # update the userprofile object
  user_profile = UserProfile.objects.get(user=user_id)
  update_userprofile_token(user_profile, token)
  user_profile.gauth_email = google_user_email
  user_profile.save()

  # success response
  response = HttpResponse(json.dumps({"token": token['access_token'], "email": google_user_email}), content_type="text/plain")
  return response;


def update_userprofile_token(user_profile, token):
  user_profile.gauth_access_token = token['access_token']
  user_profile.gauth_refresh_token = token['refresh_token']
  user_profile.expires_in = token['expires_in']
  user_profile.expires_at = token['expires_at']


# @csrf_exempt
@api_view(['POST'])
def clearToken(request):
  user_id = request.POST.get('user_id')
  user_profile = UserProfile.objects.get(user=user_id)
  user_profile.gauth_access_token = ""
  user_profile.gauth_email = ""
  user_profile.save()
  response = HttpResponse(serializers.serialize('json', [user_profile]))
  return response


def create_spreadsheet_response(sheets, spreadsheet_title, user_id):
  user_profile = UserProfile.objects.get(user=user_id)
  token = {
    'access_token': user_profile.gauth_access_token,
    'refresh_token': user_profile.gauth_refresh_token,
    'token_type':  'Bearer',
    'expires_at': user_profile.expires_at,
    'expires_in': user_profile.expires_in
  }
  extra = {
    'client_id': settings.GOOGLE_OAUTH2_CLIENT_ID,
    'client_secret': settings.GOOGLE_OAUTH2_CLIENT_SECRET
  }

  # try to authenticate or refresh the token
  try:
    google = OAuth2Session(
      settings.GOOGLE_OAUTH2_CLIENT_ID,
      token=token,
      auto_refresh_url=REFRESH_URL,
      auto_refresh_kwargs=extra,
      scope=settings.GOOGLEAUTH_SCOPE
    )
    # do a random call to force the oauth2session to try to authenticate
    google_user_data = google.get('https://www.googleapis.com/plus/v1/people/me')
  except TokenUpdated as e:
    update_userprofile_token(user_profile, e.token)
    user_profile.save()

  r1 = google.post('https://sheets.googleapis.com/v4/spreadsheets')
  body = json.loads(r1.content)
  spreadsheetID = body["spreadsheetId"]

  update_body = {
    "requests": [{
      "updateSpreadsheetProperties": {
        "properties": {"title": spreadsheet_title},
        "fields": "title"
      },
    },
      {
        "updateSheetProperties": {
          "properties": {
            "sheetId": 0,
            "title": sheets[0]['title']
          },
          "fields": "title"
        }
      }]
  }

  for sheet in sheets[1:]:
    update_body['requests'].append({
      "addSheet": {
        "properties": {
          "title": sheet['title'],
        }
      },
    })

  sheets_url = 'https://sheets.googleapis.com/v4/spreadsheets/' + spreadsheetID + ':batchUpdate'
  r2 = google.post(sheets_url, json.dumps(update_body))

  values_body = {
    "valueInputOption": "RAW",
    "data": [
    ]
  }

  for sheet in sheets:
    values_body['data'].append(
      {
        "range": sheet['title'] + "!A1",
        "values": sheet['data']
      }
    )

  values_url = 'https://sheets.googleapis.com/v4/spreadsheets/' + spreadsheetID + '/values:batchUpdate'
  r3 = google.post(values_url, json.dumps(values_body))
  return HttpResponse(r3, content_type='application/json')


def create_csv_response(rows):
  response = HttpResponse(content_type='text/csv')
  response['Content-Disposition'] = 'attachment;'
  writer = csv.writer(response)
  for row in rows:
    writer.writerow([unicode(s).encode("utf-8") for s in row])
  return response


# ** single_process_array helper methods **

# Returns dict of {attribute_id: (value, created_at), ...}
def get_task_attributes_dict(task_attributes):
  vals = {}
  for ta in task_attributes:
    ta_id = ta[0]
    vals.setdefault(ta_id, []).append(ta[-2:])
  return vals

def get_formatted_value(value_and_date_created, attr, easy_format, timezone):
  formatted_value = value_and_date_created[0]
  created_at = value_and_date_created[1].astimezone(timezone).strftime(easy_format)
  # Handle Time
  if attr.datatype == constants.TIME_TYPE:
    is_valid = dateparse.parse_datetime(formatted_value)
    if (is_valid):
      formatted_value = is_valid.astimezone(timezone).strftime(easy_format)
  # Handle Yes/No Booleans
  elif attr.datatype == constants.BOOLEAN_TYPE:
    formatted_value = 'Yes' if formatted_value == 'true' else 'No'

  if attr.is_recurrent:
    return '%s [%s]' % (str(formatted_value), created_at)
  else:
    return str(formatted_value)

def single_process_array(process, params):
  dt = datetime.datetime
  if not process or not params['start'] or not params['end'] or not params['team']:
    return [[]]

  startDate = dt.strptime(params['start'], dateformat)
  endDate = dt.strptime(params['end'], dateformat)

  data = [];

  fields = ['id', 'display', 'product type', 'inputs', 'batch size', 'creation date', 'last edited date', 'first use date']
  attrs = Attribute.objects.filter(process_type=process).order_by('is_trashed', 'rank')
  fields = fields + [x.name + ' (Inactive)' if x.is_trashed else x.name for x in attrs]
  data.append(fields)

  product_type_ids = params['products'].split(',')
  queryset = Task.objects.filter(is_trashed=False,
                                 process_type__team_created_by=params['team'], process_type=process,
                                 product_type__in=product_type_ids, created_at__range=(startDate, endDate))


  if 'label' in params:
    label = params['label']
    queryset = queryset.filter(Q(keywords__icontains=label) | Q(search=SearchQuery(label)) | Q(label__istartswith=label) | Q(custom_display__istartswith=label))

  if 'flagged' in params and params['flagged'].lower() == 'true':
    queryset = queryset.filter(is_flagged=True)

  tasks = queryset.annotate(
    inputcount=Count('inputs', distinct=True)).annotate(
    first_use_date=Min('items__inputs__task__created_at'))

  timezone = pytz.timezone(Team.objects.get(pk=params['team']).timezone)
  time_format_type = Team.objects.get(pk=params['team']).time_format
  
  easy_format = '%Y-%m-%d %H:%M'
  if time_format_type == 'n':
    easy_format = '%Y-%m-%d %I:%M %p'

  for t in tasks:
    tid = t.id
    display = str(t)
    product_type = t.product_type.code
    inputs = t.inputcount
    batch_size = t.items.aggregate(amount=Coalesce(Sum('amount'), 0))['amount']
    formatted_batch_size = int(batch_size) if batch_size % 1 == 0 else batch_size
    creation_date = t.created_at.astimezone(timezone).strftime(easy_format)
    last_edited_date = t.updated_at.astimezone(timezone).strftime(easy_format)
    first_use_date = t.first_use_date
    if first_use_date is not None:
      first_use_date = first_use_date.astimezone(timezone).strftime(easy_format)
    results = [tid, display, product_type, inputs, formatted_batch_size, creation_date, last_edited_date, first_use_date]
    task_attributes = TaskAttribute.objects.filter(task=t).order_by('created_at').values_list('attribute__id', 'value', 'created_at')
    values = get_task_attributes_dict(task_attributes)

    for attr in attrs:
      attr_values = values.get(attr.id, [])
      value = ''
      if (attr.is_recurrent):
        value = ', '.join(get_formatted_value(value_and_date_created, attr, easy_format, timezone) for value_and_date_created in attr_values)
      elif len(attr_values) > 0:
        # Values sorted old-to-new due to TaskAttribute.objects.filter(task=t).order_by('created_at').
        value = get_formatted_value(attr_values[-1], attr, easy_format, timezone)

      results = results + [value]
    data.append(results)

  return data


def convert_to_readable_time(time):
  arr = str(time).split('-')
  return '-'.join(arr[0:3])

@api_view(['POST'])
def activity_spreadsheet(request):
  params = dict(request.POST.items())
  processes = ProcessType.objects.filter(id__in=params['processes'].split(','))
  label = processes[0].name if len(processes) == 1 else 'Runs'
  spreadsheet_title = label + " " + convert_to_readable_time(params['start']) + " to " + convert_to_readable_time(
    params['end'])

  def build_sheet(process):
    return {
      'title': process.name,
      'data': single_process_array(process.id, params),
    }
  sheets = map(build_sheet, processes)
  return create_spreadsheet_response(sheets, spreadsheet_title, params['user_id'])

@api_view(['POST'])
def activity_csv(request):
  params = dict(request.POST.items())
  rows = []
  for i, process in enumerate(params['processes'].split(',')):
    process_name = ProcessType.objects.get(pk=process).name
    rows.append(['Process: ' + process_name])
    rows.extend(single_process_array(process, params))

    if (i + 1) < len(params['processes']):
      rows.append(['\n'])

  return create_csv_response(rows)

def get_trends(bucket, start, process_type, product_types):
  end = datetime.date.today() + datetime.timedelta(days=1)
  unit = ProcessType.objects.get(pk=process_type).unit
  p = inflect.engine()
  formatted_unit = p.plural(unit)
  if(p.singular_noun(unit)):
    formatted_unit = unit
  total_amount_str = 'Total Amount (' + formatted_unit + ')'

  rows = [['Time Period', 'Number of Tasks', total_amount_str]]
  rows.extend(map(lambda d: [d['bucket'].strftime('%Y-%m-%d'), d['num_tasks'], d['total_amount']],
             get_output_by_bucket(bucket, start, end, process_type, product_types)))
  return rows

def get_trends_data(process_type, product_types):
  last_year = datetime.date.today() - datetime.timedelta(days=365)
  last_week = datetime.date.today() - datetime.timedelta(days=datetime.date.today().isoweekday()%7)
  first_of_month = datetime.date.today().replace(day=1)
  return [
    {
      'title': 'Produced Each Month',
      'data': get_trends('month', last_year, process_type, product_types)
    },
    {
      'title': 'Produced This Week',
      'data': get_trends('day', last_week, process_type, product_types)
    },
    {
      'title': 'Produced This Month',
      'data': get_trends('day', first_of_month, process_type, product_types)
    },
  ]

@api_view(['POST'])
def trends_spreadsheet(request):
  params = dict(request.POST.items())
  product_types = params['products'] or None
  spreadsheet_title = 'Recent Trends'
  sheets = get_trends_data(params['process'], product_types)
  return create_spreadsheet_response(sheets, spreadsheet_title, params['user_id'])

@api_view(['POST'])
def trends_csv(request):
  params = dict(request.POST.items())
  product_types = params['products'] or None

  csv_data = get_trends_data(params['process'], product_types)
  rows = []
  rows.extend([[csv_data[0]['title']]] + csv_data[0]['data'] + [['\n']])
  rows.extend([[csv_data[1]['title']]] + csv_data[1]['data'] + [['\n']])
  rows.extend([[csv_data[2]['title']]] + csv_data[2]['data'])
  return create_csv_response(rows)


