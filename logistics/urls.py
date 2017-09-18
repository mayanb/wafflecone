from django.conf.urls import include, url
from django.contrib import admin
from . import settings
from django.contrib.auth import views as auth_views

admin.autodiscover()

#import hello.views

urlpatterns = [
    #url(r'^$', hello.views.index, name='index'),
    url(r'^docs/', include('rest_framework_docs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^gauth/', include('gauth.urls')),
    url(r'^ics/', include('ics.urls')),
    url(r'^qr/', include('qr.urls')),
    #url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    #url(r'^dashboard/', include('dashboard.urls')),
]

# if settings.DEBUG:
#   import debug_toolbar
#   urlpatterns = [
#     url(r'^__debug__/', include(debug_toolbar.urls)),
#   ] + urlpatterns
