from .base import *

DEMO_ENGINE = 'wand'
THUMBNAIL_ENGINE = 'sorl.thumbnail.engines.wand_engine.Engine'
THUMBNAIL_PREFIX = 'cache/wand/'
THUMBNAIL_DBM_FILE = str(MEDIA_ROOT / 'cache' / 'wand-kvstore')
