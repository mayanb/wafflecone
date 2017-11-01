from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [

    #url(r'^$', views.index, name='index'),
    url(r'^get-process-coocurrence/$', views.GetProcessCoocurrence),

]

urlpatterns = format_suffix_patterns(urlpatterns)