import logging
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from demo.views import gallery_context, home_context
from sorl.thumbnail import get_thumbnail


class FailOnError(logging.Handler):
    """sorl logs some failures instead of raising them, like a missing source image."""

    def emit(self, record):
        raise RuntimeError('sorl-thumbnail logged an error: %s' % record.getMessage())


class Command(BaseCommand):
    help = 'Export the gallery of the engine in these settings to site/, plus the homepage for pil'

    def handle(self, **options):
        engine = settings.DEMO_ENGINE
        cache = settings.MEDIA_ROOT / 'cache'
        site = settings.SITE_DIR

        # Start from an empty cache, thumbnails and key-value store together
        shutil.rmtree(cache / engine, ignore_errors=True)
        for path in cache.glob('%s-kvstore*' % engine):
            path.unlink()
        logging.getLogger('sorl.thumbnail').addHandler(FailOnError(logging.ERROR))

        site.mkdir(exist_ok=True)
        page = render_to_string('gallery.html', gallery_context(engine))
        (site / ('demo-%s.html' % engine)).write_text(page)
        if engine == 'pil':
            (site / 'index.html').write_text(render_to_string('index.html', home_context()))
            # The link preview image, made by sorl like everything else on the site
            im = get_thumbnail('images/earth-apollo-11.png', '1200x630', crop='top', quality=85)
            shutil.copyfile(im.storage.path(im.name), site / 'social.jpg')

        shutil.copytree(settings.MEDIA_ROOT / 'images', site / 'media' / 'images',
                        dirs_exist_ok=True, ignore=shutil.ignore_patterns('README.md'))
        shutil.rmtree(site / 'media' / 'cache' / engine, ignore_errors=True)
        shutil.copytree(cache / engine, site / 'media' / 'cache' / engine)
        self.stdout.write('Wrote site/demo-%s.html' % engine)
