import os

from .default import *


THUMBNAIL_KVSTORE = 'sorl.thumbnail.kvstores.redis_kvstore.KVStore'
THUMBNAIL_REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
