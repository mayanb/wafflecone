from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^ics/', include('ics.urls')),
    url(r'^qr/', include('qr.urls')),
    url(r'^dashboard/', include('dashboard.urls'))
]
