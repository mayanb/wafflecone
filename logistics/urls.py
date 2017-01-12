from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

import hello.views

urlpatterns = [
    url(r'^$', hello.views.index, name='index'),
    url(r'^db', hello.views.db, name='db'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^ics/', include('ics.urls')),
    url(r'^qr/', include('qr.urls')),
    url(r'^dashboard/', include('dashboard.urls'))
]
