********
Settings
********

.. highlight:: python

``THUMBNAIL_DEBUG``
===================

- Default: ``False``

When set to ``True`` the ``ThumbnailNode.render`` method can raise errors.
Django recommends that tags never raise errors in the ``Node.render`` method
but since sorl-thumbnail is such a complex tag we will need to have more
debugging available.


``THUMBNAIL_BACKEND``
=====================

- Default: ``'sorl.thumbnail.base.ThumbnailBackend'``

This is the entry point for generating thumbnails, you probably want to keep the
default one but just in case you would like to generate thumbnails filenames
differently or need some special functionality you can override this and use
your own implementation.


``THUMBNAIL_KVSTORE``
=====================

- Default: ``'sorl.thumbnail.kvstores.cached_db_kvstore.KVStore'``

.. deprecated:: 12.11.0

    Using any other KVStore than the Cached Db KVStore is deprecated.
    Please configure the cache that suits your use case at Django level and set
    this cache alias in ``THUMBNAIL_CACHE``.

.. versionchanged:: 13.4.0

    The DynamoDB store, ``sorl.thumbnail.kvstores.dynamodb_kvstore.KVStore``,
    was removed. It was built on boto 2 and could not be imported on any
    supported Python. The default Cached DB store works with any Django cache,
    including one backed by DynamoDB.

sorl-thumbnail needs a Key Value Store to :doc:`/operation`.
sorl-thumbnail ships with support for three Key Value Stores:

Cached DB
---------
``sorl.thumbnail.kvstores.cached_db_kvstore.KVStore``. This is the default and
preferred Key Value Store. It uses the cache configured at the Django project
level.

Features
^^^^^^^^
* Fast persistent storage
* First query uses database which is slow. Successive queries are cached and if
  you use memcached this is very fast.
* Easy to transfer data between environments since the data is in the default
  database.
* If you get the database and fast cache out of sync there could be problems.

Redis
-----
From Django 4.0, you can configure a Redis cache at Django level and then use
the Cached DB store while using the configured cache alias in the
``THUMBNAIL_CACHE`` setting. Therefore the Redis store in sorl-thumbnail and its
associated ``THUMBNAIL_REDIS*`` settings maybe removed in the future.

``sorl.thumbnail.kvstores.redis_kvstore.KVStore``. It requires you to install a
Redis server as well as a `redis python client
<https://github.com/andymccurdy/redis-py/>`_.

Features
^^^^^^^^
* Fast persistent storage
* More dependencies
* Requires a little extra work to transfer data between environments

Dbm
---
``sorl.thumbnail.kvstores.dbm_kvstore.KVStore``. A simple Key Value Store has no
dependencies outside the standard Python library and uses the DBM modules to
store the data.

Features
^^^^^^^^
* No external dependencies, besides the standard library
* No extra components required, e.g., database or cache
* Specially indicated for local development environments


``THUMBNAIL_KEY_DBCOLUMN``
==========================

- Default ``'key'``

Since MSSQL reserved the ``key`` name for db columns you can change this to
something else using this setting.


``THUMBNAIL_ENGINE``
====================

- Default: ``'sorl.thumbnail.engines.pil_engine.Engine'``

This is the processing class for sorl-thumbnail. It does all the resizing,
cropping or whatever processing you want to perform. sorl-thumbnail ships with
five engines:

PIL
---
``'sorl.thumbnail.engines.pil_engine.Engine'``. This is the default engine
because it is what most people have installed already. Features:

* Easy to install
* Produces good quality images but not the best
* It is fast

Pgmagick
--------
``'sorl.thumbnail.engines.pgmagick_engine.Engine'``. Pgmagick uses `Graphics
<http://www.graphicsmagick.org/>`_. Features:

* Not easy to install unless on linux, very slow to compile
* Produces high quality images
* It is a tad slow
* Can handle CMYK sources

ImageMagick / GraphicsMagick
----------------------------
``'sorl.thumbnail.engines.convert_engine.Engine'``. This engine uses the
ImageMagick ``convert`` or  GraphicsMagic ``gm convert`` command. Features:

* Easy to install
* Produces high quality images
* It is pretty fast
* Can handle CMYK sources
* It is a command line command, that is less than ideal,

Wand
----------------------------
``'sorl.thumbnail.engines.wand_engine.Engine'``. This engine uses `Wand
<https://docs.wand-py.org/>`_, a ctypes-based simple ImageMagick binding for Python. 
Features:

* Easy to install
* Produces high quality images
* Can handle CMYK sources

libvips
-------
``'sorl.thumbnail.engines.vips_engine.Engine'``. This engine uses `libvips
<https://www.libvips.org/>`__ through `pyvips
<https://libvips.github.io/pyvips/>`_. ``pip install sorl-thumbnail[vips]``
installs pyvips with libvips as a binary wheel for Linux, macOS and Windows,
or run ``pip install pyvips`` to use the libvips from your system packages.
Features:

* Easy to install
* Produces high quality images
* It is fast
* Can handle CMYK sources
* Reads JPEG, PNG, GIF, WebP, TIFF and AVIF sources
* Keeps animated GIFs animated when the thumbnail format is ``GIF``

libvips runs inside the Django process, like Pillow. A crash on a broken or
hostile image takes the worker down with it. Like Pillow, it refuses sources
over 178,956,970 pixels, so a small upload that unpacks into a huge image can't
use up the memory.

sorl-thumbnail loads pyvips with the first thumbnail, not when Django starts,
and libvips starts its threads then. With gunicorn's ``--preload``, make no
thumbnails in the master before it forks the workers, or the workers will hang.

The engine blocks the loaders libvips doesn't test against hostile files. On
libvips 8.18 they include PDF, SVG, ImageMagick and MATLAB, so those sources
are refused and ``is_valid_image`` returns ``False`` for them. The block applies
to the whole process, so other pyvips code in your site can't use those
loaders either. For PDF and SVG sources use the convert engine, which runs
ImageMagick in a separate process and stops it after
``THUMBNAIL_COMMAND_TIMEOUT``.

The engine needs libvips 8.15 or later. Ubuntu 24.04 and Debian 13 ship it,
Debian 12 does not.

For long running workers on glibc Linux, libvips recommends jemalloc, see the
`libvips developer checklist
<https://www.libvips.org/API/current/developer-checklist.html>`_. Its operation
cache is off, see ``THUMBNAIL_VIPS_CACHE_MAX``.

It differs from the PIL engine in a few ways:

* ``padding_color`` must be a hex color such as ``#f00`` or ``#ff0000``. A
  color name such as ``red`` raises ``ThumbnailParseError``.
* Resizing uses the libvips resampler, so pixels differ slightly.
* ``colorspace="GRAY"`` keeps the alpha channel of a transparent source, and
  the gray values come from the libvips color model.
* ``crop="smart"`` picks the area with the libvips entropy measure, so it may
  keep a different part of the image. It always returns the requested size.
* ``remove_border`` cuts the rows and columns that match the top left pixel's
  color, where PIL cuts the strips with almost no detail. The two can differ by
  a few pixels.
* A truncated source raises an error when the thumbnail is made, and
  ``is_valid_image`` decodes the whole file, so a form rejects a truncated
  upload.

``THUMBNAIL_CONVERT``
=====================

- Default ``'convert'``

Path to convert command, use ``'gm convert'`` for GraphicsMagick.
Only applicable for the convert Engine.


``THUMBNAIL_IDENTIFY``
======================

- Default ``'identify'``

Path to identify command, use ``'gm identify'`` for GraphicsMagick.
Only applicable for the convert Engine.


``THUMBNAIL_COMMAND_TIMEOUT``
=============================

- Default ``60``

Seconds a ``convert`` or ``identify`` call may run before it is killed and
``EngineError`` is raised. Raise it if large sources or high ``density`` values
legitimately take longer. ``None`` lets a call run as long as it takes, so a
malformed or hostile image can keep a worker busy indefinitely. Only applicable
for the convert Engine. The vips engine runs libvips inside the Django process,
so it has no timeout.


``THUMBNAIL_VIPS_CACHE_MAX``
============================

- Default ``0``

How many operations the vips engine keeps in the libvips operation cache. The
cache helps a program that repeats the same operation on the same image, which
sorl-thumbnail doesn't do: every thumbnail reads its source again. With the
cache on, a worker used more memory and was not faster. libvips' own default
is ``100``.

The engine sets it when it makes the first thumbnail, with
``pyvips.cache_set_max()``. The cache belongs to the whole process, so any
other pyvips code in your site gets the same limit. Only applicable for the
vips engine.


``THUMBNAIL_FLATTEN``
=====================

- Default: ``False``

When ``True`` a transparent source written as JPEG gets a solid background
instead of the color stored under its transparent pixels, which is usually
black. The background is white, or the padding color when the thumbnail is
padded.

The PIL, wand and vips engines only flatten thumbnails written as JPEG. The
convert engine adds ``-flatten`` to the convert command whatever the format, so
PNG, GIF and WEBP thumbnails lose their transparency too. Every other engine
ignores this setting. Pass ``flatten=False`` or ``flatten="off"`` as a
thumbnail option to turn it off for one thumbnail.


``THUMBNAIL_STORAGE``
=====================

- Default: ``default``

The storage to use for the generated thumbnails, as an alias from the Django
``STORAGES`` setting.
Optionally accepts a path to a Storage subclass.


``THUMBNAIL_REDIS_URL``
=======================

The Redis database URL to connect as used by `redis-py <https://redis-py.readthedocs.io/en/latest/#redis.Redis.from_url>`_

When specified, other ``THUMBNAIL_REDIS_*`` connection settings will be ignored.


``THUMBNAIL_REDIS_DB``
======================

- Default: ``0``

The Redis database. Only applicable for the Redis Key Value Store


``THUMBNAIL_REDIS_PASSWORD``
============================

- Default: ``''``

The password for Redis server. Only applicable for the Redis Key Value Store


``THUMBNAIL_REDIS_HOST``
========================

- Default: ``'localhost'``

The host for Redis server. Only applicable for the Redis Key Value Store


``THUMBNAIL_REDIS_PORT``
========================

- Default: ``6379``

The port for Redis server. Only applicable for the Redis Key Value Store


``THUMBNAIL_REDIS_TIMEOUT``
===========================

- Default: ``3600 * 24 * 365 * 10``

Cache timeout for Redis Key Value Store in seconds. You should probably keep this 
at maximum or ``None``.


``THUMBNAIL_DBM_FILE``
======================

- Default: ``thumbnail_kvstore``

Filename of the DBM database. Depending on the DBM engine selected by your
Python installation, this will be used as a prefix because multiple files may be
created. This can be an absolute path.


``THUMBNAIL_DBM_MODE``
======================

- Default: ``0o644``

Permission bits to use when creating new DBM files


``THUMBNAIL_CACHE_TIMEOUT``
===========================

- Default: ``3600 * 24 * 365 * 10``

Cache timeout for Cached DB Key Value Store in seconds. You should probably keep this 
at maximum or ``None`` if your caching backend can handle that as infinite.
Only applicable for the Cached DB Key Value Store.


``THUMBNAIL_CACHE``
===================

- Default: ``'default'``

Django configured cache alias to use for Cached DB Key Value Store. Defaults to
the ``'default'`` cache but you can use any other cache configured in the Django
project.

- ``https://docs.djangoproject.com/en/stable/topics/cache/``


``THUMBNAIL_KEY_PREFIX``
========================

- Default: ``'sorl-thumbnail'``

Key prefix used by the key value store.


``THUMBNAIL_PREFIX``
====================

- Default: ``'cache/'``

The generated thumbnails filename prefix.


``THUMBNAIL_FORMAT``
====================

- Default: ``'JPEG'``

Default image format, supported formats are: ``'JPEG'``, ``'PNG'``, ``'GIF'``, ``'WEBP'``, ``'AVIF'``. This also implicitly
sets the filename extension. This can be overridden by individual options.

With the PIL engine, an animated source stays animated when the format is
``'GIF'``, for example with ``format='GIF'`` or ``THUMBNAIL_PRESERVE_FORMAT``.
Every frame is thumbnailed, so the cost grows with the number of frames. If you
accept uploaded images, consider limiting the frame count when validating them,
for example with Pillow's ``Image.open(file).n_frames``.


``THUMBNAIL_PRESERVE_FORMAT``
=============================

- Default: ``False``

If ``True``, the format of the input file will be preserved. If ``False``,
``THUMBNAIL_FORMAT`` will be used.


``THUMBNAIL_COLORSPACE``
========================

- Default: ``'RGB'``

Default thumbnail color space, engines are required to implement: ``'RGB'``,
``'GRAY'`` Setting this to None will keep the original color space. This can be
overridden by individual options.


``THUMBNAIL_UPSCALE``
=====================

- Default: ``True``

Should we upscale by default? ``True`` means we upscale images by default.
``False`` means we don't. This can be overridden by individual options.


``THUMBNAIL_QUALITY``
=====================

- Default: ``95``

Default thumbnail quality. A value between 0 and 100 is allowed. This can be
overridden by individual options.

``THUMBNAIL_PROGRESSIVE``
=========================

- Default: ``True``

Saves jpeg thumbnails as progressive jpegs. This can be overridden by individual
options.


``THUMBNAIL_ORIENTATION``
=========================

- Default: ``True``

Orientate the thumbnail with respect to source EXIF orientation tag


``THUMBNAIL_DUMMY``
===================

- Default: ``False``

This is a very powerful option which came from real world frustration. The use
case is when you want to do development on a deployed project that has image
references in its database. Instead of downloading all the image files from the
server hosting the deployed project and all its thumbnails we just set this
option to ``True``. This will generate placeholder images for all thumbnails
missing input source.


``THUMBNAIL_DUMMY_SOURCE``
==========================

- Default ``https://dummyimage.com/%(width)sx%(height)s``

The URL of the placeholder image. ``%(width)s`` and ``%(height)s`` are
replaced with the thumbnail size. Another service that works the same way:

- ``https://placehold.co/%(width)sx%(height)s``


``THUMBNAIL_DUMMY_RATIO``
=========================

- Default: ``1.5``

This value sets an image ratio to all thumbnails that are not defined by width
**and** height since we cannot determine from the file input (since we don't
have that).

``THUMBNAIL_ALTERNATIVE_RESOLUTIONS``
=====================================

- Default: ``[]``
- Example: ``[1.5, 2]``

This value enables creation of additional high-resolution ("Retina") thumbnails
for every thumbnail. Resolution multiplicators, e.g. value 2 means for every thumbnail
of regular size x\*y, additional thumbnail of 2x\*2y size is created.

``THUMBNAIL_FILTER_WIDTH``
==========================

- Default: ``500``

This value sets the width of thumbnails inserted when running filters one texts
that regex replaces references to images with thumbnails.

``THUMBNAIL_URL_TIMEOUT``
=========================

- Default: ``None``

This value sets the timeout value in seconds when retrieving a source image from a URL. 
If no timeout value is specified, it will wait indefinitely for a response.

.. _force-overwrite:

``THUMBNAIL_FORCE_OVERWRITE``
=============================

- Default: ``False``

What to do when a thumbnail is missing from the key-value store. By default
sorl-thumbnail asks the storage whether the file already exists. If it does,
the file is kept and only its size is read back into the store; if it does not,
the thumbnail is generated. With ``True`` the ``exists()`` call is skipped and
the thumbnail is always generated and saved again.

Thumbnails that are in the key-value store never touch the storage, so this
setting only matters while the store is being filled or after it is cleared.

Set it to ``True`` when ``exists()`` is slow or expensive in your storage, or
when you want a cleared store to regenerate every file. Do not set it for
Amazon S3 with django-storages: there ``exists()`` is one ``HEAD`` request,
while regenerating means downloading the full-size source, resizing it and
uploading the result. Also make sure your storage overwrites files. Django's
``FileSystemStorage`` with its default ``allow_overwrite=False``, or S3 with
``AWS_S3_FILE_OVERWRITE = False``, saves the regenerated thumbnail under a new
name and leaves the old file behind.

``THUMBNAIL_REMOVE_URL_ARGS``
=============================

- Default: ``True``

This value sets if URL arguments will be removed from the source URL of the image we want to generate a thumbnail of. E.g. if our source image is at ``<domain>/picture?height=600&width=600`` a ``True`` value would instead attempt to generate a thumbnail from ``<domain>/picture``.
