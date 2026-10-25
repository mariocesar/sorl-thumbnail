import io
import logging
from collections import Counter
from unittest import skipIf

import django
from django.core.cache import cache
from django.core.files.storage import Storage
from django.template import Context, Template
from django.test import AsyncClient, Client
from PIL import Image

from sorl.thumbnail import delete, get_thumbnail, source_cache
from sorl.thumbnail.images import ImageFile, sources
from sorl.thumbnail.templatetags.thumbnail import is_portrait

from .models import Item
from .storage import MockLoggingHandler
from .utils import BaseTestCase, same_open_fd_count

FILTER_THEN_TAG = Template(
    '{% load thumbnail %}{{ item.image|is_portrait }}'
    '{% thumbnail item.image "100x100" as im %}{{ im.url }}{% endthumbnail %}'
)
TAG_THEN_FILTER = Template(
    '{% load thumbnail %}'
    '{% thumbnail item.image "100x100" as im %}{{ im.url }}{% endthumbnail %}'
    '{{ item.image|is_portrait }}'
)
THREE_SIZES = Template(
    '{% load thumbnail %}'
    '{% thumbnail item.image "100x100" as im %}{{ im.url }}{% endthumbnail %}'
    '{% thumbnail item.image "200x200" as im %}{{ im.url }}{% endthumbnail %}'
    '{% thumbnail item.image "300x300" as im %}{{ im.url }}{% endthumbnail %}'
)


def jpeg(width, height):
    buffer = io.BytesIO()
    Image.new('L', (width, height)).save(buffer, 'JPEG')
    return buffer.getvalue()


class Stream(io.BytesIO):
    """Readable but not seekable, like an HTTP response body."""

    def seekable(self):
        return False

    def seek(self, *args):
        raise io.UnsupportedOperation('seek')

    def tell(self):
        raise io.UnsupportedOperation('tell')


class RemoteStorage(Storage):
    """In-memory storage that counts how often each file is fetched."""

    def __init__(self, files=None):
        self.files = files or {}
        self.fetches = Counter()

    def open(self, name, mode='rb'):
        self.fetches[name] += 1
        if name not in self.files:
            raise FileNotFoundError(name)
        return Stream(self.files[name])

    def exists(self, name):
        return name in self.files


class SourceCacheTestCase(BaseTestCase):
    """Inside a request or a source_cache() block the last source read is kept."""

    def setUp(self):
        super().setUp()
        # The rolled back database leaves sizes from earlier tests in the cache
        cache.clear()
        self.handler = MockLoggingHandler(level=logging.DEBUG)
        logger = logging.getLogger('slog')
        logger.setLevel(logging.DEBUG)
        logger.addHandler(self.handler)
        self.item = Item.objects.get(image='500x500.jpg')

    def tearDown(self):
        logging.getLogger('slog').removeHandler(self.handler)
        super().tearDown()

    def opens(self, name='500x500.jpg'):
        return self.handler.messages['debug'].count('open: %s' % name)

    def test_filter_then_tag(self):
        with source_cache():
            FILTER_THEN_TAG.render(Context({'item': self.item}))
        self.assertEqual(self.opens(), 1)

    def test_tag_then_filter(self):
        with source_cache():
            TAG_THEN_FILTER.render(Context({'item': self.item}))
        self.assertEqual(self.opens(), 1)

    def test_three_sizes(self):
        with source_cache():
            THREE_SIZES.render(Context({'item': self.item}))
        self.assertEqual(self.opens(), 1)

    def test_outside_a_block_every_read_opens_the_file(self):
        FILTER_THEN_TAG.render(Context({'item': self.item}))
        self.assertEqual(self.opens(), 2)
        self.assertIsNone(sources.get())

    def test_known_thumbnails_read_nothing(self):
        with source_cache():
            THREE_SIZES.render(Context({'item': self.item}))
        with source_cache():
            THREE_SIZES.render(Context({'item': self.item}))
        self.assertEqual(self.opens(), 1)

    def test_field_instances_of_one_file_share_the_read(self):
        other = Item.objects.get(pk=self.item.pk)
        with source_cache():
            get_thumbnail(self.item.image, '50x50')
            get_thumbnail(other.image, '60x60')
        self.assertEqual(self.opens(), 1)

    def test_only_the_last_source_is_kept(self):
        other = Item.objects.get(image='100x100.jpg')
        with source_cache():
            get_thumbnail(self.item.image, '50x50')
            get_thumbnail(other.image, '50x50')
            get_thumbnail(self.item.image, '60x60')
        self.assertEqual(self.opens('500x500.jpg'), 2)
        self.assertEqual(self.opens('100x100.jpg'), 1)

    def test_block_end_drops_the_source(self):
        with source_cache():
            get_thumbnail(self.item.image, '50x50')
        self.assertIsNone(sources.get())
        with source_cache():
            get_thumbnail(self.item.image, '60x60')
        self.assertEqual(self.opens(), 2)

    def test_nested_block_has_its_own_source(self):
        with source_cache():
            get_thumbnail(self.item.image, '50x50')
            with source_cache():
                get_thumbnail(self.item.image, '60x60')
            get_thumbnail(self.item.image, '70x70')
        self.assertEqual(self.opens(), 2)

    def test_exception_ends_the_block(self):
        with self.assertRaises(ValueError), source_cache():
            get_thumbnail(self.item.image, '50x50')
            raise ValueError
        self.assertIsNone(sources.get())

    def test_storage_identifies_the_content(self):
        a = RemoteStorage({'x.jpg': jpeg(100, 200)})
        b = RemoteStorage({'x.jpg': jpeg(200, 100)})
        with source_cache():
            self.assertEqual(ImageFile('x.jpg', storage=a).read(), a.files['x.jpg'])
            self.assertEqual(ImageFile('x.jpg', storage=b).read(), b.files['x.jpg'])
            self.assertEqual(ImageFile('x.jpg', storage=b).read(), b.files['x.jpg'])
        self.assertEqual(a.fetches['x.jpg'], 1)
        self.assertEqual(b.fetches['x.jpg'], 1)

    def test_storage_override_wins_over_the_field_storage(self):
        remote = RemoteStorage({'500x500.jpg': jpeg(100, 200)})
        with source_cache():
            source = ImageFile(self.item.image, storage=remote)
            self.assertEqual(source.read(), remote.files['500x500.jpg'])
            self.assertEqual(get_thumbnail(source, '50x50').size, [25, 50])
        self.assertEqual(remote.fetches['500x500.jpg'], 1)
        self.assertEqual(self.opens(), 0)

    def test_non_seekable_source(self):
        remote = RemoteStorage({'x.jpg': jpeg(100, 200)})
        source = ImageFile('x.jpg', storage=remote)
        self.assertEqual(source.read(), remote.files['x.jpg'])
        with source_cache():
            self.assertTrue(is_portrait(source))
            self.assertEqual(get_thumbnail(source, '50x50').size, [25, 50])
        self.assertEqual(remote.fetches['x.jpg'], 2)

    def test_failed_read_is_not_kept(self):
        remote = RemoteStorage({})
        with source_cache():
            with self.assertRaises(FileNotFoundError):
                ImageFile('x.jpg', storage=remote).read()
            remote.files['x.jpg'] = jpeg(100, 200)
            self.assertEqual(ImageFile('x.jpg', storage=remote).read(), remote.files['x.jpg'])
        self.assertEqual(remote.fetches['x.jpg'], 2)

    def test_caller_handles_are_left_alone(self):
        self.item.image.open('rb')
        self.item.image.read(10)
        with source_cache():
            get_thumbnail(self.item.image, '50x50')
            get_thumbnail(self.item.image, '60x60')
            self.assertEqual(self.item.image.tell(), 10)
            self.item.image.close()
            self.item.image.open('rb')
            self.item.image.read(20)
            get_thumbnail(self.item.image, '70x70')
        # The caller's first open and sorl's own; FieldFile.open() after close() skips the storage
        self.assertEqual(self.opens(), 2)
        self.assertFalse(self.item.image.closed)
        self.assertEqual(self.item.image.tell(), 20)
        self.item.image.close()

    def test_source_replaced_inside_a_block(self):
        with source_cache():
            get_thumbnail(self.item.image, '50x50')
            self.create_image('500x500.jpg', (100, 200))
            # The kept read is served until the source is deleted from the store
            self.assertEqual(get_thumbnail(self.item.image, '60x60').size, [60, 60])
            delete(self.item.image, delete_file=False)
            self.assertEqual(get_thumbnail(self.item.image, '60x60').size, [30, 60])
        self.assertEqual(self.opens(), 2)

    def test_request_reads_once_and_releases(self):
        with same_open_fd_count(self):
            response = Client().get('/items/%d/' % self.item.pk)
        self.assertContains(response, 'landscape')
        self.assertEqual(self.opens(), 1)
        self.assertIsNone(sources.get())

    @skipIf(django.VERSION < (6, 1), 'request_started reaches an ASGI request from Django 6.1')
    async def test_async_request_reads_once_and_releases(self):
        response = await AsyncClient().get('/items/%d/async/' % self.item.pk)
        self.assertContains(response, 'landscape')
        self.assertEqual(self.opens(), 1)
        self.assertIsNone(sources.get())
