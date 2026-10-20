import os
import platform
import shutil
import unittest
from io import BytesIO
from subprocess import Popen
from unittest import mock

from django.core.files.storage import default_storage, storages
from django.template.loader import render_to_string
from django.test.utils import override_settings
from PIL import Image, ImageSequence, ImageStat

from sorl.thumbnail import default
from sorl.thumbnail.base import EXTENSIONS, ThumbnailBackend
from sorl.thumbnail.conf import settings
from sorl.thumbnail.engines.convert_engine import EngineError
from sorl.thumbnail.engines.pil_engine import Engine as PILEngine
from sorl.thumbnail.helpers import get_module_class, run, tokey
from sorl.thumbnail.images import ImageFile, deserialize_image_file
from sorl.thumbnail.parsers import parse_geometry
from sorl.thumbnail.templatetags.thumbnail import is_portrait, margin

from .models import Item
from .utils import DATA_DIR, BaseTestCase


class SimpleTestCase(BaseTestCase):
    def test_simple(self):
        item = Item.objects.get(image='500x500.jpg')

        t = self.BACKEND.get_thumbnail(item.image, '400x300', crop='center')

        self.assertEqual(t.x, 400)
        self.assertEqual(t.y, 300)

        t = self.BACKEND.get_thumbnail(item.image, '1200x900', crop='13% 89%')

        self.assertEqual(t.x, 1200)
        self.assertEqual(t.y, 900)

    def test_upscale(self):
        item = Item.objects.get(image='100x100.jpg')

        t = self.BACKEND.get_thumbnail(item.image, '400x300', upscale=False)

        self.assertEqual(t.x, 100)
        self.assertEqual(t.y, 100)

        t = self.BACKEND.get_thumbnail(item.image, '400x300', upscale=True)

        self.assertEqual(t.x, 300)
        self.assertEqual(t.y, 300)

    def test_upscale_and_crop(self):
        item = Item.objects.get(image='200x100.jpg')

        t = self.BACKEND.get_thumbnail(item.image, '400x300', crop='center', upscale=False)

        self.assertEqual(t.x, 200)
        self.assertEqual(t.y, 100)

        t = self.BACKEND.get_thumbnail(item.image, '400x300', crop='center', upscale=True)
        self.assertEqual(t.x, 400)
        self.assertEqual(t.y, 300)

    @unittest.skipIf(
        'wand_engine' in settings.THUMBNAIL_ENGINE
        or 'pgmagick_engine' in settings.THUMBNAIL_ENGINE,
        'the wand and pgmagick engines do not implement padding',
    )
    def test_padding(self):
        item = Item.objects.get(image='200x100.jpg')

        t = self.BACKEND.get_thumbnail(item.image, '300x300', padding=True)

        self.assertEqual((t.x, t.y), (300, 300))
        self.assertEqual(Image.open(t.storage.path(t.name)).size, (300, 300))

    @unittest.skipIf(
        'wand_engine' in settings.THUMBNAIL_ENGINE
        or 'pgmagick_engine' in settings.THUMBNAIL_ENGINE,
        'the wand and pgmagick engines do not implement padding',
    )
    def test_padding_color(self):
        item = Item.objects.get(image='200x100.jpg')

        t = self.BACKEND.get_thumbnail(item.image, '300x300', padding=True, padding_color='#ff0000')

        red, green, blue = Image.open(t.storage.path(t.name)).convert('RGB').getpixel((150, 10))
        self.assertTrue(red > 250 and green < 5 and blue < 5, (red, green, blue))

    @unittest.skipIf(
        'pil_engine' not in settings.THUMBNAIL_ENGINE
        and 'vips_engine' not in settings.THUMBNAIL_ENGINE,
        'only the PIL and vips engines implement remove_border',
    )
    def test_remove_border(self):
        # A photo between black bars, the bars must go whatever their color
        photo = Image.open(os.path.join(settings.DATA_ROOT, 'icc_profile_test.jpg'))
        im = Image.new('RGB', (200, 240))
        im.paste(photo.convert('RGB').resize((200, 160)), (0, 40))
        im.save(os.path.join(settings.MEDIA_ROOT, 'letterbox.png'))

        t = self.BACKEND.get_thumbnail('letterbox.png', '200x240', remove_border=True)

        self.assertEqual((t.x, t.y), (200, 160))

    @unittest.skipIf(
        'pil_engine' not in settings.THUMBNAIL_ENGINE
        and 'vips_engine' not in settings.THUMBNAIL_ENGINE,
        'only the PIL and vips engines implement blur',
    )
    def test_crop_and_blur(self):
        item = Item.objects.get(image='200x100.jpg')

        t = self.BACKEND.get_thumbnail(item.image, '100x100', crop="center", blur='3')

        self.assertEqual(t.x, 100)
        self.assertEqual(t.y, 100)

    def test_kvstore(self):
        im = ImageFile(Item.objects.get(image='500x500.jpg').image)
        self.KVSTORE.delete_thumbnails(im)
        th1 = self.BACKEND.get_thumbnail(im, '50')
        th2 = self.BACKEND.get_thumbnail(im, 'x50')
        th3 = self.BACKEND.get_thumbnail(im, '20x20')
        self.assertEqual(
            set([th1.key, th2.key, th3.key]),
            set(self.KVSTORE._get(im.key, identity='thumbnails'))
        )
        self.KVSTORE.delete_thumbnails(im)
        self.assertEqual(
            None,
            self.KVSTORE._get(im.key, identity='thumbnails')
        )

    def test_is_portrait(self):
        im = ImageFile(Item.objects.get(image='500x500.jpg').image)
        th = self.BACKEND.get_thumbnail(im, '50x200', crop='center')
        self.assertEqual(th.is_portrait(), True)
        th = self.BACKEND.get_thumbnail(im, '500x2', crop='center')
        self.assertEqual(th.is_portrait(), False)

    def test_margin(self):
        im = ImageFile(Item.objects.get(image='500x500.jpg').image)
        self.assertEqual(margin(im, '1000x1000'), '250px 250px 250px 250px')
        self.assertEqual(margin(im, '800x1000'), '250px 150px 250px 150px')
        self.assertEqual(margin(im, '500x500'), '0px 0px 0px 0px')
        self.assertEqual(margin(im, '500x501'), '0px 0px 1px 0px')
        self.assertEqual(margin(im, '503x500'), '0px 2px 0px 1px')
        self.assertEqual(margin(im, '300x300'), '-100px -100px -100px -100px')

    def test_kvstore_get_and_set(self):
        im = ImageFile(Item.objects.get(image='500x500.jpg').image)
        self.KVSTORE.delete(im)
        self.assertEqual(self.KVSTORE.get(im), None)
        self.KVSTORE.set(im)
        self.assertEqual(im.size, [500, 500])

    def test_cleanup1(self):
        im = ImageFile(Item.objects.get(image='500x500.jpg').image)
        self.KVSTORE.delete_thumbnails(im)
        th = self.BACKEND.get_thumbnail(im, '3x3')
        self.assertEqual(th.exists(), True)
        th.delete()
        self.assertEqual(th.exists(), False)
        self.assertEqual(self.KVSTORE.get(th).x, 3)
        self.assertEqual(self.KVSTORE.get(th).y, 3)
        self.KVSTORE.cleanup()
        self.assertEqual(self.KVSTORE.get(th), None)
        self.KVSTORE.delete(im)

    def test_cleanup2(self):
        self.KVSTORE.clear()
        im = ImageFile(Item.objects.get(image='500x500.jpg').image)
        th3 = self.BACKEND.get_thumbnail(im, '27x27')
        th4 = self.BACKEND.get_thumbnail(im, '81x81')

        def keys_test(x, y, z):
            self.assertEqual(x, len(list(self.KVSTORE._find_keys(identity='image'))))
            self.assertEqual(y, len(list(self.KVSTORE._find_keys(identity='thumbnails'))))
            self.assertEqual(z, len(self.KVSTORE._get(im.key, identity='thumbnails') or []))

        keys_test(3, 1, 2)
        th3.delete()
        keys_test(3, 1, 2)
        self.KVSTORE.cleanup()
        keys_test(2, 1, 1)
        th4.delete()
        keys_test(2, 1, 1)
        self.KVSTORE.cleanup()
        keys_test(1, 0, 0)
        self.KVSTORE.clear()
        keys_test(0, 0, 0)

    def test_clear_doesnt_regenerate(self):
        self.KVSTORE.clear()
        im = ImageFile(Item.objects.get(image='500x500.jpg').image)
        th = self.BACKEND.get_thumbnail(im, '27x27')
        th_name_orig = self.KVSTORE.get(th).name
        self.KVSTORE.clear()
        th = self.BACKEND.get_thumbnail(im, '27x27')
        th_name_new = self.KVSTORE.get(th).name
        self.assertEqual(
            th_name_orig,
            th_name_new,
        )

    def test_storage_serialize(self):
        im = ImageFile(Item.objects.get(image='500x500.jpg').image)
        self.assertEqual(im.serialize_storage(), 'default')
        self.assertEqual(
            ImageFile('http://www.image.jpg').serialize_storage(),
            'sorl.thumbnail.images.UrlStorage',
        )
        self.assertEqual(
            ImageFile('http://www.image.jpg', default.storage).serialize_storage(),
            'default',
        )
        self.assertEqual(
            ImageFile('getit', default_storage).serialize_storage(),
            'default',
        )

        self.assertEqual(
            im.serialize_storage(use_backend_name=True),
            'tests.thumbnail_tests.storage.TestStorage',
        )
        self.assertEqual(
            ImageFile('http://www.image.jpg').serialize_storage(use_backend_name=True),
            'sorl.thumbnail.images.UrlStorage',
        )
        self.assertEqual(
            ImageFile('http://www.image.jpg', default.storage).serialize_storage(
                use_backend_name=True
            ),
            'tests.thumbnail_tests.storage.TestStorage',
        )
        self.assertEqual(
            ImageFile('getit', default_storage).serialize_storage(use_backend_name=True),
            'tests.thumbnail_tests.storage.TestStorage',
        )

    def test_storage_serialize_same_backend_class(self):
        test_storage = 'tests.thumbnail_tests.storage.TestStorage'
        with self.settings(STORAGES={
            'default': {'BACKEND': test_storage},
            'other': {'BACKEND': test_storage},
        }):
            on_default = ImageFile('same.jpg', storages['default'])
            on_other = ImageFile('same.jpg', storages['other'])
            self.assertEqual(on_default.serialize_storage(), 'default')
            self.assertEqual(on_other.serialize_storage(), 'other')
            # The default storage keeps its pre-13 key, the other one must not collide.
            self.assertEqual(on_default.key, tokey('same.jpg', test_storage))
            self.assertEqual(on_other.key, tokey('same.jpg', 'other'))
            self.assertNotEqual(on_default.key, on_other.key)

    def test_storage_serialize_short_backend_path(self):
        # Django's docs name FileSystemStorage by its re-export, not its module (#834).
        backend = 'django.core.files.storage.FileSystemStorage'
        with self.settings(STORAGES={
            'default': {'BACKEND': backend, 'OPTIONS': {'base_url': '/media/'}},
            'short': {'BACKEND': backend, 'OPTIONS': {'base_url': '/short/'}},
        }):
            on_default = ImageFile('short.jpg', storages['default'])
            on_short = ImageFile('short.jpg', storages['short'])
            on_short.set_size((10, 10))
            self.assertEqual(on_default.serialize_storage(), 'default')
            self.assertEqual(on_short.serialize_storage(), 'short')
            # The default storage keeps its pre-13 key, the real class path.
            self.assertEqual(
                on_default.key,
                tokey('short.jpg', 'django.core.files.storage.filesystem.FileSystemStorage'),
            )
            cached = deserialize_image_file(on_short.serialize())
            self.assertIs(cached.storage, storages['short'])
            self.assertEqual(cached.url, '/short/short.jpg')

    @unittest.skipIf(platform.system() == "Darwin", 'quality is saved a different way on os x')
    def test_quality(self):
        im = ImageFile(Item.objects.get(image='500x500.jpg').image)
        th = self.BACKEND.get_thumbnail(im, '100x100', quality=50)
        img = Image.open(th.storage.path(th.name))
        # Every engine writes JPEG with libjpeg, so quality 50 gives the same tables as Pillow's
        reference = BytesIO()
        Image.new(img.mode, (8, 8)).save(reference, 'JPEG', quality=50)
        self.assertEqual(img.quantization, Image.open(reference).quantization)

    def test_transparency(self):
        item, _created = self.create_image(
            '50x50_transparent.png', (50, 50), transparent=True)
        th = self.BACKEND.get_thumbnail(item.image, '11x11', format='PNG')
        img = Image.open(th.storage.path(th.name))
        self.assertTrue(self.is_transparent(img))

    def test_transparency_gif_to_jpeg(self):
        path = 'data/animation_w_transparency.gif'
        th = self.BACKEND.get_thumbnail(path, '11x11', format='JPEG')
        img = Image.open(th.storage.path(th.name))
        self.assertFalse(self.is_transparent(img))

    @unittest.skipUnless('pil_engine' in settings.THUMBNAIL_ENGINE
                         or 'wand_engine' in settings.THUMBNAIL_ENGINE
                         or 'convert_engine' in settings.THUMBNAIL_ENGINE,
                         'not checked on the pgmagick and vipsthumbnail engines')
    def test_transparency_la_to_jpeg(self):
        Image.new('LA', (50, 50)).save(os.path.join(settings.MEDIA_ROOT, 'la.png'))
        th = self.BACKEND.get_thumbnail('la.png', '11x11', format='JPEG')
        img = Image.open(th.storage.path(th.name))
        self.assertEqual(img.format, 'JPEG')

    @unittest.skipUnless('pil_engine' in settings.THUMBNAIL_ENGINE
                         or 'wand_engine' in settings.THUMBNAIL_ENGINE
                         or 'convert_engine' in settings.THUMBNAIL_ENGINE,
                         'only the PIL, wand and convert engines honour THUMBNAIL_FLATTEN')
    def test_flatten(self):
        # Grey diagonals on a transparent background whose stored color is black
        self.create_image('50x50_transparent.png', (50, 50), transparent=True)
        # Alpha channel with black stored under the transparent pixels
        rgba = Image.new('RGBA', (50, 50), (0, 0, 0, 0))
        rgba.save(os.path.join(settings.MEDIA_ROOT, 'rgba.png'))
        with override_settings(THUMBNAIL_FLATTEN=True):
            for name in ('50x50_transparent.png', 'rgba.png'):
                th = self.BACKEND.get_thumbnail(name, '50x50', format='JPEG')
                img = Image.open(th.storage.path(th.name)).convert('RGB')
                self.assertEqual(img.getpixel((25, 2)), (255, 255, 255))

                for off in ('off', False):
                    th = self.BACKEND.get_thumbnail(name, '50x50', format='JPEG', flatten=off)
                    img = Image.open(th.storage.path(th.name)).convert('RGB')
                    self.assertEqual(img.getpixel((25, 2)), (0, 0, 0))

    @unittest.skipUnless('pil_engine' in settings.THUMBNAIL_ENGINE
                         or 'convert_engine' in settings.THUMBNAIL_ENGINE,
                         'only the PIL and convert engines pad and flatten')
    def test_flatten_padding_color(self):
        rgba = Image.new('RGBA', (50, 25), (0, 0, 0, 0))
        rgba.save(os.path.join(settings.MEDIA_ROOT, 'rgba_wide.png'))
        with override_settings(THUMBNAIL_FLATTEN=True):
            th = self.BACKEND.get_thumbnail(
                'rgba_wide.png', '50x50', format='JPEG', padding=True, padding_color='#ff0000'
            )
        img = Image.open(th.storage.path(th.name)).convert('RGB')
        # The transparent source gets the padding color, not white, like the bars around it
        for xy in ((25, 2), (25, 25)):
            r, g, b = img.getpixel(xy)
            self.assertTrue(r > 250 and g < 5 and b < 5, img.getpixel(xy))

    @unittest.skipIf('pil_engine' not in settings.THUMBNAIL_ENGINE, 'rounded is only in PIL')
    def test_rounded(self):
        Image.new('RGB', (50, 25)).save(os.path.join(settings.MEDIA_ROOT, 'black_wide.png'))

        th = self.BACKEND.get_thumbnail('black_wide.png', '50x25', rounded=10, format='PNG')
        img = Image.open(th.storage.path(th.name))
        self.assertEqual(img.getpixel((0, 0))[3], 0)

        # JPEG has no alpha, so the corners get white like THUMBNAIL_FLATTEN
        for colorspace in ('RGB', 'GRAY'):
            th = self.BACKEND.get_thumbnail(
                'black_wide.png', '50x25', rounded=10, format='JPEG', colorspace=colorspace
            )
            img = Image.open(th.storage.path(th.name)).convert('RGB')
            self.assertTrue(min(img.getpixel((0, 0))) > 250, img.getpixel((0, 0)))
            self.assertTrue(max(img.getpixel((25, 12))) < 5, img.getpixel((25, 12)))

        th = self.BACKEND.get_thumbnail(
            'black_wide.png', '50x50', rounded=10, format='JPEG', padding=True,
            padding_color='#ff0000'
        )
        img = Image.open(th.storage.path(th.name)).convert('RGB')
        r, g, b = img.getpixel((0, 12))
        self.assertTrue(r > 250 and g < 5 and b < 5, img.getpixel((0, 12)))

    @unittest.skipIf('pil_engine' not in settings.THUMBNAIL_ENGINE, 'blur is only supported in PIL')
    def test_flatten_blur_and_remove_border(self):
        # A white and a noise square inside a 20px transparent border whose stored color is black
        rgba = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
        rgba.paste((255, 255, 255, 255), (20, 20, 80, 80))
        rgba.save(os.path.join(settings.MEDIA_ROOT, 'rgba_white.png'))
        rgba.paste(Image.effect_noise((60, 60), 64).convert('RGB'), (20, 20))
        rgba.save(os.path.join(settings.MEDIA_ROOT, 'rgba_border.png'))
        with override_settings(THUMBNAIL_FLATTEN=True):
            # Flattened onto white it is all white, the black doesn't bleed in with blur
            th = self.BACKEND.get_thumbnail('rgba_white.png', '100x100', format='JPEG', blur=3)
            img = Image.open(th.storage.path(th.name)).convert('L')
            self.assertTrue(img.getextrema()[0] > 245, img.getextrema())

            th = self.BACKEND.get_thumbnail(
                'rgba_border.png', '100x100', format='JPEG', remove_border=True
            )
            img = Image.open(th.storage.path(th.name)).convert('L')
            self.assertTrue(ImageStat.Stat(img.crop((0, 0, 100, 5))).mean[0] < 200)

    @unittest.skipIf('pil_engine' not in settings.THUMBNAIL_ENGINE, 'blur is only supported in PIL')
    def test_transparent_blur(self):
        rgba = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
        rgba.paste((255, 255, 255, 255), (20, 20, 80, 80))
        rgba.save(os.path.join(settings.MEDIA_ROOT, 'rgba_white.png'))
        th = self.BACKEND.get_thumbnail('rgba_white.png', '100x100', format='PNG', blur=3)
        img = Image.open(th.storage.path(th.name))
        # The edge fades out, but stays white instead of mixing with the black under it
        r, g, b, a = img.getpixel((18, 50))
        self.assertTrue(0 < a < 255 and min(r, g, b) > 245, img.getpixel((18, 50)))

    @unittest.skipIf('pil_engine' not in settings.THUMBNAIL_ENGINE, 'remove_border is only in PIL')
    def test_transparent_remove_border(self):
        # A 20px transparent border, first over noise, then around a black logo drawn by its alpha
        noise = Image.effect_noise((100, 100), 64)
        border = Image.new('L', (100, 100), 0)
        border.paste(255, (20, 20, 80, 80))
        logo = Image.new('L', (100, 100), 0)
        logo.paste(noise.crop((20, 20, 80, 80)), (20, 20))
        sources = {'rgba_noise_border.png': (noise, border),
                   'rgba_black_logo.png': (Image.new('L', (100, 100)), logo)}
        for name, (rgb, alpha) in sources.items():
            rgba = rgb.convert('RGBA')
            rgba.putalpha(alpha)
            rgba.save(os.path.join(settings.MEDIA_ROOT, name))
            th = self.BACKEND.get_thumbnail(
                name, '500x500', format='PNG', remove_border=True, upscale=False
            )
            self.assertEqual((th.width, th.height), (60, 60), name)

    def test_remove_border_size(self):
        engine = PILEngine()
        cases = [
            ((2000, 30), 0, (858, 14)),  # plain, came out (856, 10), a third off top and bottom
            ((600, 100), 8, (584, 84)),  # came out (590, 100)
            ((600, 600), 8, (584, 584)),  # thinner than a 10px strip, nothing was removed
            ((600, 600), 15, (570, 570)),  # came out (580, 580)
        ]
        for source, border, expected in cases:
            with self.subTest(source=source, border=border):
                im = Image.new('L', source, 255)
                if border:
                    noise = (source[0] - 2 * border, source[1] - 2 * border)
                    im.paste(Image.effect_noise(noise, 64), (border, border))
                options = dict(ThumbnailBackend.default_options, remove_border=True, upscale=False)
                im = engine.create(im, (5000, 5000), options)
                self.assertEqual(im.size, expected)

    @unittest.skipIf(
        settings.THUMBNAIL_CONVERT.startswith('gm ')
        or 'pgmagick_engine' in settings.THUMBNAIL_ENGINE,
        'GraphicsMagick has no AVIF encoder',
    )
    def test_avif_output(self):
        im = ImageFile(Item.objects.get(image='500x500.jpg').image)
        th = self.BACKEND.get_thumbnail(im, '100x100', format='AVIF')
        img = Image.open(th.storage.path(th.name))
        self.assertEqual(img.format, 'AVIF')
        self.assertEqual(img.size, (100, 100))

    @unittest.skipIf('pil_engine' not in settings.THUMBNAIL_ENGINE, 'animation is only kept in PIL')
    def test_animated_gif(self):
        # A red square moving right over a transparent background
        frames = []
        for x in (0, 50, 100):
            frame = Image.new('RGBA', (200, 100))
            frame.paste((255, 0, 0, 255), (x, 0, x + 50, 100))
            frames.append(frame)
        frames[0].save(os.path.join(settings.MEDIA_ROOT, 'animated.gif'), save_all=True,
                       append_images=frames[1:], duration=[100, 200, 300], loop=0, disposal=2)

        th = self.BACKEND.get_thumbnail('animated.gif', '100x50', format='GIF')
        img = Image.open(th.storage.path(th.name))
        self.assertEqual((th.x, th.y), (100, 50))
        self.assertEqual(img.info['loop'], 0)
        self.assertEqual([frame.info['duration'] for frame in ImageSequence.Iterator(img)],
                         [100, 200, 300])
        # The square left the top left corner, it must not leave a trail there
        img.seek(2)
        self.assertEqual(img.convert('RGBA').getpixel((0, 0))[3], 0)

    def test_image_file_deserialize(self):
        im = ImageFile(Item.objects.get(image='500x500.jpg').image)
        default.kvstore.set(im)
        self.assertEqual(
            default.kvstore.get(im).serialize_storage(),
            'default',
        )
        im = ImageFile('https://dummyimage.com/300x300/')
        default.kvstore.set(im)
        self.assertEqual(
            default.kvstore.get(im).serialize_storage(),
            'sorl.thumbnail.images.UrlStorage',
        )

    def test_abspath(self):
        item = Item.objects.get(image='500x500.jpg')
        image = ImageFile(item.image.path)
        val = render_to_string('thumbnail20.html', {'image': image, }).strip()

        im = self.BACKEND.get_thumbnail(image, '32x32', crop='center')
        self.assertEqual('<img src="%s">' % im.url, val)

    def test_new_tag_style(self):
        item = Item.objects.get(image='500x500.jpg')
        image = ImageFile(item.image.path)
        val = render_to_string('thumbnail20a.html', {'image': image, }).strip()

        im = self.BACKEND.get_thumbnail(image, '32x32', crop='center')
        self.assertEqual('<img src="%s">' % im.url, val)

    def test_relative_absolute_same_key(self):
        image = Item.objects.get(image='500x500.jpg').image
        imref1 = ImageFile(image.name)
        imref2 = ImageFile(os.path.join(settings.MEDIA_ROOT, image.name))
        self.assertEqual(imref1.key, imref2.key)

        self.create_image('medialibrary.jpg', (100, 100))
        image = Item.objects.get(image='medialibrary.jpg').image
        imref1 = ImageFile(image.name)
        imref2 = ImageFile(os.path.join(settings.MEDIA_ROOT, image.name))
        self.assertEqual(imref1.key, imref2.key)

        self.create_image('mediaäöü.jpg', (100, 100))
        image = Item.objects.get(image='mediaäöü.jpg').image
        imref1 = ImageFile(image.name)
        imref2 = ImageFile(os.path.join(settings.MEDIA_ROOT, image.name))
        self.assertEqual(imref1.key, imref2.key)

    @unittest.skipIf(
        'convert_engine' in settings.THUMBNAIL_ENGINE,
        'ImageMagick and GraphicsMagick reject the RGBA colorspace',
    )
    def test_rgba_colorspace(self):
        item = Item.objects.get(image='500x500.jpg')

        t = self.BACKEND.get_thumbnail(item.image, '100x100', colorspace="RGBA", format="JPEG")
        self.assertEqual(t.x, 100)
        self.assertEqual(t.y, 100)

    def test_calculate_scaling_factor_noop_crop(self):
        engine = PILEngine()

        factor_none = engine._calculate_scaling_factor(800, 600, (400, 400), {'crop': None})
        factor_noop = engine._calculate_scaling_factor(800, 600, (400, 400), {'crop': 'noop'})
        factor_center = engine._calculate_scaling_factor(800, 600, (400, 400), {'crop': 'center'})

        # crop='noop' must scale identically to crop being unset (fit-within-bounds).
        self.assertEqual(factor_noop, factor_none)
        # A real crop value should still use the max()-based, crop-fitting behavior.
        self.assertNotEqual(factor_noop, factor_center)
        self.assertEqual(factor_center, max(400 / 800, 400 / 600))
        self.assertEqual(factor_none, min(400 / 800, 400 / 600))

    @unittest.skipIf(
        'convert_engine' not in settings.THUMBNAIL_ENGINE,
        'read options are only supported by the convert engine',
    )
    def test_read_options(self):
        item = Item.objects.get(image='100x100.jpg')
        cases = {'density': '300'}
        if not settings.THUMBNAIL_CONVERT.startswith('gm'):
            cases['authenticate'] = 'secret'  # gm identify has no -authenticate

        with mock.patch('subprocess.Popen', wraps=Popen) as popen:
            t = self.BACKEND.get_thumbnail(item.image, '50x50', **cases)

        self.assertEqual((t.x, t.y), (50, 50))
        self.assertNotEqual(t.name, self.BACKEND.get_thumbnail(item.image, '50x50').name)

        convert = settings.THUMBNAIL_CONVERT.split(' ')
        identify = settings.THUMBNAIL_IDENTIFY.split(' ')
        for key, value in cases.items():
            flag = '-' + key
            commands = [call.args[0] for call in popen.call_args_list if flag in call.args[0]]
            # both the convert and the identify run must read the source with the flag
            self.assertTrue(any(args[:len(convert)] == convert for args in commands))
            self.assertTrue(any(args[:len(identify)] == identify for args in commands))
            for args in commands:
                source = next(arg for arg in args if arg.endswith('[0]'))
                self.assertEqual(args[args.index(flag) + 1], value)
                self.assertLess(args.index(flag), args.index(source))

    @unittest.skipIf(
        'convert_engine' not in settings.THUMBNAIL_ENGINE,
        'only the convert engine shells out to identify',
    )
    def test_identify_failure(self):
        with open(os.path.join(settings.MEDIA_ROOT, 'broken.pdf'), 'wb') as f:
            f.write(b'not a pdf')
        with self.assertRaises(EngineError):
            self.BACKEND.get_thumbnail('broken.pdf', '50x50')

    @unittest.skipIf(
        'convert_engine' not in settings.THUMBNAIL_ENGINE,
        'only the convert engine shells out to identify',
    )
    def test_read_option_without_details(self):
        with open(os.path.join(settings.MEDIA_ROOT, 'broken.pdf'), 'wb') as f:
            f.write(b'not a pdf')
        with self.assertRaises(EngineError) as cm:
            self.BACKEND.get_thumbnail('broken.pdf', '50x50', authenticate='hunter2')
        # neither the password, the command line nor the tool's stderr leak into the error
        self.assertEqual(str(cm.exception), 'The identify command did not report an image size')

    @unittest.skipIf(
        'vipsthumbnail_engine' not in settings.THUMBNAIL_ENGINE,
        'only the vipsthumbnail engine shells out to vipsheader',
    )
    def test_vipsheader_failure(self):
        with open(os.path.join(settings.MEDIA_ROOT, 'broken.pdf'), 'wb') as f:
            f.write(b'not a pdf')
        with self.assertRaises(EngineError):
            self.BACKEND.get_thumbnail('broken.pdf', '50x50')

    @unittest.skipIf(
        'convert_engine' not in settings.THUMBNAIL_ENGINE,
        'only the convert engine falls back to another format',
    )
    def test_unsupported_output_format(self):
        item = Item.objects.get(image='100x100.jpg')
        # stands in for AVIF on an ImageMagick without the libheif encoder plugin
        with mock.patch.dict(EXTENSIONS, {'NOPE': 'nope'}):
            with self.assertRaises(EngineError) as cm:
                self.BACKEND.get_thumbnail(item.image, '50x50', format='NOPE')
        self.assertIn('The convert command wrote JPEG instead of NOPE', str(cm.exception))

    @unittest.skipIf(
        'convert_engine' not in settings.THUMBNAIL_ENGINE,
        'only the convert engine checks the written format',
    )
    def test_format_check_only_on_conversion(self):
        item = Item.objects.get(image='100x100.jpg')
        with mock.patch('subprocess.Popen', wraps=Popen) as popen:
            self.BACKEND.get_thumbnail(item.image, '40x40', format='JPEG')
            self.BACKEND.get_thumbnail(item.image, '40x40', format='PNG')
        checks = [call.args[0] for call in popen.call_args_list if '%m' in call.args[0]]
        # JPEG to JPEG can't fall back to another format, so only the PNG is checked
        self.assertEqual(len(checks), 1)
        self.assertTrue(checks[0][-1].endswith('.png[0]'))

    def test_falsey_file_argument(self):
        with self.assertRaises(ValueError):
            self.BACKEND.get_thumbnail('', '100x100')
        with self.assertRaises(ValueError):
            self.BACKEND.get_thumbnail(None, '100x100')


class CropTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()

        # portrait
        name = 'portrait.jpg'
        fn = os.path.join(settings.MEDIA_ROOT, name)
        im = Image.new('L', (100, 200))
        im.paste(255, (0, 0, 100, 100))
        im.save(fn)
        self.portrait = ImageFile(Item.objects.get_or_create(image=name)[0].image)
        self.KVSTORE.delete(self.portrait)

        # landscape
        name = 'landscape.jpg'
        fn = os.path.join(settings.MEDIA_ROOT, name)
        im = Image.new('L', (200, 100))
        im.paste(255, (0, 0, 100, 100))
        im.save(fn)
        self.landscape = ImageFile(Item.objects.get_or_create(image=name)[0].image)
        self.KVSTORE.delete(self.landscape)

    def test_portrait_crop(self):
        def mean_pixel(x, y):
            values = im.getpixel((x, y))
            if not isinstance(values, (tuple, list)):
                values = [values]
            return sum(values) / len(values)

        for crop in ('center', '88% 50%', '50px'):
            th = self.BACKEND.get_thumbnail(self.portrait, '100x100', crop=crop)
            engine = PILEngine()
            im = engine.get_image(th)

            self.assertEqual(mean_pixel(50, 0), 255)
            self.assertEqual(mean_pixel(50, 45), 255)
            self.assertEqual(250 <= mean_pixel(50, 49) <= 255, True, mean_pixel(50, 49))
            self.assertEqual(mean_pixel(50, 55), 0)
            self.assertEqual(mean_pixel(50, 99), 0)

        for crop in ('top', '0%', '0px'):
            th = self.BACKEND.get_thumbnail(self.portrait, '100x100', crop=crop)
            engine = PILEngine()
            im = engine.get_image(th)
            for x in range(0, 99, 10):
                for y in range(0, 99, 10):
                    self.assertEqual(250 < mean_pixel(x, y) <= 255, True)

        for crop in ('bottom', '100%', '100px'):
            th = self.BACKEND.get_thumbnail(self.portrait, '100x100', crop=crop)
            engine = PILEngine()
            im = engine.get_image(th)
            for x in range(0, 99, 10):
                for y in range(0, 99, 10):
                    self.assertEqual(0 <= mean_pixel(x, y) < 5, True)

    def test_landscape_crop(self):

        def mean_pixel(x, y):
            values = im.getpixel((x, y))
            if not isinstance(values, (tuple, list)):
                values = [values]
            return sum(values) / len(values)

        for crop in ('center', '50% 200%', '50px 700px'):
            th = self.BACKEND.get_thumbnail(self.landscape, '100x100', crop=crop)
            engine = PILEngine()
            im = engine.get_image(th)

            self.assertEqual(mean_pixel(0, 50), 255)
            self.assertEqual(254 <= mean_pixel(45, 50) <= 255, True)
            self.assertEqual(250 < mean_pixel(49, 50) <= 255, True)
            self.assertEqual(mean_pixel(55, 50), 0)
            self.assertEqual(mean_pixel(99, 50), 0)

        for crop in ('left', '0%', '0px'):
            th = self.BACKEND.get_thumbnail(self.landscape, '100x100', crop=crop)
            engine = PILEngine()
            im = engine.get_image(th)
            for x in range(0, 99, 10):
                for y in range(0, 99, 10):
                    self.assertEqual(250 < mean_pixel(x, y) <= 255, True)

        for crop in ('right', '100%', '100px'):
            th = self.BACKEND.get_thumbnail(self.landscape, '100x100', crop=crop)
            engine = PILEngine()
            im = engine.get_image(th)
            coords = ((x, y) for y in range(0, 99, 10) for x in range(0, 99, 10))

            for x, y in coords:
                self.assertEqual(0 <= mean_pixel(x, y) < 5, True)

    @unittest.skipIf(
        'pil_engine' not in settings.THUMBNAIL_ENGINE
        and 'vips_engine' not in settings.THUMBNAIL_ENGINE,
        'only the PIL and vips engines implement smart crop',
    )
    def test_smart_crop(self):
        th = self.BACKEND.get_thumbnail('data/white_border.jpg', '32x32', crop='smart')
        self.assertEqual(th.x, 32)
        self.assertEqual(th.y, 32)

        engine = PILEngine()
        im = engine.get_image(th)
        self.assertEqual(im.size[0], 32)
        self.assertEqual(im.size[1], 32)

    def test_smart_crop_size(self):
        engine = PILEngine()
        cases = [
            ((1280, 720), (200, 200), True, (200, 200)),  # came out 44px wide
            ((500, 442), (60, 60), True, (60, 60)),  # never returned
            ((720, 1280), (50, 100), True, (50, 100)),  # raised ValueError
            ((100, 50), (200, 200), False, (50, 50)),  # not scaled, never returned
        ]
        for source, geometry, upscale, expected in cases:
            with self.subTest(source=source, geometry=geometry):
                options = dict(ThumbnailBackend.default_options, crop='smart', upscale=upscale)
                im = engine.create(Image.new('RGB', source), geometry, options)
                self.assertEqual(im.size, expected)

    @unittest.skipIf(
        'pil_engine' in settings.THUMBNAIL_ENGINE or 'vips_engine' in settings.THUMBNAIL_ENGINE,
        'the PIL and vips engines support smart crop',
    )
    def test_smart_crop_unsupported(self):
        message = "crop='smart' is only supported by the PIL engine"
        with self.assertRaisesMessage(NotImplementedError, message):
            self.BACKEND.get_thumbnail('data/white_border.jpg', '32x32', crop='smart')

    def test_image_with_orientation(self):
        name = 'data/aspect_test.jpg'
        item, _ = Item.objects.get_or_create(image=name)

        im = ImageFile(item.image)
        th = self.BACKEND.get_thumbnail(im, '50x50')

        # this is a 100x200 image with orientation 6 (90 degrees CW rotate)
        # the thumbnail should end up 25x50
        self.assertEqual(th.x, 25)
        self.assertEqual(th.y, 50)

    def test_orientation_off_applies_to_one_call(self):
        # aspect_test.jpg is stored 200x100 with orientation 6, so it shows as 100x200
        source = os.path.join(DATA_DIR, 'aspect_test.jpg')
        for name in 'abcd':
            shutil.copy(source, os.path.join(DATA_DIR, f'{name}.jpg'))

        th = self.BACKEND.get_thumbnail('data/a.jpg', '50')
        self.assertEqual((th.x, th.y), (50, 100))
        th = self.BACKEND.get_thumbnail('data/b.jpg', '50', orientation=False)
        self.assertEqual((th.x, th.y), (50, 25))
        th = self.BACKEND.get_thumbnail('data/c.jpg', '50')
        self.assertEqual((th.x, th.y), (50, 100))
        self.assertTrue(is_portrait('data/d.jpg'))

    @unittest.skipIf(
        'pgmagick_engine' in settings.THUMBNAIL_ENGINE,
        'keeping the ICC profile is not verified on the pgmagick engine',
    )
    def test_crop_image_with_icc_profile(self):
        name = 'data/icc_profile_test.jpg'
        item, _ = Item.objects.get_or_create(image=name)

        im = ImageFile(item.image)
        th = self.BACKEND.get_thumbnail(im, '100x100')

        engine = PILEngine()

        self.assertEqual(
            engine.get_image(im).info.get('icc_profile'),
            engine.get_image(th).info.get('icc_profile')
        )


# Only PIL has support for checking pixel color. convert and wand engines are both missing it,
# so we cannot test for pixel color
class CropBoxTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()

        # portrait
        name = 'portrait.jpg'
        fn = os.path.join(settings.MEDIA_ROOT, name)
        im = Image.new('L', (100, 200))
        im.paste(255, (0, 0, 100, 100))
        im.save(fn)
        self.portrait = ImageFile(Item.objects.get_or_create(image=name)[0].image)
        self.KVSTORE.delete(self.portrait)

        # landscape
        name = 'landscape.jpg'
        fn = os.path.join(settings.MEDIA_ROOT, name)
        im = Image.new('L', (200, 100))
        im.paste(255, (0, 0, 100, 100))
        im.save(fn)
        self.landscape = ImageFile(Item.objects.get_or_create(image=name)[0].image)
        self.KVSTORE.delete(self.landscape)

    @unittest.skipIf(
        'pil_engine' not in settings.THUMBNAIL_ENGINE,
        'the other engines fail this test',
    )
    def PIL_test_portrait_crop(self):
        def mean_pixel(x, y):
            values = im.getpixel((x, y))
            if not isinstance(values, (tuple, list)):
                values = [values]
            return sum(values) / len(values)

        # Center Crop
        th = self.BACKEND.get_thumbnail(self.portrait, '100x100', cropbox="0,50,100,150")
        engine = PILEngine()
        im = engine.get_image(th)

        # Top half should be color, bottom not
        self.assertEqual(mean_pixel(0, 0), 255)
        self.assertEqual(mean_pixel(50, 0), 255)
        self.assertEqual(mean_pixel(50, 45), 255)
        self.assertEqual(mean_pixel(50, 55), 0)
        self.assertEqual(mean_pixel(50, 99), 0)

        # Top Crop
        th = self.BACKEND.get_thumbnail(self.portrait, '100x100', cropbox="0,0,100,100")
        engine = PILEngine()
        im = engine.get_image(th)
        for x in range(0, 99, 10):
            for y in range(0, 99, 10):
                self.assertEqual(250 < mean_pixel(x, y) <= 255, True)

        # Bottom Crop
        th = self.BACKEND.get_thumbnail(self.portrait, '100x100', cropbox="0,100,100,200")
        engine = PILEngine()
        im = engine.get_image(th)
        for x in range(0, 99, 10):
            for y in range(0, 99, 10):
                self.assertEqual(0 <= mean_pixel(x, y) < 5, True)

    @unittest.skipIf(
        'pil_engine' not in settings.THUMBNAIL_ENGINE,
        'the other engines fail this test',
    )
    def PIL_test_landscape_crop(self):

        def mean_pixel(x, y):
            values = im.getpixel((x, y))
            if not isinstance(values, (tuple, list)):
                values = [values]
            return sum(values) / len(values)

        # Center
        th = self.BACKEND.get_thumbnail(self.landscape, '100x100', cropbox="50,0,150,100")
        engine = PILEngine()
        im = engine.get_image(th)

        self.assertEqual(mean_pixel(0, 50), 255)
        self.assertEqual(mean_pixel(45, 50), 255)
        self.assertEqual(250 < mean_pixel(49, 50) <= 255, True)
        self.assertEqual(mean_pixel(55, 50), 0)
        self.assertEqual(mean_pixel(99, 50), 0)

        # Left
        th = self.BACKEND.get_thumbnail(self.landscape, '100x100', cropbox="0,0,100,100")
        engine = PILEngine()
        im = engine.get_image(th)
        for x in range(0, 99, 10):
            for y in range(0, 99, 10):
                self.assertEqual(250 < mean_pixel(x, y) <= 255, True)

        # Right
        th = self.BACKEND.get_thumbnail(self.landscape, '100x100', cropbox="100,0,200,100")
        engine = PILEngine()
        im = engine.get_image(th)
        coords = ((x, y) for y in range(0, 99, 10) for x in range(0, 99, 10))

        for x, y in coords:
            self.assertEqual(0 <= mean_pixel(x, y) < 5, True)

    @unittest.skipIf(
        'wand_engine' not in settings.THUMBNAIL_ENGINE,
        'the other engines fail this test',
    )
    def wand_test_cropbox(self):
        from sorl.thumbnail.engines.wand_engine import Engine as WandEngine
        th = self.BACKEND.get_thumbnail(self.portrait, '100x100', cropbox="0,50,100,150")
        engine = WandEngine()
        im = engine.get_image(th)

        # If the crop went well, then it should scale to 100x100 perfectly
        self.assertEqual(im.width(100), 100)
        self.assertEqual(im.height(100), 100)

    @unittest.skipIf(
        'pgmagick_engine' not in settings.THUMBNAIL_ENGINE,
        'the other engines fail this test',
    )
    def pgmagick_test_cropbox(self):
        from sorl.thumbnail.engines.pgmagick_engine import Engine as PgMagickEngine
        th = self.BACKEND.get_thumbnail(self.portrait, '100x100', cropbox="0,50,100,150")
        engine = PgMagickEngine()
        im = engine.get_image(th)

        # If the crop went well, then it should scale to 100x100 perfectly
        self.assertEqual(im.width(100), 100)
        self.assertEqual(im.height(100), 100)

    @unittest.skipIf(
        'convert_engine' not in settings.THUMBNAIL_ENGINE,
        'the other engines fail this test',
    )
    def convert_test_cropbox(self):
        from sorl.thumbnail.engines.convert_engine import Engine as ConvertEngine
        th = self.BACKEND.get_thumbnail(self.portrait, '100x100', cropbox="0,50,100,150")
        engine = ConvertEngine()
        im = engine.get_image(th)

        # If the crop went well, then it should scale to 100x100 perfectly
        self.assertEqual(im["size"], (100, 100))


class DummyTestCase(unittest.TestCase):
    def setUp(self):
        self.BACKEND = get_module_class(settings.THUMBNAIL_BACKEND)()

    def tearDown(self):
        super().tearDown()
        settings.THUMBNAIL_ALTERNATIVE_RESOLUTIONS = []

    def test_dummy_tags(self):
        settings.THUMBNAIL_DUMMY = True

        val = render_to_string('thumbnaild1.html', {'anything': 'AINO', }).strip()
        self.assertEqual(val, '<img style="margin:auto" width="200" height="100">')
        val = render_to_string('thumbnaild2.html', {'anything': None, }).strip()
        self.assertEqual(
            val,
            '<img src="https://dummyimage.com/300x200" width="300" height="200"><p>NOT</p>'
        )
        val = render_to_string('thumbnaild3.html', {}).strip()
        self.assertEqual(val, '<img src="https://dummyimage.com/600x400" width="600" height="400">')

        settings.THUMBNAIL_DUMMY = False

    def test_alternative_resolutions(self):
        settings.THUMBNAIL_DUMMY = True
        settings.THUMBNAIL_ALTERNATIVE_RESOLUTIONS = [1.5, 2]
        val = render_to_string('thumbnaild4.html', {}).strip()
        self.assertEqual(
            val,
            '<img src="https://dummyimage.com/600x400" width="600" '
            'height="400" srcset="https://dummyimage.com/1200x800 2x; '
            'https://dummyimage.com/900x600 1.5x">'
        )


class ShellTestCase(unittest.TestCase):
    def test_captures_text_and_exit_code(self):
        p = run(['sh', '-c', 'echo out; echo err >&2; exit 3'])
        self.assertEqual((p.returncode, p.stdout, p.stderr), (3, 'out\n', 'err\n'))

    def test_large_stderr_does_not_block(self):
        # more than a pipe buffer on stderr deadlocked the old Popen + wait() pattern
        p = run(['sh', '-c', 'head -c 300000 /dev/zero | tr "\\0" x >&2'])
        self.assertEqual((p.returncode, len(p.stderr)), (0, 300000))

    def test_stdin_is_closed(self):
        # cat would block on an inherited terminal instead of returning
        self.assertEqual(run(['cat']).stdout, '')

    def test_missing_tool(self):
        with self.assertRaises(EngineError) as cm:
            run(['sorl-thumbnail-no-such-tool'])
        self.assertEqual(
            str(cm.exception), 'sorl-thumbnail-no-such-tool is not installed or not on PATH'
        )

    @override_settings(THUMBNAIL_COMMAND_TIMEOUT=0.1)
    def test_timeout(self):
        with self.assertRaises(EngineError) as cm:
            run(['sleep', '5'])
        self.assertEqual(
            str(cm.exception), 'sleep did not finish in 0.1 seconds, see THUMBNAIL_COMMAND_TIMEOUT'
        )


class ImageValidationTestCase(unittest.TestCase):
    def setUp(self):
        self.BACKEND = get_module_class(settings.THUMBNAIL_BACKEND)()

    def test_truncated_validation(self):
        """
        Test that is_valid_image returns false for a truncated image.
        """
        buffer = BytesIO()
        Image.effect_noise((400, 300), 64).convert('RGB').save(buffer, 'JPEG')
        data = buffer.getvalue()
        with open(os.path.join(settings.DATA_ROOT, 'broken.jpeg'), 'rb') as broken_jpeg:
            broken = broken_jpeg.read()

        engine = PILEngine()

        self.assertTrue(engine.is_valid_image(data))
        self.assertFalse(engine.is_valid_image(data[:-400]))
        self.assertFalse(engine.is_valid_image(broken))

    @unittest.skipIf(
        'vips_engine' not in settings.THUMBNAIL_ENGINE,
        'only the PIL and vips engines decode every pixel to validate an image',
    )
    def test_vips_truncated_validation(self):
        with open(os.path.join(settings.DATA_ROOT, 'broken.jpeg'), 'rb') as broken_jpeg:
            self.assertFalse(default.engine.is_valid_image(broken_jpeg.read()))

    @unittest.skipIf(
        'pil_engine' not in settings.THUMBNAIL_ENGINE,
        'ImageMagick and wand fill the missing part of a truncated image with grey',
    )
    def test_truncated_generation_failure(self):
        """
        Confirm that generating a thumbnail for our "broken" image fails.
        """
        name = os.path.join(settings.DATA_ROOT, 'broken.jpeg')
        with open(name, 'rb') as broken_jpeg:

            with self.assertRaises((OSError, IOError,)):
                im = default.engine.get_image(broken_jpeg)

                options = ThumbnailBackend.default_options
                ratio = default.engine.get_image_ratio(im, options)
                geometry = parse_geometry('120x120', ratio)
                default.engine.create(im, geometry, options)
