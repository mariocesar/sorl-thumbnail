.. meta::
   :description: Install sorl-thumbnail, add it to INSTALLED_APPS and make your first thumbnail with the {% thumbnail %} template tag.

****************************************
How do I make thumbnails in Django?
****************************************

With sorl-thumbnail you write the size you want in the template. The
thumbnail is made the first time the page renders, saved in your media
storage and reused on every render after that. This page goes from
``pip install`` to a thumbnail on a page.

1. Install
==========

::

    pip install "sorl-thumbnail[pil]"

This installs sorl-thumbnail and Pillow, the image library it uses by
default. For WebP and AVIF, or for another image library such as ImageMagick
or libvips, see :doc:`requirements`.

2. Add the app
==============

In ``settings.py``::

    INSTALLED_APPS = [
        ...
        'sorl.thumbnail',
    ]

Then create its table. sorl-thumbnail keeps a record of every thumbnail it
has made in your database, read through your cache::

    python manage.py migrate

3. Use the tag
==============

In a template::

    {% load thumbnail %}

    {% thumbnail item.image "200x200" crop="center" as im %}
        <img src="{{ im.url }}" width="{{ im.width }}" height="{{ im.height }}" alt="">
    {% endthumbnail %}

``item.image`` can be an ``ImageField`` or ``FileField``, a path inside your
``MEDIA_ROOT``, or the URL of an image. ``"200x200"`` is the size in pixels.
``crop="center"`` cuts the image so it fills the whole box; without ``crop``
the image is scaled to fit inside the box and keeps its proportions. ``im``
is the thumbnail, with ``url``, ``width`` and ``height``.

The file is written under ``cache/`` in your media storage and served by
your media URL like any upload. The first render of a page makes its
thumbnails, so that visit is slower. After that no image work and no storage
request happens.

What next
=========

- Sizes, cropping, formats and the other options: :doc:`template`.
- Thumbnails in Python code and in the admin: :doc:`examples`.
- Every setting: :doc:`reference/settings`.
- You replaced an image and the thumbnail did not change: :doc:`operation`.
- Media on Amazon S3 or another remote storage: :doc:`s3`.
- Nothing shows up: set ``THUMBNAIL_DEBUG = True`` in development, so the
  tag raises the error instead of logging it and rendering nothing.
