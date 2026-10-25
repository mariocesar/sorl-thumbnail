********************
Installation & Setup
********************

Installation
============
First you need to make sure to read the :doc:`requirements`. To install
sorl-thumbnail::

    pip install sorl-thumbnail

Depending on the image library you choose, you may install one of these
instead. The quotes keep the shell from reading the brackets::

    pip install "sorl-thumbnail[pil]"
    pip install "sorl-thumbnail[pil,avif]"
    pip install "sorl-thumbnail[wand]"
    pip install "sorl-thumbnail[pgmagick]"
    pip install "sorl-thumbnail[vips]"

Setup
=====

.. highlight:: python

1. Add ``sorl.thumbnail`` to your ``settings.INSTALLED_APPS``.
2. Configure your ``settings``
3. If you are using the cached database key value store you need to sync the
   database::

    python manage.py migrate

4. If you serve with ASGI on Django 5.2 or 6.0, add the middleware so a source
   is downloaded once per request. WSGI, and ASGI from Django 6.1, need
   nothing, see :ref:`source-cache`::

    MIDDLEWARE = [
        ...
        'sorl.thumbnail.middleware.SourceCacheMiddleware',
    ]

