from django.apps import AppConfig
from django.core.signals import request_finished, request_started


class ThumbnailConfig(AppConfig):
    name = 'sorl.thumbnail'

    def ready(self):
        from sorl.thumbnail.images import close_source_cache, open_source_cache

        request_started.connect(open_source_cache)
        request_finished.connect(close_source_cache)
