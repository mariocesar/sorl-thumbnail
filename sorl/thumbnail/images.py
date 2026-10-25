import json
import os
import platform
import re
from contextlib import contextmanager
from contextvars import ContextVar
from functools import lru_cache
from urllib.error import URLError
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from django.conf import DEFAULT_STORAGE_ALIAS
from django.core.files.base import ContentFile, File
from django.core.files.storage import InvalidStorageError, Storage, storages
from django.utils.encoding import force_str
from django.utils.functional import LazyObject, empty

from sorl.thumbnail import default
from sorl.thumbnail.conf import settings
from sorl.thumbnail.default import storage as default_storage
from sorl.thumbnail.helpers import ThumbnailError, deserialize, get_module_class, tokey
from sorl.thumbnail.parsers import parse_geometry

url_pat = re.compile(r'^(https?|ftp):\/\/')

# The last source read, as bytes, kept for the rest of the request or source_cache() block
sources = ContextVar('sorl.thumbnail.sources', default=None)


@contextmanager
def source_cache():
    """Keep the last source read until the block ends, so each image is read once."""
    token = sources.set({})
    try:
        yield
    finally:
        sources.reset(token)


def open_source_cache(**kwargs):
    """request_started: a request is a source_cache() block."""
    sources.set({})


def close_source_cache(**kwargs):
    """request_finished"""
    cache = sources.get()
    if cache is not None:
        # Threads the request ran through sync_to_async share this dict
        cache.clear()
    sources.set(None)


@lru_cache
def get_or_create_storage(storage):
    try:
        return storages[storage]
    except InvalidStorageError:
        return get_module_class(storage)()


def serialize_image_file(image_file):
    if image_file.size is None:
        raise ThumbnailError('Trying to serialize an ``ImageFile`` with a '
                             '``None`` size.')
    data = {
        'name': image_file.name,
        'storage': image_file.serialize_storage(),
        'size': image_file.size,
    }
    return json.dumps(data)


def deserialize_image_file(s):
    data = deserialize(s)
    image_file = ImageFile(data['name'], get_or_create_storage(data['storage']))
    image_file.set_size(data['size'])
    return image_file


class BaseImageFile:
    size = []

    def exists(self):
        raise NotImplementedError()

    @property
    def width(self):
        return self.size[0]

    x = width

    @property
    def height(self):
        return self.size[1]

    y = height

    def is_portrait(self):
        return self.y > self.x

    @property
    def ratio(self):
        return float(self.x) / float(self.y)

    @property
    def url(self):
        raise NotImplementedError()

    src = url


class ImageFile(BaseImageFile):
    _size = None

    def __init__(self, file_, storage=None):
        if not file_:
            raise ThumbnailError('File is empty.')

        # figure out name
        if hasattr(file_, 'name'):
            self.name = file_.name
        else:
            self.name = force_str(file_)

        # TODO: Add a customizable naming method as a signal

        # Remove query args from names. Fixes cache and signature arguments
        # from third party services, like Amazon S3 and signature args.
        if settings.THUMBNAIL_REMOVE_URL_ARGS:
            self.name = self.name.split('?')[0]

        # Support for relative protocol urls
        if self.name.startswith('//'):
            self.name = 'http:' + self.name

        # figure out storage
        if storage is not None:
            self.storage = storage
        elif hasattr(file_, 'storage'):
            self.storage = file_.storage
        elif url_pat.match(self.name):
            self.storage = UrlStorage()
        else:
            self.storage = default_storage

        if hasattr(self.storage, 'location'):
            location = self.storage.location
            if not self.storage.location.endswith("/"):
                location += "/"
            if self.name.startswith(location):
                self.name = self.name[len(location):]

    def __str__(self):
        return self.name

    def exists(self):
        return self.storage.exists(self.name)

    def set_size(self, size=None):
        # set the size if given
        if size is not None:
            pass
        # Don't try to set the size the expensive way if it already has a
        # value.
        elif self._size is not None:
            return
        elif hasattr(self.storage, 'image_size'):
            # Storage backends can implement ``image_size`` method that
            # optimizes this.
            size = self.storage.image_size(self.name)
        else:
            # This is the worst case scenario
            image = default.engine.get_image(self)
            size = default.engine.get_image_size(image)
            if self.flip_dimensions(image):
                size = list(size)
                size.reverse()
        self._size = list(size)

    def flip_dimensions(self, image):
        """
        Do not manipulate image, but ask engine whether we'd be doing a 90deg
        rotation at some point.
        """
        return default.engine.flip_dimensions(image)

    @property
    def size(self):
        return self._size

    @property
    def url(self):
        return self.storage.url(self.name)

    def read(self):
        cache = sources.get()
        key = (self.storage, self.name)
        data = cache.get(key) if cache is not None else None
        if data is None:
            f = self.storage.open(self.name)
            try:
                data = f.read()
            finally:
                f.close()
            if cache is not None:
                # One entry: a filter, the tag and every size of one image share it
                cache.clear()
                cache[key] = data
        return data

    def forget(self):
        """Drop the kept read of this file, so the next read goes to the storage."""
        cache = sources.get()
        if cache:
            cache.pop((self.storage, self.name), None)

    def write(self, content):
        if not isinstance(content, File):
            content = ContentFile(content)

        self._size = None
        self.forget()
        self.name = self.storage.save(self.name, content)

        return self.name

    def delete(self):
        self.forget()
        return self.storage.delete(self.name)

    def serialize_storage(self, use_backend_name=False):
        storage = self.storage
        if isinstance(storage, LazyObject):
            # if storage is wrapped in a lazy object we need to get the real
            # thing.
            if storage._wrapped is empty:
                storage._setup()
            storage = storage._wrapped
        cls = storage.__class__
        backend = f"{cls.__module__}.{cls.__name__}"
        if use_backend_name:
            return backend
        # Resolve the alias by instance, not by class: several aliases may share
        # a backend class and differ only in OPTIONS (#806).
        for alias, params in storages.backends.items():
            if params.get("BACKEND") == backend and storages[alias] is storage:
                return alias
        return backend

    @property
    def key(self):
        storage = self.serialize_storage()
        # The default and thumbnail storages keep their pre-13 keys (#805).
        if storage in (DEFAULT_STORAGE_ALIAS, settings.THUMBNAIL_STORAGE):
            storage = self.serialize_storage(use_backend_name=True)
        return tokey(self.name, storage)

    def serialize(self):
        return serialize_image_file(self)


class DummyImageFile(BaseImageFile):
    def __init__(self, geometry_string):
        self.size = parse_geometry(
            geometry_string,
            settings.THUMBNAIL_DUMMY_RATIO,
        )

    def exists(self):
        return True

    @property
    def url(self):
        return settings.THUMBNAIL_DUMMY_SOURCE % (
            {'width': self.x, 'height': self.y}
        )


class UrlStorage(Storage):
    def normalize_url(self, url, charset="utf-8"):
        # Convert URL to ASCII before processing
        url = url.encode(charset, errors="ignore")
        url = url.decode("ascii", errors="ignore")
        scheme, netloc, path, qs, anchor = urlsplit(url)

        path = quote(path, b"/%")
        # Only escape characters not allowed in a query (RFC 3986). Escaping
        # "+" and "/" breaks signed URLs, whose signatures often contain them.
        # "%" is kept so already-encoded values aren't encoded twice.
        qs = quote(qs, b"!$&'()*+,;=:@/?~%")

        return urlunsplit((scheme, netloc, path, qs, anchor))

    def open(self, name, mode='rb'):
        url = self.normalize_url(name)
        python_version = platform.python_version_tuple()[0]
        user_agent = "python-urllib{python_version}/0.6".format(python_version=python_version)
        req = Request(url, headers={"User-Agent": user_agent})
        return urlopen(req, timeout=settings.THUMBNAIL_URL_TIMEOUT)

    def exists(self, name):
        try:
            self.open(name)
        except URLError:
            return False
        return True

    def url(self, name):
        return name

    def delete(self, name):
        pass


def delete_all_thumbnails():
    storage = default.storage
    path = settings.THUMBNAIL_PREFIX

    def walk(path):
        dirs, files = storage.listdir(path)
        for f in files:
            storage.delete(os.path.join(path, f))
        for d in dirs:
            directory = os.path.join(path, d)
            walk(directory)
            try:
                full_path = storage.path(directory)
            except Exception:
                continue
            os.rmdir(full_path)

    walk(path)
