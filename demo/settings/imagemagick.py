import shutil

from .base import *

DEMO_ENGINE = 'imagemagick'
THUMBNAIL_ENGINE = 'sorl.thumbnail.engines.convert_engine.Engine'
THUMBNAIL_PREFIX = 'cache/imagemagick/'
THUMBNAIL_DBM_FILE = str(MEDIA_ROOT / 'cache' / 'imagemagick-kvstore')

# ImageMagick 7 has magick, 6 has convert and identify
THUMBNAIL_CONVERT = 'magick' if shutil.which('magick') else 'convert'
THUMBNAIL_IDENTIFY = 'magick identify' if shutil.which('magick') else 'identify'
