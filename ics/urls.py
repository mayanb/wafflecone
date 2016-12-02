from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^tasks/create/$', views.CreateTask.as_view()),
    url(r'^inputs/create/$', views.CreateInput.as_view()),
    url(r'^items/create/$', views.CreateItem.as_view()),

    url(r'^tasks/$', views.TaskList.as_view()),
    url(r'^tasks/(?P<pk>[0-9]+)/$', views.TaskDetail.as_view()),

    url(r'^items/$', views.ItemList.as_view()),
    url(r'^items/(?P<pk>[0-9]+)/$', views.ItemDetail.as_view()),

    url(r'^inputs/$', views.InputList.as_view()),

    url(r'^processes/$', views.ProcessList.as_view()),
    url(r'^products/$', views.ProductList.as_view()),

    url(r'^attributes/$', views.AttributeList.as_view()),
    url(r'^attributes/(?P<pk>[0-9]+)/$', views.AttributeDetail.as_view()),

    url(r'^taskAttributes/$', views.TaskAttributeList.as_view()),
    url(r'^taskAttributes/(?P<pk>[0-9]+)/$', views.TaskAttributeDetail.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)