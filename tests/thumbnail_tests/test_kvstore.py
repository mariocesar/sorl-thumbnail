import threading
import unittest

from django.test import TestCase

from sorl.thumbnail.kvstores.cached_db_kvstore import KVStore
from sorl.thumbnail.models import KVStore as KVStoreModel


class KVStoreTestCase(unittest.TestCase):
    @unittest.skipIf(threading is None, 'Test requires threading')
    def test_cache_backend(self):
        kv = KVStore()
        cache_backends = []

        def thread_cache_backend():
            cache_backends.append(kv.cache)

        for _ in range(2):
            t = threading.Thread(target=thread_cache_backend)
            t.start()
            t.join()

        # Cache backend for each thread needs to be unique
        self.assertNotEqual(cache_backends[0], cache_backends[1])


class CachedDbKVStoreTestCase(TestCase):
    def test_set_raw_is_one_statement(self):
        kv = KVStore()
        key = 'sorl-thumbnail||test||upsert'
        with self.assertNumQueries(1):
            kv._set_raw(key, 'first')
        with self.assertNumQueries(1):
            kv._set_raw(key, 'second')
        self.assertEqual(KVStoreModel.objects.get(key=key).value, 'second')
        self.assertEqual(kv._get_raw(key), 'second')
