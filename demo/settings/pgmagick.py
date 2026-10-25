from .base import *

DEMO_ENGINE = 'pgmagick'
THUMBNAIL_ENGINE = 'sorl.thumbnail.engines.pgmagick_engine.Engine'
THUMBNAIL_PREFIX = 'cache/pgmagick/'
THUMBNAIL_DBM_FILE = str(MEDIA_ROOT / 'cache' / 'pgmagick-kvstore')
