from demo.examples import MAGICK

from .base import *

DEMO_ENGINE = 'imagemagick'
THUMBNAIL_ENGINE = 'sorl.thumbnail.engines.convert_engine.Engine'
THUMBNAIL_PREFIX = 'cache/imagemagick/'
THUMBNAIL_DBM_FILE = str(MEDIA_ROOT / 'cache' / 'imagemagick-kvstore')

THUMBNAIL_CONVERT = MAGICK
THUMBNAIL_IDENTIFY = 'magick identify' if MAGICK == 'magick' else 'identify'
