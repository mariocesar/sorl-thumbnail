import logging
import os
import shutil
from contextlib import contextmanager

from django.test import TestCase
from PIL import Image, ImageDraw

from sorl.thumbnail.conf import settings
from sorl.thumbnail.helpers import get_module_class
from sorl.thumbnail.images import ImageFile
from sorl.thumbnail.log import ThumbnailLogHandler

from .models import Item
from .storage import MockLoggingHandler

DATA_DIR = os.path.join(settings.MEDIA_ROOT, 'data')

handler = ThumbnailLogHandler()
handler.setLevel(logging.ERROR)
logging.getLogger('sorl.thumbnail').addHandler(handler)


@contextmanager
def same_open_fd_count(testcase):
    num_opened_fd_before = get_open_fds_count()
    yield
    num_opened_fd_after = get_open_fds_count()
    testcase.assertEqual(
        num_opened_fd_before, num_opened_fd_after,
        'Open descriptors count changed, was %s, now %s' % (num_opened_fd_before,
                                                            num_opened_fd_after)
    )


def get_open_fds_count():
    """Return the number of open file descriptors for current process."""
    return len(os.listdir('/dev/fd'))


class FakeFile:
    """
    Used to test the _get_format method.
    """

    def __init__(self, name):
        self.name = name


class BaseTestCase(TestCase):
    IMAGE_DIMENSIONS = [(500, 500), (100, 100), (200, 100), ]
    BACKEND = None
    ENGINE = None
    KVSTORE = None

    def create_image(self, name, dim, transparent=False):
        """
        Creates an image and prepends the MEDIA ROOT path.
        :param name: e.g. 500x500.jpg
        :param dim: a dimension tuple e.g. (500, 500)
        """
        filename = os.path.join(settings.MEDIA_ROOT, name)
        im = Image.new('L', dim)

        if transparent:
            draw = ImageDraw.Draw(im)
            draw.line((0, 0) + im.size, fill=128)
            draw.line((0, im.size[1], im.size[0], 0), fill=128)

            im.save(filename, transparency=0)
        else:
            im.save(filename)

        return Item.objects.get_or_create(image=name)

    def is_transparent(self, img):
        return img.mode in ('RGBA', 'LA') or 'transparency' in img.info

    def setUp(self):
        self.BACKEND = get_module_class(settings.THUMBNAIL_BACKEND)()
        self.ENGINE = get_module_class(settings.THUMBNAIL_ENGINE)()
        self.KVSTORE = get_module_class(settings.THUMBNAIL_KVSTORE)()
        # A shared Redis keeps keys between runs; start every test from an empty store
        self.KVSTORE.clear()

        if not os.path.exists(settings.MEDIA_ROOT):
            os.makedirs(settings.MEDIA_ROOT)
            shutil.copytree(settings.DATA_ROOT, DATA_DIR)

        for dimension in self.IMAGE_DIMENSIONS:
            name = '%sx%s.jpg' % dimension
            self.create_image(name, dimension)

    def tearDown(self):
        shutil.rmtree(settings.MEDIA_ROOT)


class BaseStorageTestCase(TestCase):
    image = None
    name = None

    def setUp(self):
        os.makedirs(settings.MEDIA_ROOT)
        filename = os.path.join(settings.MEDIA_ROOT, self.name)
        Image.new('L', (100, 100)).save(filename)
        self.image = ImageFile(self.name)

        logger = logging.getLogger('slog')
        logger.setLevel(logging.DEBUG)
        handler = MockLoggingHandler(level=logging.DEBUG)
        logger.addHandler(handler)
        self.log = handler.messages['debug']

    def tearDown(self):
        shutil.rmtree(settings.MEDIA_ROOT)
