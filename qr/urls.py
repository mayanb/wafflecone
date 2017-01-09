from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='qr'),
    url(r'^codes/$', views.codes, name='codes'),
]