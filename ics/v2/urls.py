from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from ics.v2 import views
from django.contrib.auth import views as auth_views

import oauth2client.contrib.django_util.site as django_util_site


urlpatterns = [
	url(r'^teams/$', views.TeamList.as_view()),
	url(r'^teams/(?P<pk>[0-9]+)/$', views.TeamGet.as_view()),
  url(r'^teams/create/$', views.TeamCreate.as_view()),

  url(r'^members/$', views.MembersList.as_view()),
]

