from django.conf.urls import url
from ics.v8 import views


urlpatterns = [
    url(r'^use-code/$', views.UseCode.as_view()),
    url(r'^is-code-available/$', views.IsCodeAvailable.as_view()),
    url(r'^codes/$', views.InviteCodeList.as_view()), 

    url(r'^users/$', views.UserList.as_view()),
    url(r'^users/(?P<pk>[0-9]+)/$', views.UserGet.as_view()),
    url(r'^userprofiles/$', views.UserProfileList.as_view()),
    url(r'^userprofiles/(?P<pk>[0-9]+)/$', views.UserProfileGet.as_view()),
    url(r'^userprofiles/edit/(?P<pk>[0-9]+)/$', views.UserProfileEdit.as_view()),
    url(r'^userprofiles/clear-token/(?P<pk>[0-9]+)/$', views.UserProfileClearToken.as_view()),
    url(r'^userprofiles/last-seen/(?P<pk>[0-9]+)/$', views.UserProfileLastSeenUpdate.as_view()),
    url(r'^userprofiles/increment-walkthrough/(?P<pk>[0-9]+)/$', views.UserProfileIncrementWalkthroughUpdate.as_view()),
    url(r'^userprofiles/complete-walkthrough/(?P<pk>[0-9]+)/$', views.UserProfileCompleteWalkthroughUpdate.as_view()),

    url(r'^users/create/$', views.UserProfileCreate.as_view(), name='create_userprofile'),
    url(r'^userprofiles/change-username-password/(?P<pk>[0-9]+)/$', views.UserChangeUsernamePassword.as_view()),

    url(r'^teams/$', views.TeamList.as_view()),
    url(r'^teams/(?P<pk>[0-9]+)/$', views.TeamGet.as_view()),
    url(r'^teams/create/$', views.TeamCreate.as_view(), name='create_team'),

    url(r'^$', views.index, name='index'),
    
    url(r'^tasks/create/$', views.TaskCreate.as_view(), name='create_task'),
    url(r'^tasks/$', views.TaskList.as_view(), name='tasks'),
    url(r'^tasks/(?P<pk>[0-9]+)/$', views.TaskDetail.as_view(), name='task_detail'),
    url(r'^tasks/edit/(?P<pk>[0-9]+)/$', views.TaskEdit.as_view()),
    url(r'^tasks/search/$', views.TaskSearch.as_view()),
    url(r'^tasks/simple/$', views.SimpleTaskSearch.as_view()),
    url(r'^tasks/delete/(?P<pk>[0-9]+)/$', views.DeleteTask.as_view()),

    url(r'^items/create/$', views.CreateItem.as_view()),
    url(r'^items/$', views.ItemList.as_view()),
    url(r'^items/(?P<pk>[0-9]+)/$', views.ItemDetail.as_view()),

    url(r'^inputs/create/$', views.CreateInput.as_view(), name='create_input'),

    url(r'^processes/$', views.ProcessList.as_view(), name='process_types'),
    url(r'^processes/(?P<pk>[0-9]+)/$', views.ProcessDetail.as_view(), name='process_type_detail'),
    url(r'^processes/move/(?P<pk>[0-9]+)/$', views.ProcessMoveDetail.as_view()),
    url(r'^processes/duplicate/$', views.ProcessDuplicate.as_view(), name='process_duplicate'),


    url(r'^products/$', views.ProductList.as_view(), name='product_types'),
    url(r'^products/(?P<pk>[0-9]+)/$', views.ProductDetail.as_view(), name='product_type_detail'),
    url(r'^products/codes/$', views.ProductCodes.as_view()),

    url(r'^attributes/$', views.AttributeList.as_view(), name='attributes'),
    url(r'^attributes/(?P<pk>[0-9]+)/$', views.AttributeDetail.as_view(), name='attribute_detail'),
    url(r'^attributes/move/(?P<pk>[0-9]+)/$', views.ReorderAttribute.as_view(), name='attribute_move'),

    url(r'^taskAttributes/$', views.TaskAttributeList.as_view()),
    url(r'^taskAttributes/create/$', views.TaskAttributeCreate.as_view(), name='create_task_attribute'),
    url(r'^taskAttributes/(?P<pk>[0-9]+)/$', views.TaskAttributeDetail.as_view()),

    url(r'^movements/create/$', views.MovementCreate.as_view(), name='create_movement'),
    url(r'^movements/$', views.MovementList.as_view()),
    url(r'^movements/(?P<pk>[0-9]+)/$', views.MovementReceive.as_view()),

    url(r'^inventory/$', views.InventoryList.as_view()),
    url(r'^inventory/detail/$', views.InventoryDetail.as_view()),
    url(r'^inventory/detail-test/$', views.InventoryDetailTest2.as_view()), # this is the one in production!!!!

    url(r'^activity/$', views.ActivityList.as_view()),
    url(r'^activity/detail/$', views.ActivityListDetail.as_view()),

    url(r'^goals/$', views.GoalList.as_view(), name='goals'),
    url(r'^goals/(?P<pk>[0-9]+)/$', views.GoalGet.as_view()),
    url(r'^goals/create/$', views.GoalCreate.as_view(), name='create_goal'),
    url(r'^goals/edit/(?P<pk>[0-9]+)/$', views.GoalRetrieveUpdateDestroy.as_view(), name='goal_edit'),
    url(r'^goals/move/(?P<pk>[0-9]+)/$', views.ReorderGoal.as_view(), name='goal_move'),

    url(r'^alerts/$', views.AlertList.as_view()),
    url(r'^alerts/(?P<pk>[0-9]+)/$', views.AlertGet.as_view()),
    url(r'^alerts/create/$', views.AlertCreate.as_view()),
    url(r'^alerts/edit/(?P<pk>[0-9]+)/$', views.AlertEdit.as_view()),
    url(r'^alerts/mark-as-read/$', views.AlertsMarkAsRead.as_view()),

    url(r'^alerts/recently-flagged-tasks/$', views.GetRecentlyFlaggedTasks.as_view()),
    url(r'^alerts/recently-unflagged-tasks/$', views.GetRecentlyUnflaggedTasks.as_view()),
    url(r'^alerts/incomplete-goals/$', views.GetIncompleteGoals.as_view()),
    url(r'^alerts/complete-goals/$', views.GetCompleteGoals.as_view()),
    url(r'^alerts/recent-anomolous-inputs/$', views.GetRecentAnomolousInputs.as_view()),

    url(r'^adjustments/$', views.CreateAdjustment.as_view(), name='adjustments'),

    url(r'^inventories/$', views.InventoryList2.as_view(), name='inventories'),

    url(r'^adjustment-history/$', views.AdjustmentHistory.as_view(), name='adjustment-history'),
]

