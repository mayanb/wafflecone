from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from . import views
from django.contrib.auth import views as auth_views

import oauth2client.contrib.django_util.site as django_util_site


urlpatterns = [

    url(r'^users/$', views.UserList.as_view()),
    url(r'^users/(?P<pk>[0-9]+)/$', views.UserGet.as_view()),
    url(r'^users/create/$', views.UserProfileCreate.as_view()),

    url(r'^teams/$', views.TeamList.as_view()),
    url(r'^teams/(?P<pk>[0-9]+)/$', views.TeamGet.as_view()),
    url(r'^teams/create/$', views.TeamCreate.as_view()),


    url(r'^$', views.index, name='index'),
    

    url(r'^tasks/create/$', views.TaskCreate.as_view(), name='create_task'),
    url(r'^tasks/$', views.TaskList.as_view()),
    url(r'^tasks/(?P<pk>[0-9]+)/$', views.TaskDetail.as_view()),
    url(r'^tasks/edit/(?P<pk>[0-9]+)/$', views.TaskEdit.as_view()),
    url(r'^tasks/search/$', views.TaskSearch.as_view()),

    url(r'^items/create/$', views.CreateItem.as_view()),
    url(r'^items/$', views.ItemList.as_view()),
    url(r'^items/(?P<pk>[0-9]+)/$', views.ItemDetail.as_view()),

    url(r'^inputs/create/$', views.CreateInput.as_view()),
    url(r'^inputs/$', views.InputList.as_view()),
    url(r'^inputs/(?P<pk>[0-9]+)/$', views.InputDetail.as_view()),

    url(r'^processes/$', views.ProcessList.as_view()),
    url(r'^processes/(?P<pk>[0-9]+)/$', views.ProcessDetail.as_view()),
    url(r'^processes/move/(?P<pk>[0-9]+)/$', views.ProcessMoveDetail.as_view()),

    url(r'^products/$', views.ProductList.as_view()),
    url(r'^products/(?P<pk>[0-9]+)/$', views.ProductDetail.as_view()),
    url(r'^products/codes/$', views.ProductCodes.as_view()),

    url(r'^attributes/$', views.AttributeList.as_view()),
    url(r'^attributes/(?P<pk>[0-9]+)/$', views.AttributeDetail.as_view()),

    url(r'^taskAttributes/$', views.TaskAttributeList.as_view()),
    url(r'^taskAttributes/(?P<pk>[0-9]+)/$', views.TaskAttributeDetail.as_view()),

    url(r'^recommendedInputs/$', views.RecommendedInputsList.as_view()),
    url(r'^recommendedInputs/(?P<pk>[0-9]+)/$', views.RecommendedInputsDetail.as_view()),

    url(r'^movements/create/$', views.MovementCreate.as_view()),
    url(r'^movements/$', views.MovementList.as_view()),
    url(r'^movements/(?P<pk>[0-9]+)/$', views.MovementReceive.as_view()),

    url(r'^inventory/$', views.InventoryList.as_view()),
    url(r'^inventory/detail/$', views.InventoryDetail.as_view()),
    url(r'^inventory/detail-test/$', views.InventoryDetailTest2.as_view()), # this is the one in production!!!!

    url(r'^activity/$', views.ActivityList.as_view()),
    url(r'^activity/detail/$', views.ActivityListDetail.as_view()),

    url(r'^potatoes/$', views.activityCSV, name='residence time'),

    url(r'^goals/$', views.GoalListCreate.as_view()),
    url(r'^goals/edit/(?P<pk>[0-9]+)/$', views.GoalRetrieveUpdateDestroy.as_view()),

]

urlpatterns = format_suffix_patterns(urlpatterns)