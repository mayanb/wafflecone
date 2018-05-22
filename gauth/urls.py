from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [

    #url(r'^$', views.index, name='index'),
    url(r'^create-auth-url/$', views.createAuthURL, name='x'),
    url(r'^create-auth-token/$', views.createAuthToken, name='y'),
    url(r'^create-spreadsheet/$', views.activity_spreadsheet, name='z'),
    #url(r'^token-saver/$', views.token_saver, name='a'),
    url(r'^clear-token/$', views.clearToken, name='b'),
    #url(r'^send-email/$', views.sendEmail),
    url(r'^test/$', views.test),

    url(r'^create-csv/$', views.activity_csv, name='a'),

    url(r'^trends-spreadsheet/$', views.trends_spreadsheet, name='trends_spreadsheet'),
    url(r'^trends-csv/$', views.trends_csv, name='trends_csv'),




]

urlpatterns = format_suffix_patterns(urlpatterns)