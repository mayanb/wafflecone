from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns
from django.contrib.auth import views as auth_views

import oauth2client.contrib.django_util.site as django_util_site


urlpatterns = [ 
    url(r'^v4/', include('ics.v4.urls')),
    url(r'^v7/', include('ics.v7.urls')),
    url(r'^v8/', include('ics.v8.urls')),
    url(r'^v9/', include('ics.v8.urls')),
  
    url(r'', include('ics.v7.urls'))
]

urlpatterns = format_suffix_patterns(urlpatterns)