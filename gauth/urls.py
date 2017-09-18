from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [

    #url(r'^$', views.index, name='index'),
    url(r'^create-auth-url/$', views.createAuthURL, name='x'),
    url(r'^create-auth-token/$', views.createAuthToken, name='y'),
    url(r'^create-spreadsheet/$', views.createSpreadsheet, name='z'),


]

urlpatterns = format_suffix_patterns(urlpatterns)