# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import csv

from ics.models import *
from django.http import HttpResponse
from requests_oauthlib import OAuth2Session, TokenUpdated
from django.conf import settings
from rest_framework.decorators import api_view
import requests
import datetime
from django.db.models import Q, Count, Min, Sum
from django.core import serializers
from django.contrib.postgres.search import SearchQuery

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
  return response;

def single_process_array(process, params):
  easy_format = '%Y-%m-%d %H:%M'
  dt = datetime.datetime
  if not process or not params['start'] or not params['end'] or not params['team']:
    return [[]]

  startDate = dt.strptime(params['start'], dateformat)
  endDate = dt.strptime(params['end'], dateformat)

  data = [];

  fields = ['id', 'display', 'product type', 'inputs', 'batch size', 'creation date', 'last edited date', 'first use date']
  attrs = Attribute.objects.filter(process_type=process).order_by('rank')
  attrVals = attrs.values_list('name', flat=True)
  fields = fields + [str(x) for x in attrVals]
  data.append(fields)

  #Backwards compatibility code - can remove later
  if 'products' not in params:
    params['products'] = ','.join(map(lambda p: str(p.id), ProductType.objects.filter(team_created_by=params['team']).all()))
  #End of backwards compatibility code

  product_type_ids = params['products'].split(',')
  queryset = Task.objects.filter(is_trashed=False,
    process_type__team_created_by=params['team'], process_type=process,
    product_type__in=product_type_ids, created_at__range=(startDate, endDate))


  if 'label' in params:
    label = params['label']
    queryset = queryset.filter(Q(search=SearchQuery(label)) | Q(label__istartswith=label) | Q(custom_display__istartswith=label))

  if 'flagged' in params and params['flagged'].lower() == 'true':
    queryset = queryset.filter(is_flagged=True)

  tasks = queryset.annotate(
    inputcount=Count('inputs', distinct=True)).annotate(
    first_use_date=Min('items__inputs__task__created_at'))

  for t in tasks:
    tid = t.id
    display = str(t)
    product_type = t.product_type.code
    inputs = t.inputcount
    batch_size = t.items.aggregate(Sum('amount'))['amount__sum']
    creation_date = t.created_at.strftime(easy_format)
    last_edited_date = t.updated_at.strftime(easy_format)
    first_use_date = t.first_use_date
    if first_use_date is not None:
      first_use_date = first_use_date.strftime(easy_format)
    results = [tid, display, product_type, inputs, batch_size, creation_date, last_edited_date, first_use_date]
    vals = dict(TaskAttribute.objects.filter(task=t).values_list('attribute__id', 'value'))
    for attr in attrs:
      results = results + [vals.get(attr.id, '')]
    # writer.writerow(results)
    data.append(results)

  return data



@api_view(['POST'])
def createSpreadsheet(request):
  params = dict(request.POST.items())
  user_id = request.POST.get('user_id')
  user_profile = UserProfile.objects.get(user=user_id)
  processes = request.POST.get('processes', None)
  start = request.POST.get('start', None)
  end = request.POST.get('end', None)
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

  #Backwards compatibility code - can remove later
  if 'process' in params and not processes:
	  processes = params['process']
	  params['processes'] = processes
  #End of backwards compatibility code


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

  # get the spreadsheet data
  label = str(ProcessType.objects.get(pk=processes[0]).name) if len(processes) == 1 else 'Runs'
  title = label + " " + convert_to_readable_time(start) + " to " + convert_to_readable_time(end)

  # post the spreadsheet to google & return happily
  r = post_spreadsheet(google, title, params)
  return HttpResponse(r, content_type='application/json')


def post_spreadsheet(google, title, params):
  r1 = google.post('https://sheets.googleapis.com/v4/spreadsheets')
  body = json.loads(r1.content)
  spreadsheetID = body["spreadsheetId"]

  processes = ProcessType.objects.filter(id__in=params['processes'].split(','))

  update_body = {
    "requests": [{
      "updateSpreadsheetProperties": {
        "properties": {"title": title},
        "fields": "title"
      },
    },
      {
        "updateSheetProperties": {
          "properties": {
            "sheetId": 0,
            "title": processes[0].name
          },
          "fields": "title"
        }
      }]
  }

  for process in processes[1:]:
    update_body['requests'].append({
      "addSheet": {
        "properties": {
          "title": process.name,
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

  for process in processes:
    values_body['data'].append(
      {
        "range": process.name + "!A1",
        "values": single_process_array(process.id, params)
      }
    )

  values_url = 'https://sheets.googleapis.com/v4/spreadsheets/' + spreadsheetID + '/values:batchUpdate'
  r3 = google.post(values_url, json.dumps(values_body))
  return r3


@api_view(['POST'])
def create_csv_spreadsheet(request):
  params = dict(request.POST.items())

  #Backwards compatibility code - can remove later
  if 'process' in params and 'processes' not in params:
    params['processes'] = params['process']
  #End of backwards compatibility code

  response = HttpResponse(content_type='text/csv')
  response['Content-Disposition'] = 'attachment;'
  writer = csv.writer(response)

  for i, process in enumerate(params['processes'].split(',')):
    process_name = ProcessType.objects.get(pk=process).name
    writer.writerow(['Process: ' + process_name])
    data = single_process_array(process, params)
    for row in data:
      writer.writerow([unicode(s).encode("utf-8") for s in row])

    if (i + 1) < len(params['processes']):
      writer.writerow(['\n'])

  return response


def convert_to_readable_time(time):
  arr = str(time).split('-')
  return '-'.join(arr[0:3])

