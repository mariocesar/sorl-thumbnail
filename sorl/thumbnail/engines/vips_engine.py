import pyvips

from sorl.thumbnail.base import EXTENSIONS
from sorl.thumbnail.engines.base import EngineBase


class Engine(EngineBase):
    def get_image(self, source):
        # Raise on a truncated source like PIL instead of filling it with grey
        return pyvips.Image.new_from_buffer(source.read(), '', fail_on='truncated')

    def get_image_size(self, image):
        return image.width, image.height

    def is_valid_image(self, raw_data):
        try:
            # Decode every pixel, a truncated file only fails there
            pyvips.Image.new_from_buffer(raw_data, '', fail_on='truncated').avg()
        except pyvips.Error:
            return False
        return True

    def _orientation(self, image):
        return image.autorot()

    def _flip_dimensions(self, image):
        return image.get_typeof('orientation') and image.get('orientation') in (5, 6, 7, 8)

    def _colorspace(self, image, colorspace):
        if colorspace == 'RGB':
            return image.colourspace('srgb')
        if colorspace == 'GRAY':
            return image.colourspace('b-w')
        return image

    def _remove_border(self, image, image_width, image_height):
        # The top left pixel is the border color
        left, top, width, height = image.find_trim(background=image.getpoint(0, 0))
        if not width or not height:  # the image is plain
            return image
        return image.crop(left, top, width, height)

    def _entropy_crop(self, image, geometry_width, geometry_height, image_width, image_height):
        width = min(geometry_width, image_width)
        height = min(geometry_height, image_height)
        return image.smartcrop(width, height, interesting='entropy')

    def _scale(self, image, width, height):
        return image.thumbnail_image(width, height=height, size='force', no_rotate=True)

    def _crop(self, image, width, height, x_offset, y_offset):
        return image.crop(x_offset, y_offset, width, height)

    def _cropbox(self, image, x, y, x2, y2):
        return image.crop(x, y, x2 - x, y2 - y)

    def _rounded(self, image, r):
        svg = '<svg width="%d" height="%d"><rect width="100%%" height="100%%" rx="%d"/></svg>'
        mask = pyvips.Image.svgload_buffer((svg % (image.width, image.height, r)).encode())
        if image.hasalpha():
            image = image.extract_band(0, n=image.bands - 1)
        return image.bandjoin(mask[3])

    def _blur(self, image, radius):
        return image.gaussblur(radius)

    def _padding(self, image, geometry, options):
        background = list(bytes.fromhex(options['padding_color'].lstrip('#')))
        if image.bands < 3:
            background = [sum(background) / 3]
        if image.hasalpha():
            background.append(255)
        return image.gravity('centre', geometry[0], geometry[1],
                             extend='background', background=background)

    def _get_raw_data(self, image, format_, quality, image_info=None, progressive=False):
        options = {'keep': 'icc'}  # drop EXIF and XMP, keep the color profile
        if format_ in ('JPEG', 'WEBP', 'AVIF'):
            options['Q'] = quality
        if format_ == 'JPEG':
            options['interlace'] = progressive
        return image.write_to_buffer('.' + EXTENSIONS[format_], **options)
