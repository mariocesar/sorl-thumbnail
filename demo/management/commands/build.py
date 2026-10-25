import shutil
import subprocess
import sys

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string

from demo.examples import ENGINES, missing
from demo.views import gallery_context


class Command(BaseCommand):
    help = 'Export the homepage and every engine gallery to site/, then check it'

    def add_arguments(self, parser):
        parser.add_argument('--engines', default=','.join(ENGINES),
                            help='engines to build, the rest get a page without results')
        parser.add_argument('--require', default='',
                            help='fail if one of these engines is missing')

    def handle(self, engines, require, **options):
        selected = [key for key in engines.split(',') if key]
        required = [key for key in require.split(',') if key]
        for key in selected + required:
            if key not in ENGINES:
                raise CommandError('Unknown engine %r, choose from %s' % (key, ', '.join(ENGINES)))
        if 'pil' not in selected:
            raise CommandError('pil is needed, it renders the homepage')
        for key in required:
            if key not in selected or missing(key):
                raise CommandError('%s is required but not selected or missing' % key)

        shutil.rmtree(settings.SITE_DIR, ignore_errors=True)
        settings.SITE_DIR.mkdir()
        built = []
        for key in ENGINES:
            if key not in selected:
                reason = 'Not included in this build'
            elif missing(key):
                reason = 'This site was built without %s' % ', '.join(missing(key))
            else:
                reason = ''

            if reason:
                self.stdout.write('%s: %s' % (key, reason))
                page = render_to_string('gallery.html', gallery_context(key, False, reason))
                (settings.SITE_DIR / ('demo-%s.html' % key)).write_text(page)
                continue

            # sorl's settings are process-wide, so each engine renders in its own process
            command = [sys.executable, settings.BASE_DIR / 'manage.py', 'render',
                       '--settings=demo.settings.%s' % key]
            if subprocess.run(command, timeout=300).returncode:
                raise CommandError('Rendering %s failed, see the error above' % key)
            built.append(key)

        # Pages without results are left out, they are marked noindex
        paths = [''] + ['demo-%s.html' % key for key in built]
        sitemap = render_to_string('sitemap.xml', {'site_url': settings.SITE_URL, 'paths': paths})
        (settings.SITE_DIR / 'sitemap.xml').write_text(sitemap)
        call_command('checksite')
