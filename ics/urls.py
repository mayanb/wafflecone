from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns



urlpatterns = [ 
    url(r'^v4/', include('ics.v4.urls')),
    url(r'^v7/', include('ics.v7.urls')),
    url(r'^v8/', include('ics.v8.urls')),
    url(r'^v9/', include('ics.v9.urls')),
    url(r'^v10/', include('ics.v10.urls')),
    url(r'^v11/', include('ics.v11.urls')),

    url(r'', include('ics.v11.urls'))
]

urlpatterns = format_suffix_patterns(urlpatterns)