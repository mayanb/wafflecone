from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from ics.v6 import views
from django.contrib.auth import views as auth_views

import oauth2client.contrib.django_util.site as django_util_site


urlpatterns = [
    url(r'^users/$', views.UserList.as_view()),
    url(r'^users/(?P<pk>[0-9]+)/$', views.UserGet.as_view()),
    url(r'^userprofiles/$', views.UserProfileList.as_view()),
    url(r'^userprofiles/(?P<pk>[0-9]+)/$', views.UserProfileGet.as_view()),
    url(r'^userprofiles/edit/(?P<pk>[0-9]+)/$', views.UserProfileEdit.as_view()),
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
    url(r'^tasks/flow/$', views.CreateTaskFlow.as_view()),


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
    url(r'^attributes/move/(?P<pk>[0-9]+)/$', views.ReorderAttribute.as_view()),

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

    url(r'^goals/$', views.GoalList.as_view()),
    url(r'^goals/(?P<pk>[0-9]+)/$', views.GoalGet.as_view()),
    url(r'^goals/create/$', views.GoalCreate.as_view()),
    url(r'^goals/edit/(?P<pk>[0-9]+)/$', views.GoalRetrieveUpdateDestroy.as_view()),
    url(r'^goals/move/(?P<pk>[0-9]+)/$', views.ReorderGoal.as_view()),

    url(r'^accounts/$', views.AccountList.as_view()),
    url(r'^accounts/(?P<pk>[0-9]+)/$', views.AccountGet.as_view()),
    url(r'^accounts/create/$', views.AccountCreate.as_view()),
    url(r'^accounts/edit/(?P<pk>[0-9]+)/$', views.AccountEdit.as_view()),

    url(r'^contacts/$', views.ContactList.as_view()),
    url(r'^contacts/(?P<pk>[0-9]+)/$', views.ContactGet.as_view()),
    url(r'^contacts/create/$', views.ContactCreate.as_view()),
    url(r'^contacts/edit/(?P<pk>[0-9]+)/$', views.ContactEdit.as_view()),

    url(r'^orders/$', views.OrderList.as_view()),
    url(r'^orders/(?P<pk>[0-9]+)/$', views.OrderGet.as_view()),
    url(r'^orders/create/$', views.OrderCreate.as_view()),
    url(r'^orders/edit/(?P<pk>[0-9]+)/$', views.OrderEdit.as_view()),

    url(r'^inventoryunits/$', views.InventoryUnitList.as_view()),
    url(r'^inventoryunits/(?P<pk>[0-9]+)/$', views.InventoryUnitGet.as_view()),
    url(r'^inventoryunits/create/$', views.InventoryUnitCreate.as_view()),
    url(r'^inventoryunits/edit/(?P<pk>[0-9]+)/$', views.InventoryUnitEdit.as_view()),

    url(r'^orderinventoryunits/$', views.OrderInventoryUnitList.as_view()),
    url(r'^orderinventoryunits/(?P<pk>[0-9]+)/$', views.OrderInventoryUnitGet.as_view()),
    url(r'^orderinventoryunits/create/$', views.OrderInventoryUnitCreate.as_view()),
    url(r'^orderinventoryunits/edit/(?P<pk>[0-9]+)/$', views.OrderInventoryUnitEdit.as_view()),

    url(r'^orderitems/$', views.OrderItemList.as_view()),
    url(r'^orderitems/(?P<pk>[0-9]+)/$', views.OrderItemGet.as_view()),
    url(r'^orderitems/create/$', views.OrderItemCreate.as_view()),
    url(r'^orderitems/edit/(?P<pk>[0-9]+)/$', views.OrderItemEdit.as_view()),

    url(r'^packingorder/create/$', views.CreatePackingOrder.as_view()),

    url(r'^alerts/recently-flagged-tasks/$', views.GetRecentlyFlaggedTasks.as_view()),
    url(r'^alerts/incomplete-goals/$', views.GetIncompleteGoals.as_view()),
    url(r'^alerts/recent-anomolous-inputs/$', views.GetRecentAnomolousInputs.as_view()),

]
