from .base import *

DEMO_ENGINE = 'vips'
THUMBNAIL_ENGINE = 'sorl.thumbnail.engines.vips_engine.Engine'
THUMBNAIL_PREFIX = 'cache/vips/'
THUMBNAIL_DBM_FILE = str(MEDIA_ROOT / 'cache' / 'vips-kvstore')
