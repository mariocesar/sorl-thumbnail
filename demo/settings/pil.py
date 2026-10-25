from .base import *

DEMO_ENGINE = 'pil'
THUMBNAIL_ENGINE = 'sorl.thumbnail.engines.pil_engine.Engine'
THUMBNAIL_PREFIX = 'cache/pil/'
THUMBNAIL_DBM_FILE = str(MEDIA_ROOT / 'cache' / 'pil-kvstore')
