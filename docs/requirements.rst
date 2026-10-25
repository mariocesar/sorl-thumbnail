************
Requirements
************
 
Base requirements
=================
- `Python`_ 3.10+
- `Django`_ 5.2, 6.0 or 6.1, following the `Django supported versions policy`_
- :ref:`kvstore-requirements`
- :ref:`image-library`

.. _kvstore-requirements:

Key Value Store
===============
sorl-thumbnail needs a Key Value Store for its operation. You can choose between
a **cached database** which requires no special installation to your normal
Django setup besides installing a proper cache like Redis or memcached **or** you can
setup **redis** which requires a little bit more work.

Since Django 4.0, the Redis cache can be configured at Django level, so any
alternative Key Value Store in sorl-thumbnail is now deprecated.

Cached DB
---------
All you need to use the cached database key value store is a database and a
`cache <https://docs.djangoproject.com/en/stable/topics/cache/>`_. Use a fast
cache that every process shares, Redis or memcached; Django ships a backend
for each. The local memory cache works but is one per process, and the dummy
cache sends every lookup to the database.

Redis
-----
Redis is a fast key value store also suited for the job. To use the `redis`_ key
value store you first need to install the `redis server
<https://redis.io/>`_.  After that install the `redis client
<https://github.com/redis/redis-py/>`_::

    pip install redis


.. _image-library:

Image Library
=============
You need to have an image library installed. sorl-thumbnail ships with support
for `Python Imaging Library`_, `pgmagick`_, `ImageMagick`_ (or `GraphicsMagick`)
command line tools and `libvips`_. `pgmagick`_ are python bindings for
`GraphicsMagick`_ (Magick++)`,

The `ImageMagick`_ based engine ``sorl.thumbnail.engines.convert_engine.Engine``
by default calls ``convert`` and ``identify`` shell commands. You can change the
paths to these tools by setting ``THUMBNAIL_CONVERT`` and ``THUMBNAIL_IDENTIFY``
respectively.  Note that you need to change these to use `GraphicsMagick`_ to
``/path/to/gm convert`` and ``/path/to/gm identify``.

To write AVIF, ImageMagick needs libheif with an AV1 encoder. On Debian and
Ubuntu that is the ``libheif-plugin-aomenc`` package. It is only a recommended
package, so ``--no-install-recommends`` leaves it out. Without it the convert
engine raises an error instead of saving a JPEG under an ``.avif`` name.

Pillow installation
-------------------
`Pillow`_ ships binary wheels with JPEG, PNG, GIF and WebP support, so no
system package is needed::

    pip install "sorl-thumbnail[pil]"

For AVIF add the ``pillow-avif-plugin`` package through the ``avif`` extra::

    pip install "sorl-thumbnail[pil,avif]"

pgmagick installation
---------------------
Prerequisites:

- GraphicsMagick
- Boost.Python

Debian and Ubuntu package installation::

    sudo apt-get install libgraphicsmagick++1-dev libboost-python-dev

Fedora installation::

    sudo dnf install GraphicsMagick-c++-devel boost-devel

Installing `pgmagick`_ using pip::

    pip install pgmagick

ImageMagick installation
------------------------
Debian and Ubuntu package installation::

    sudo apt-get install imagemagick

Or if you prefer `GraphicsMagick`_::

    sudo apt-get install graphicsmagick

Wand installation
------------------------

Ubuntu installation::

    apt-get install libmagickwand-dev
    pip install Wand

libvips installation
--------------------

Installing `pyvips`_ with libvips as a binary wheel, no system package needed::

    pip install sorl-thumbnail[vips]

To use the libvips from your system instead::

    sudo apt-get install libvips-dev
    pip install pyvips

Either way the engine refuses PDF and SVG sources, because it blocks the
loaders libvips doesn't test against hostile files. Use the convert engine for
those.

The engine needs libvips 8.15 or later. Ubuntu 24.04 and Debian 13 ship it,
Debian 12 does not.


.. _Python Imaging Library: https://python-pillow.org/
.. _Pillow: https://pillow.readthedocs.io/
.. _Django supported versions policy: https://www.djangoproject.com/download/#supported-versions
.. _ImageMagick: https://imagemagick.org/
.. _GraphicsMagick: http://www.graphicsmagick.org/
.. _redis: https://redis.io/
.. _redis-py: https://github.com/redis/redis-py
.. _Django: https://www.djangoproject.com/
.. _Python: https://www.python.org/
.. _pgmagick: https://pgmagick.readthedocs.io/
.. _wand: https://docs.wand-py.org
.. _libvips: https://www.libvips.org/
.. _pyvips: https://libvips.github.io/pyvips/
