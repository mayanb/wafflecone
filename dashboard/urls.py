from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^[a-z]+/$', views.index, name='index'),
]

urlpatterns = format_suffix_patterns(urlpatterns)