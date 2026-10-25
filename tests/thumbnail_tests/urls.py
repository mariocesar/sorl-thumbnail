try:
    from django.conf.urls import url
except ImportError:
    from django.urls import re_path as url
from django.conf import settings
from django.views.static import serve

from .views import direct_to_template, item, item_async, item_stream

urlpatterns = [
    url(r'^media/(?P<path>.+)$', serve,
        {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    url(r'^(.*\.html)$', direct_to_template),
    url(r'^items/(?P<pk>\d+)/$', item),
    url(r'^items/(?P<pk>\d+)/async/$', item_async),
    url(r'^items/(?P<pk>\d+)/stream/$', item_stream),
]
