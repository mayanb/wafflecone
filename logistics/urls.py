from django.conf.urls import include, url
from django.contrib import admin
from rest_framework_jwt.views import obtain_jwt_token

admin.autodiscover()

#import hello.views

urlpatterns = [
    url(r'^docs/', include('rest_framework_docs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^gauth/', include('gauth.urls')),
    url(r'^ics/', include('ics.urls')),
    url(r'^basic/', include('basic.urls')),
    url(r'^cogs/', include('cogs.urls')),
    url(r'^api-token-auth/', obtain_jwt_token),
    url(r'^auth/', include('rest_auth.urls')),
    url(r'^graphs/', include('graphs.urls')),
]

# if settings.DEBUG:
#     urlpatterns += [url(r'^silk/', include('silk.urls', namespace='silk'))]