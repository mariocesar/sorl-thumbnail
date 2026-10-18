from .base import *

DEMO_ENGINE = 'graphicsmagick'
THUMBNAIL_ENGINE = 'sorl.thumbnail.engines.convert_engine.Engine'
THUMBNAIL_PREFIX = 'cache/graphicsmagick/'
THUMBNAIL_DBM_FILE = str(MEDIA_ROOT / 'cache' / 'graphicsmagick-kvstore')
THUMBNAIL_CONVERT = 'gm convert'
THUMBNAIL_IDENTIFY = 'gm identify'
