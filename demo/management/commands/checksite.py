import re
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from PIL import Image

from demo.examples import ENGINES

EXTENSIONS = {'jpg': 'JPEG', 'png': 'PNG', 'webp': 'WEBP', 'gif': 'GIF', 'avif': 'AVIF'}


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.ids, self.links, self.images = set(), [], []
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])
        if tag == 'img':
            self.images.append(attrs)


def check_image(site, img):
    """The file is in the site, decodes, and matches its extension and width/height."""
    src = img.get('src', '')
    path = site / unquote(src)
    if not src or src.startswith('/') or urlsplit(src).scheme or not path.is_file():
        return ['image %r is not a file in the site' % src]
    errors = [] if img.get('alt') else ['image %s has no alt text' % src]
    try:
        with Image.open(path) as im:
            im.load()
            size, format_ = im.size, im.format
    except Exception as e:
        return errors + ['image %s does not decode: %s' % (src, e)]
    expected = EXTENSIONS.get(path.suffix[1:].lower())
    if format_ != expected:
        errors.append('%s is %s, not %s' % (src, format_, expected))
    if (img.get('width'), img.get('height')) != tuple(str(n) for n in size):
        errors.append('%s is %dx%d, the page says %sx%s'
                      % ((src,) + size + (img.get('width'), img.get('height'))))
    return errors


def check_sitemap(site, pages):
    """Every sitemap URL is an indexable page, and the link preview image exists."""
    errors = []
    sitemap = site / 'sitemap.xml'
    urls = re.findall(r'<loc>([^<]+)</loc>', sitemap.read_text()) if sitemap.exists() else []
    if not urls:
        errors.append('sitemap.xml is missing or empty')
    for url in urls:
        name = url.removeprefix(settings.SITE_URL) or 'index.html'
        if name not in pages:
            errors.append('sitemap.xml lists %s, which is not a page in the site' % url)
        elif 'name="robots" content="noindex"' in (site / name).read_text():
            errors.append('sitemap.xml lists %s, which is marked noindex' % url)
    social = site / 'social.jpg'
    if not social.is_file():
        return errors + ['social.jpg, the link preview image, is missing']
    with Image.open(social) as im:
        if im.size != (1200, 630):
            errors.append('social.jpg is %dx%d, not 1200x630' % im.size)
    return errors


class Command(BaseCommand):
    help = 'Check site/: links, anchors and images resolve, and images are what the page says'

    def handle(self, **options):
        site = settings.SITE_DIR
        names = ['index.html'] + ['demo-%s.html' % key for key in ENGINES]
        pages = {name: Page(site / name) for name in names if (site / name).exists()}
        errors = ['missing page %s' % name for name in names if name not in pages]

        for name, page in pages.items():
            for href in page.links:
                url = urlsplit(href)
                if url.scheme or href.startswith('mailto:'):
                    continue
                target = unquote(url.path) or name
                if not (site / target).is_file():
                    errors.append('%s: link to missing file %s' % (name, href))
                elif url.fragment and url.fragment not in getattr(pages.get(target), 'ids', ()):
                    errors.append('%s: link to missing anchor %s' % (name, href))
            for img in page.images:
                errors += ['%s: %s' % (name, e) for e in check_image(site, img)]
            html = (site / name).read_text()
            for result in re.findall(r'<div class="result">(.*?)</div>', html, re.S):
                if '<img' not in result:
                    errors.append('%s: an example rendered no image' % name)

        pil = (site / 'demo-pil.html').read_text()
        if 'class="notice"' in pil or 'class="skipped"' in pil:
            errors.append('demo-pil.html: Pillow skipped examples')
        errors += check_sitemap(site, pages)

        for error in errors:
            self.stderr.write(error)
        if errors:
            raise CommandError('%d errors in site/' % len(errors))
        self.stdout.write('Checked %d pages, no errors' % len(pages))
