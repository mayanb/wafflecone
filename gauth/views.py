# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from ics.models import *
from django.http import HttpResponse
from requests_oauthlib import OAuth2Session
from django.conf import settings
from rest_framework.decorators import api_view
import requests

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

  token['user_id'] = user_id
  user_profile = UserProfile.objects.get(user=user_id)
  user_profile.gauth_access_token = token['access_token']
  user_profile.gauth_refresh_token = token['refresh_token']
  user_profile.save()
  response = HttpResponse(token['access_token'], content_type="text/plain")
  return response;

@api_view(['POST'])
def createSpreadsheet(request):
  
  'https://sheets.googleapis.com/v4/spreadsheets'
  token['user_id'] = user_id
  user_profile = UserProfile.objects.get(user=user_id)
  user_profile.gauth_access_token = token['access_token']
  user_profile.gauth_refresh_token = token['refresh_token']
  user_profile.save()
  response = HttpResponse(token['access_token'], content_type="text/plain")
  return response;


def createAuthURL(request):
  user_id = request.GET.get('user_id')
  user_profile = UserProfile.objects.get(user=user_id)
  oauth = OAuth2Session(settings.GOOGLE_OAUTH2_CLIENT_ID, redirect_uri=settings.GOOGLEAUTH_CALLBACK_DOMAIN, scope=settings.GOOGLEAUTH_SCOPE)
  authorization_url, state = oauth.authorization_url( 'https://accounts.google.com/o/oauth2/auth', access_type="offline", prompt="select_account")
  response = HttpResponse(authorization_url, content_type="text/plain")
  return response

def token_saver(token):
  userprofile = UserProfile.objects.get(user=token['user_id'])
  userprofile.gauth_access_token = token['access_token']
  userprofile.gauth_refresh_token = token['refresh_token']
  userprofile.gauth_refresh_token = token['token_type']
  userprofile.gauth_refresh_token = token['expires_in']
  userprofile.gauth_refresh_token = token['expires_at']
  userprofile.save()
