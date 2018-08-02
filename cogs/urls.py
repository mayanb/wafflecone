from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from . import views

urlpatterns = [
    url(r'^adjustments/square/$', views.CreateSquareAdjustments.as_view(), name='square_adjustments'),
    url(r'^adjustments/csv/$', views.CreateCsvAdjustments.as_view(), name='create_csv_adjustments'),
]

urlpatterns = format_suffix_patterns(urlpatterns)
