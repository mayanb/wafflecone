from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns
from django.contrib.auth import views as auth_views

import oauth2client.contrib.django_util.site as django_util_site


urlpatterns = [ 

    url(r'^v2/', include('ics.v2.urls')),
    url(r'^v3/', include('ics.v3.urls')),
    url(r'^v4/', include('ics.v4.urls')),
    url(r'^v5/', include('ics.v5.urls')),
    url(r'^v6/', include('ics.v6.urls')),
    url(r'', include('ics.v1.urls'))
]

urlpatterns = format_suffix_patterns(urlpatterns)