from .base import *

DEMO_ENGINE = 'vipsthumbnail'
THUMBNAIL_ENGINE = 'sorl.thumbnail.engines.vipsthumbnail_engine.Engine'
THUMBNAIL_PREFIX = 'cache/vipsthumbnail/'
THUMBNAIL_DBM_FILE = str(MEDIA_ROOT / 'cache' / 'vipsthumbnail-kvstore')
