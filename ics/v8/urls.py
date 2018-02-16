from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from ics.v8 import views
from django.contrib.auth import views as auth_views

import oauth2client.contrib.django_util.site as django_util_site


urlpatterns = [
    url(r'^tasks/$', views.TaskList.as_view()),
]


