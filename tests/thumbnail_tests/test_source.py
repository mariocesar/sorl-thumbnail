import logging
import pickle

from django.core.cache import cache
from django.template import Context, Template
from django.test import Client

from sorl.thumbnail import get_thumbnail
from sorl.thumbnail.images import release_source

from .models import Item
from .storage import MockLoggingHandler
from .utils import BaseTestCase, same_open_fd_count

FILTER_THEN_TAG = Template(
    '{% load thumbnail %}{{ item.image|is_portrait }}'
    '{% thumbnail item.image "100x100" as im %}{{ im.url }}{% endthumbnail %}'
)
THREE_SIZES = Template(
    '{% load thumbnail %}'
    '{% thumbnail item.image "100x100" as im %}{{ im.url }}{% endthumbnail %}'
    '{% thumbnail item.image "200x200" as im %}{{ im.url }}{% endthumbnail %}'
    '{% thumbnail item.image "300x300" as im %}{{ im.url }}{% endthumbnail %}'
)
FILTER_ONLY = Template('{% load thumbnail %}{{ item.image|is_portrait }}')


class FieldFileSourceTestCase(BaseTestCase):
    """A model field source is downloaded once, however many times sorl reads it."""

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
        # is_portrait reads the source for its size, then the tag reads it to resize
        FILTER_THEN_TAG.render(Context({'item': self.item}))
        self.assertEqual(self.opens(), 1)

    def test_three_sizes(self):
        THREE_SIZES.render(Context({'item': self.item}))
        self.assertEqual(self.opens(), 1)

    def test_filter_only(self):
        FILTER_ONLY.render(Context({'item': self.item}))
        self.assertEqual(self.opens(), 1)

    def test_string_source_is_read_each_time(self):
        # A plain name has no FieldFile to keep open
        FILTER_THEN_TAG.render(Context({'item': {'image': '500x500.jpg'}}))
        self.assertEqual(self.opens(), 2)

    def test_file_the_user_opened_is_left_alone(self):
        self.item.image.open('rb')
        self.item.image.read(10)

        get_thumbnail(self.item.image, '100x100')

        # sorl opened its own handle and did not move the user's
        self.assertEqual(self.opens(), 2)
        self.assertFalse(self.item.image.closed)
        self.assertEqual(self.item.image.tell(), 10)
        self.item.image.close()

    def test_next_source_releases_the_previous_one(self):
        other = Item.objects.get(image='100x100.jpg')

        get_thumbnail(self.item.image, '50x50')
        get_thumbnail(other.image, '50x50')
        self.assertTrue(self.item.image.closed)
        self.assertFalse(other.image.closed)

        get_thumbnail(self.item.image, '60x60')
        self.assertFalse(self.item.image.closed)
        self.assertTrue(other.image.closed)

        self.assertEqual(self.opens('500x500.jpg'), 2)
        self.assertEqual(self.opens('100x100.jpg'), 1)

    def test_released_source_reads_like_a_new_one(self):
        get_thumbnail(self.item.image, '100x100')
        release_source()
        self.assertTrue(self.item.image.closed)

        # The user's read opens a new handle through the storage
        self.assertEqual(len(self.item.image.read()), self.item.image.size)
        self.assertEqual(self.opens(), 2)
        self.item.image.close()

    def test_user_read_while_held_gets_the_whole_file(self):
        get_thumbnail(self.item.image, '100x100')
        self.assertEqual(len(self.item.image.read()), self.item.image.size)

    def test_user_closes_the_held_source(self):
        get_thumbnail(self.item.image, '100x100')
        self.item.image.close()

        # The next thumbnail opens it again instead of reading a closed file
        im = get_thumbnail(self.item.image, '50x50')
        self.assertEqual(im.size, [50, 50])
        self.assertEqual(self.opens(), 2)

    def test_pickled_copy_is_closed(self):
        get_thumbnail(self.item.image, '100x100')
        copy = pickle.loads(pickle.dumps(self.item))
        self.assertFalse(self.item.image.closed)
        self.assertTrue(copy.image.closed)

    def test_end_of_request_releases_the_source(self):
        # item.html runs is_portrait then the tag; request_finished closes the file
        with same_open_fd_count(self):
            response = Client().get('/items/%d/' % self.item.pk)
        self.assertContains(response, 'landscape')
        self.assertEqual(self.opens(), 1)
