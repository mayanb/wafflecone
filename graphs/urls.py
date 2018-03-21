from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from graphs.v2 import views

urlpatterns = [
    url(r'^production-actuals/$', views.production_actuals),
]

urlpatterns = format_suffix_patterns(urlpatterns)