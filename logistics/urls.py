from django.conf.urls import include, url
from django.contrib import admin
from . import settings

admin.autodiscover()

#import hello.views

urlpatterns = [
    #url(r'^$', hello.views.index, name='index'),
    url(r'^docs/', include('rest_framework_docs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^ics/', include('ics.urls')),
    url(r'^qr/', include('qr.urls')),
    url(r'^dashboard/', include('dashboard.urls')),
]

if settings.DEBUG:
  import debug_toolbar
  urlpatterns = [
    url(r'^__debug__/', include(debug_toolbar.urls)),
  ] + urlpatterns
