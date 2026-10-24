import os

from django.template import Template, TemplateSyntaxError
from django.template.loader import render_to_string
from django.test import Client, TestCase
from django.test.utils import override_settings
from PIL import Image

from sorl.thumbnail.conf import settings
from sorl.thumbnail.engines.pil_engine import Engine as PILEngine

from .models import Item
from .utils import DATA_DIR, BaseTestCase


class TemplateTestCaseA(BaseTestCase):
    def test_model(self):
        item = Item.objects.get(image='500x500.jpg')
        val = render_to_string('thumbnail1.html', {'item': item, }).strip()
        self.assertEqual(val, '<img style="margin:0px 0px 0px 0px" width="200" height="100">')
        val = render_to_string('thumbnail2.html', {'item': item, }).strip()
        self.assertEqual(val, '<img style="margin:0px 50px 0px 50px" width="100" height="100">')

    def test_nested(self):
        item = Item.objects.get(image='500x500.jpg')
        val = render_to_string('thumbnail6.html', {'item': item, }).strip()
        self.assertEqual(val, (
            '<a href="/media/test/cache/fc/f6/fcf65c09cc4bb8671147de41997422bf.jpg">'
            '<img src="/media/test/cache/67/6b/676b2331a071478b0cb280d0edba7818.jpg" '
            'width="400" height="400"></a>'
        ))

    def test_serialization_options(self):
        item = Item.objects.get(image='500x500.jpg')

        for _ in range(0, 20):
            # we could be lucky...
            val0 = render_to_string('thumbnail7.html', {
                'item': item,
            }).strip()
            val1 = render_to_string('thumbnail7a.html', {
                'item': item,
            }).strip()
            self.assertEqual(val0, val1)

    def test_options(self):
        item = Item.objects.get(image='500x500.jpg')
        options = {
            'crop': "center",
            'upscale': True,
            'quality': 77,
        }
        val0 = render_to_string('thumbnail8.html', {'item': item, 'options': options, }).strip()
        val1 = render_to_string('thumbnail8a.html', {'item': item, }).strip()
        self.assertEqual(val0, val1)

    def test_progressive(self):
        im = Item.objects.get(image='500x500.jpg').image
        th = self.BACKEND.get_thumbnail(im, '100x100', progressive=True)
        path = os.path.join(settings.MEDIA_ROOT, th.name)
        self.assertTrue(Image.open(path).info.get('progressive'))

    def test_nonprogressive(self):
        im = Item.objects.get(image='500x500.jpg').image
        th = self.BACKEND.get_thumbnail(im, '100x100', progressive=False)
        path = os.path.join(settings.MEDIA_ROOT, th.name)
        self.assertFalse(Image.open(path).info.get('progressive'))

    def test_orientation(self):
        ref = Image.open(os.path.join(DATA_DIR, '1_topleft.jpg'))
        top = ref.getpixel((14, 7))
        left = ref.getpixel((7, 14))
        engine = PILEngine()

        def epsilon(x, y):
            if isinstance(x, (tuple, list)):
                x = sum(x) / len(x)
            if isinstance(y, (tuple, list)):
                y = sum(y) / len(y)
            return abs(x - y)

        data_images = (
            '1_topleft.jpg',
            '2_topright.jpg',
            '3_bottomright.jpg',
            '4_bottomleft.jpg',
            '5_lefttop.jpg',
            '6_righttop.jpg',
            '7_rightbottom.jpg',
            '8_leftbottom.jpg'
        )

        for name in data_images:
            th = self.BACKEND.get_thumbnail('data/%s' % name, '30x30')
            im = engine.get_image(th)

            self.assertLess(epsilon(top, im.getpixel((14, 7))), 10)
            self.assertLess(epsilon(left, im.getpixel((7, 14))), 10)
            exif = im._getexif()

            # no exif editor in GraphicsMagick
            if exif and not (
                settings.THUMBNAIL_CONVERT.endswith('gm convert')
                or 'pgmagick_engine' in settings.THUMBNAIL_ENGINE
            ):
                self.assertEqual(exif.get(0x0112), 1)


class TemplateTestCaseB(BaseTestCase):
    def test_url(self):
        val = render_to_string('thumbnail3.html', {}).strip()
        self.assertEqual(val, '<img style="margin:0px 0px 0px 0px" width="20" height="20">')

    def test_portrait(self):
        val = render_to_string('thumbnail4.html', {
            'source': 'https://dummyimage.com/120x100/',
            'dims': 'x66',
        }).strip()
        self.assertEqual(val,
                         '<img src="/media/test/cache/82/62/8262858c5f95f2bd7715d7aaa3e52b11.jpg" '
                         'width="79" height="66" class="landscape">')

        val = render_to_string('thumbnail4.html', {
            'source': 'https://dummyimage.com/100x120/',
            'dims': 'x66',
        }).strip()
        self.assertEqual(val, '<img width="1" height="1" class="portrait">')

        with override_settings(THUMBNAIL_DEBUG=True):
            with self.assertRaises(FileNotFoundError):
                render_to_string('thumbnail4a.html', {
                    'source': 'broken.jpeg',
                }).strip()

        with override_settings(THUMBNAIL_DEBUG=False):
            val = render_to_string('thumbnail4a.html', {
                'source': 'broken.jpeg',
            }).strip()
            self.assertEqual(val, 'no')

    def test_empty(self):
        val = render_to_string('thumbnail5.html', {}).strip()
        self.assertEqual(val, '<p>empty</p>')


class TemplateTestCaseClient(TestCase):
    def test_empty_error(self):
        with override_settings(THUMBNAIL_DEBUG=False):
            from django.core.mail import outbox

            client = Client()
            response = client.get('/thumbnail9.html')
            self.assertEqual(response.content.strip(), b'<p>empty</p>')
            self.assertEqual(outbox[0].subject, '[sorl-thumbnail] ERROR: Unknown URL')

            end = outbox[0].body.split('\n\n')[-2].split(':')[1].strip()

            self.assertEqual(end, '[Errno 2] No such file or directory')


class TemplateTestCaseSyntax(TestCase):
    def test_missing_arguments(self):
        sources = [
            '{% thumbnail %}',
            '{% thumbnail source %}',
            '{% thumbnail source as im %}{% endthumbnail %}',
            '{% thumbnail as im %}{% endthumbnail %}',
            '{% thumbnail source "100x100" as im %}{% thumbnail %}',
        ]
        for source in sources:
            with self.subTest(source=source):
                with self.assertRaises(TemplateSyntaxError):
                    Template('{% load thumbnail %}' + source)


class TemplateTestCaseTemplateTagAlias(BaseTestCase):
    """Testing alternative template tag (alias)."""

    def test_model(self):
        item = Item.objects.get(image='500x500.jpg')
        val = render_to_string(
            'thumbnail1_alias.html', {'item': item}
        ).strip()
        self.assertEqual(
            val,
            '<img style="margin:0px 0px 0px 0px" width="200" height="100">'
        )
        val = render_to_string(
            'thumbnail2_alias.html', {'item': item}
        ).strip()
        self.assertEqual(
            val,
            '<img style="margin:0px 50px 0px 50px" width="100" height="100">'
        )

    def test_nested(self):
        item = Item.objects.get(image='500x500.jpg')
        val = render_to_string(
            'thumbnail6_alias.html', {'item': item}
        ).strip()
        self.assertEqual(
            val,
            (
                '<a href="/media/test/cache/fc/f6/'
                'fcf65c09cc4bb8671147de41997422bf.jpg">'
                '<img src="/media/test/cache/67/6b/'
                '676b2331a071478b0cb280d0edba7818.jpg" '
                'width="400" height="400"></a>'
            )
        )

    def test_serialization_options(self):
        item = Item.objects.get(image='500x500.jpg')

        for _ in range(0, 20):
            # we could be lucky...
            val0 = render_to_string('thumbnail7_alias.html', {
                'item': item,
            }).strip()
            val1 = render_to_string('thumbnail7a_alias.html', {
                'item': item,
            }).strip()
            self.assertEqual(val0, val1)

    def test_options(self):
        item = Item.objects.get(image='500x500.jpg')
        options = {
            'crop': "center",
            'upscale': True,
            'quality': 77,
        }
        val0 = render_to_string(
            'thumbnail8_alias.html',
            {'item': item, 'options': options}
        ).strip()
        val1 = render_to_string(
            'thumbnail8a_alias.html', {'item': item}
        ).strip()
        self.assertEqual(val0, val1)
