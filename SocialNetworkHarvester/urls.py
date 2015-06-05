# coding=UTF-8

from django.conf.urls.defaults import patterns, include, url
import grappelli

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^grappelli/', include('grappelli.urls')),
    url(r'^fandjango/', include('fandjango.urls')),
    url(r'^admin/', include(admin.site.urls)),
    (r'^login/$', 'django.contrib.auth.views.login'),
    (r'^logout/$', 'django.contrib.auth.views.logout'),
    url(r'', include("snh.urls")),


)
