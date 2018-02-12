# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
import json

# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from ics.models import *
from django.http import HttpResponse
from requests_oauthlib import OAuth2Session
from django.conf import settings
from rest_framework.decorators import api_view
import requests
import datetime
from django.db.models import F, Q, Count, Case, When, Min, Value, Subquery, OuterRef, Sum, DecimalField
from django.core import serializers
from django.core.mail import send_mail

dateformat = "%Y-%m-%d-%H-%M-%S-%f"

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
  user_profile.gauth_access_token = token['access_token']
  user_profile.gauth_refresh_token = token['refresh_token']
  user_profile.expires_in = token['expires_in']
  user_profile.expires_at = token['expires_at']
  user_profile.gauth_email = google_user_email
  user_profile.save()

  # success response
  response = HttpResponse(json.dumps({"token": token['access_token'], "email": google_user_email}), content_type="text/plain")
  return response;



# @csrf_exempt
@api_view(['POST'])
def clearToken(request):
  # received_json_data = json.loads(request.body.decode("utf-8"))
  user_id = request.POST.get('user_id')
  print(user_id)
  # user_id = received_json_data["user_id"]
  user_profile = UserProfile.objects.get(user=user_id)
  print(user_profile.gauth_email)
  user_profile.gauth_access_token = ""
  user_profile.gauth_email = ""
  # # user_profile.gauth_refresh_token = token['refresh_token']
  # # user_profile.expires_in = ""
  # # user_profile.expires_at = ""
  user_profile.save()
  response = HttpResponse(serializers.serialize('json', [user_profile]))
  return response;

def activityArray(process, start, end, team):
  easy_format = '%Y-%m-%d %H:%M'
  dt = datetime.datetime
  if not process or not start or not end or not team:
    return [[]]

  startDate = dt.strptime(start, dateformat)
  endDate = dt.strptime(end, dateformat)

  data = [];

  fields = ['id', 'display', 'product type', 'inputs', 'outputs', 'creation date', 'close date', 'first use date']
  attrs = Attribute.objects.filter(process_type=process).order_by('rank')
  attrVals = attrs.values_list('name', flat=True)
  fields = fields + [str(x) for x in attrVals]
  data.append(fields)

  # writer = csv.writer(response)
  # writer.writerow(fields)

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
    # writer.writerow(results)
    data.append(results)

  return data



@api_view(['POST'])
def createSpreadsheet(request):
  user_id = request.POST.get('user_id')
  process = request.POST.get('process', None)
  start = request.POST.get('start', None)
  end = request.POST.get('end', None)
  user_profile = UserProfile.objects.get(user=user_id)
  team = user_profile.team.id
  print(team)
  data = activityArray(process, start, end, team)



  token = {}
  # token['access_token'] = 'ya29.GlvIBC1eeMAd_vmPZLLlqY8erwyCvx8kn2qmZChRTSMabPEscXUVsNUZWO2dguIqF6KopAZqZxUYlMVVviEgpYuYGJFFLmP4IkF9zVXNHINo7V8cACFAhWwzU6X-'
  token['access_token'] = user_profile.gauth_access_token
  token['refresh_token'] = user_profile.gauth_refresh_token
  token['token_type'] = 'Bearer'
  # token['expires_in']=3600
  token['expires_in'] = user_profile.expires_in
  token['expires_at'] = user_profile.expires_at
  refresh_url = 'https://accounts.google.com/o/oauth2/token'
  extra = {}
  extra['client_id'] = settings.GOOGLE_OAUTH2_CLIENT_ID
  extra['client_secret'] = settings.GOOGLE_OAUTH2_CLIENT_SECRET
  google = OAuth2Session(settings.GOOGLE_OAUTH2_CLIENT_ID, token=token, auto_refresh_url=refresh_url,
    auto_refresh_kwargs=extra, token_updater=token_saver, scope=settings.GOOGLEAUTH_SCOPE)
  r = google.post('https://sheets.googleapis.com/v4/spreadsheets')
  body = json.loads(r.content)
  spreadsheetID = body["spreadsheetId"]
  startRange = "Sheet1!A1:A1"
  body = {
    "values": data,
  }

  URLAppend = ('https://sheets.googleapis.com/v4/spreadsheets/' + str(spreadsheetID).encode('utf-8') + '/values/' + str(startRange).encode('utf-8') + ':append').encode('utf-8') + '?valueInputOption=RAW'
  r2 = google.post(URLAppend, json.dumps(body))
  body2 = json.loads(r2.content)
  print( "response2: %s" % body2 )

  dt = datetime.datetime
  title = str(ProcessType.objects.get(pk=process).name) + " " + str(start) + " to " + str(end)
  print(title)
  updateTitleBody = {
    "requests": [{
      "updateSpreadsheetProperties": {
          "properties": {"title": title},
          "fields": "title"
        }
    }]
  }
  titleURL = 'https://sheets.googleapis.com/v4/spreadsheets/' + spreadsheetID + ':batchUpdate'
  r3 = google.post(titleURL, json.dumps(updateTitleBody))
  body3 = json.loads(r3.content)
  return HttpResponse(r3, content_type='application/json')


# @csrf_exempt
@api_view(['POST'])
def sendEmail(request):
  userprofile_id = request.POST.get('userprofile')

  userprofile = UserProfile.objects.get(pk=userprofile_id)
  team_name = userprofile.team.name
  email = userprofile.email

  link = "https://dashboard.usepolymer.com/join/" + userprofile_id + "/"

  subject = "You're invited to team " + team_name + " on Polymer!"
  message = ""
  html_message = "You have been invited to join team: <b>" + team_name + '</b> on Polymer. Click the link to accept your invitation and set your username/password. ' + link
  try:
    send_mail(
        subject,
        message,
        'admin@polymerize.co',
        [email],
        fail_silently=False,
        html_message=html_message,
    )
    return HttpResponse("Email sent!")
  except SMTPException:
    return HttpResponse("Failed to send email.")

def createAuthURL(request):
  user_id = request.GET.get('user_id')
  user_profile = UserProfile.objects.get(user=user_id)
  oauth = OAuth2Session(settings.GOOGLE_OAUTH2_CLIENT_ID, redirect_uri=settings.GOOGLEAUTH_CALLBACK_DOMAIN, scope=settings.GOOGLEAUTH_SCOPE)
  authorization_url, state = oauth.authorization_url( 'https://accounts.google.com/o/oauth2/auth', access_type="offline", prompt="consent")
  response = HttpResponse(authorization_url, content_type="text/plain")
  return response

def token_saver(token):
  print("hi")
  userprofile = UserProfile.objects.get(user=token['user_id'])
  userprofile.gauth_access_token = token['access_token']
  userprofile.gauth_refresh_token = token['refresh_token']
  userprofile.gauth_refresh_token = token['token_type']
  userprofile.gauth_refresh_token = token['expires_in']
  userprofile.gauth_refresh_token = token['expires_at']
  userprofile.save()
