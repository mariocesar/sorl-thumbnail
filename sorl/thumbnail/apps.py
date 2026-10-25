from django.apps import AppConfig
from django.core.signals import request_finished


class ThumbnailConfig(AppConfig):
    name = 'sorl.thumbnail'

    def ready(self):
        from sorl.thumbnail.images import release_source

        request_finished.connect(release_source)
