from rest_framework import status
from rest_framework.response import Response
from django.db import models
from django.db.models import F, Q, Count, Case, When, Min, Value, Subquery, OuterRef, Sum, DecimalField
from django.db.models.functions import Coalesce
from django.contrib.postgres.aggregates.general import ArrayAgg
from ics.models import *
from django.contrib.auth.models import User
from ics.v2.serializers import *
from rest_framework import generics
from django.shortcuts import get_object_or_404, render
import django_filters
from rest_framework.filters import OrderingFilter
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.rest_framework import DjangoFilterBackend
from ics.paginations import *
import datetime
# from datetime import date, datetime, timedelta
from django.http import HttpResponse
import csv

######################
# TEAM-RELATED VIEWS #
######################
# teams/
class TeamList(generics.ListAPIView):
  queryset = Team.objects.all()
  serializer_class = TeamSerializer

# teams/[pk]/
class TeamGet(generics.RetrieveAPIView):
  queryset = Team.objects.all()
  serializer_class = TeamSerializer

# teams/create/
class TeamCreate(generics.CreateAPIView):
  queryset = Team.objects.all()
  serializer_class = TeamSerializer

class MembersList(generics.ListCreateAPIView):
	queryset = UserProfile.objects.all()
	serializer_class = UserProfileCreateSerializer

	def get_queryset(self):
		return UserProfile.objects.filter(team=self.request.query_params.get('team', None))

