************
Requirements
************
 
Base requirements
=================
- `Python`_ 3.10+
- `Django`_
- :ref:`kvstore-requirements`
- :ref:`image-library`

.. _kvstore-requirements:

Key Value Store
===============
sorl-thumbnail needs a Key Value Store for its operation. You can choose between
a **cached database** which requires no special installation to your normal
Django setup besides installing a proper cache like memcached **or** you can
setup **redis** which requires a little bit more work.

Since Django 4.0, the Redis cache can be configured at Django level, so any
alternative Key Value Store in sorl-thumbnail is now deprecated.

Cached DB
---------
All you need to use the cached database key value store is a database and `cache
<https://docs.djangoproject.com/en/stable/topics/cache/>`_ setup properly using
memcached. This cache needs to be really fast so **using anything else than
memcached is not recommended**.

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
command line tools. `pgmagick`_ are python bindings for `GraphicsMagick`_
(Magick++)`,

The `ImageMagick`_ based engine ``sorl.thumbnail.engines.convert_engine.Engine``
by default calls ``convert`` and ``identify`` shell commands. You can change the
paths to these tools by setting ``THUMBNAIL_CONVERT`` and ``THUMBNAIL_IDENTIFY``
respectively.  Note that you need to change these to use `GraphicsMagick`_ to
``/path/to/gm convert`` and ``/path/to/gm identify``.

To write AVIF, ImageMagick needs libheif with an AV1 encoder. On Debian and
Ubuntu that is the ``libheif-plugin-aomenc`` package. It is only a recommended
package, so ``--no-install-recommends`` leaves it out. Without it the convert
engine raises an error instead of saving a JPEG under an ``.avif`` name.

Python Imaging Library installation
-----------------------------------
Prerequisites:

- libjpeg
- zlib

Ubuntu 10.04 package installation::

    sudo apt-get install libjpeg62 libjpeg62-dev zlib1g-dev

Installing `Python Imaging Library`_ using pip::

    pip install Pillow

Watch the output for messages on what support got compiled in, you at least
want to see the following::

    --- JPEG support available
    --- ZLIB (PNG/ZIP) support available
    
to activate avif support install the plugin::

    pip install sorl-thumbnail[avif, pil]

pgmagick installation
---------------------
Prerequisites:

- GraphicsMagick
- Boost.Python

Ubuntu 10.04 package installation::

    sudo apt-get install libgraphicsmagick++-dev
    sudo apt-get install libboost-python1.40-dev

Fedora installation::

    yum install GraphicsMagick-c++-devel
    yum install boost-devel

Installing `pgmagick`_ using pip::

    pip install pgmagick

ImageMagick installation
------------------------
Ubuntu 10.04 package installation::

    sudo apt-get install imagemagick

Or if you prefer `GraphicsMagick`_::

    sudo apt-get install graphicsmagick

Wand installation
------------------------

Ubuntu installation::

    apt-get install libmagickwand-dev
    pip install Wand


.. _Python Imaging Library: https://python-pillow.org/
.. _ImageMagick: https://imagemagick.org/
.. _GraphicsMagick: http://www.graphicsmagick.org/
.. _redis: https://redis.io/
.. _redis-py: https://github.com/redis/redis-py
.. _Django: https://www.djangoproject.com/
.. _Python: https://www.python.org/
.. _pgmagick: https://pgmagick.readthedocs.io/
.. _wand: https://docs.wand-py.org
