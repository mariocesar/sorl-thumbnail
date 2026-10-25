import pyvips

from sorl.thumbnail.base import EXTENSIONS
from sorl.thumbnail.conf import settings
from sorl.thumbnail.engines.base import EngineBase
from sorl.thumbnail.parsers import parse_color


def background(color, image):
    """Band values of a padding_color for the image, without alpha"""
    rgb = list(parse_color(color))
    bands = image.bands - 1 if image.hasalpha() else image.bands
    return rgb if bands >= 3 else [sum(rgb) / 3]


class Engine(EngineBase):
    def create(self, image, geometry, options):
        """
        An animated source written as GIF is thumbnailed frame by frame,
        other formats take the first frame
        """
        height = image.get_page_height()
        frames = []
        for top in range(0, image.height, height):
            frame = image.crop(0, top, image.width, height)
            frames.append(super().create(frame, geometry, options))
            if options['format'] != 'GIF':
                break
        thumbnail = pyvips.Image.arrayjoin(frames, across=1).copy()
        # Always set, a frame keeps the source frame height in its metadata
        thumbnail.set_type(pyvips.GValue.gint_type, 'page-height', frames[0].height)
        return thumbnail

    def get_image(self, source):
        data = source.read()
        # Raise on a truncated source like PIL instead of filling it with grey
        image = pyvips.Image.new_from_buffer(data, '', fail_on='truncated')
        if image.get('vips-loader') == 'gifload_buffer':
            # Every frame stacked top to bottom, see create()
            image = pyvips.Image.new_from_buffer(data, '', fail_on='truncated', n=-1)
        return image

    def get_image_size(self, image):
        return image.width, image.get_page_height()

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

    def colorspace(self, image, geometry, options):
        if options['format'] == 'JPEG' and image.hasalpha():
            if settings.THUMBNAIL_FLATTEN and options.get('flatten') not in ('off', False):
                # Composite onto a background before JPEG drops the alpha channel, like PIL
                color = options['padding_color'] if options.get('padding') else '#ffffff'
                image = image.flatten(background=background(color, image))
            else:
                # Show the color stored under transparent pixels, like PIL
                image = image.extract_band(0, n=image.bands - 1)
        return super().colorspace(image, geometry, options)

    def _colorspace(self, image, colorspace):
        if colorspace == 'RGB':
            return image.colourspace('srgb')
        if colorspace == 'GRAY':
            return image.colourspace('b-w')
        return image

    def _remove_border(self, image, image_width, image_height):
        layers = [image]
        if image.hasalpha():
            # A border is plain on black and on white, whatever color is under transparent pixels
            layers = [image.flatten(background=0), image.flatten(background=255)]
        left, top, right, bottom = image_width, image_height, 0, 0
        for layer in layers:
            # The top left pixel is the border color
            x, y, width, height = layer.find_trim(background=layer.getpoint(0, 0))
            if width and height:  # else the layer is plain
                left, top = min(left, x), min(top, y)
                right, bottom = max(right, x + width), max(bottom, y + height)
        if left >= right or top >= bottom:  # the image is plain
            return image
        # Don't remove too much, like PIL
        max_x, max_y = int(image_width / 3.5), int(image_height / 3.5)
        left, top = min(left, max_x), min(top, max_y)
        right, bottom = max(right, image_width - max_x), max(bottom, image_height - max_y)
        return image.crop(left, top, right - left, bottom - top)

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
        if not image.hasalpha():
            return image.gaussblur(radius)
        # Weigh each pixel by its alpha, so the color under transparent pixels doesn't bleed in
        return image.premultiply().gaussblur(radius).unpremultiply().cast(image.format)

    def _padding(self, image, geometry, options):
        color = background(options['padding_color'], image)
        if image.hasalpha():
            color.append(255)
        return image.gravity('centre', geometry[0], geometry[1],
                             extend='background', background=color)

    def write(self, image, options, thumbnail):
        if options['format'] == 'JPEG' and image.hasalpha():
            # rounded adds alpha after colorspace, so composite it like flatten
            color = options['padding_color'] if options.get('padding') else '#ffffff'
            image = image.flatten(background=background(color, image))
        super().write(image, options, thumbnail)

    def _get_raw_data(self, image, format_, quality, image_info=None, progressive=False):
        options = {'keep': 'icc'}  # drop EXIF and XMP, keep the color profile
        if format_ in ('JPEG', 'WEBP', 'AVIF'):
            options['Q'] = quality
        if format_ == 'JPEG':
            options['interlace'] = progressive
        return image.write_to_buffer('.' + EXTENSIONS[format_], **options)
