from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns


urlpatterns = [ 
    url(r'^v9/', include('basic.v9.urls')),
    url(r'^v10/', include('basic.v10.urls')),
    url(r'^v11/', include('basic.v11.urls')),

    url(r'', include('basic.v11.urls'))
]

urlpatterns = format_suffix_patterns(urlpatterns)