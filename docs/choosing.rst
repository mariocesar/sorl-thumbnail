.. meta::
   :description: sorl-thumbnail, easy-thumbnails, django-imagekit, django-versatileimagefield and django-pictures compared, and which fits which project.

****************************
Choosing a thumbnail library
****************************

Django has several maintained libraries for making smaller versions of
uploaded images. They differ less in image quality, most of them resize with
Pillow, than in two questions: where you say what size you want, and when the
image is made. This page compares them on those questions. The facts come
from each project's README and PyPI page as of October 2026; check the
project for anything that matters to you.

.. list-table::
   :header-rows: 1
   :widths: 22 30 30 18

   * - Library
     - Where you define the size
     - When the image is made
     - Latest release
   * - `sorl-thumbnail`_
     - In the template tag or the Python call, any size and options
     - On first render, then served from a key-value store
     - 13.3.0, October 2026
   * - `easy-thumbnails`_
     - In the template tag or the Python call, or as a named alias in
       settings
     - On first render, then recorded in database tables
     - 2.10.1, August 2025
   * - `django-imagekit`_
     - As a spec in Python, usually a field on the model
     - On first access by default; ``generateimages`` makes them ahead
     - 6.1.1, September 2026
   * - `django-versatileimagefield`_
     - As attributes on the field, chained in the template
     - On demand, which can be turned off for production
     - 3.1, January 2024
   * - `django-pictures`_
     - As aspect ratios on the field; widths come from your grid breakpoints
     - When the file is saved, through Django's task framework
     - 2.0.1, October 2026

sorl-thumbnail
==============

The size, crop, format and quality are written where the image is used, in
a ``{% thumbnail %}`` tag or a ``get_thumbnail()`` call, so a template can ask
for a new size without a migration or a deploy. The thumbnail is made the
first time it is asked for, and a key-value store remembers it: later renders
read the store and never ask the storage whether the file exists, which is
what keeps S3 fast (:doc:`s3`). Resizing runs through a pluggable engine:
Pillow by default, or libvips, ImageMagick, GraphicsMagick, Wand or pgmagick.

Fits when you want to decide the size in the template and add sizes freely,
when media lives on a remote storage, or when you need an engine other than
Pillow, for PDF pages or CMYK sources for example. Less of a fit when you
want ``<picture>`` and ``srcset`` markup generated for you:
``THUMBNAIL_ALTERNATIVE_RESOLUTIONS`` and the ``resolution`` filter give 2x
versions, nothing more. Supports Django 5.2 to 6.1 and Python 3.10 and
later.

easy-thumbnails
===============

The closest to sorl-thumbnail in use. ``{% thumbnail profile.photo 50x50 crop %}``
outputs the URL, and ``get_thumbnailer(photo).get_thumbnail(options)`` does the
same in Python. Sizes can also be named once in ``THUMBNAIL_ALIASES`` and used
as ``{{ photo|thumbnail_url:'avatar' }}`` or, with its ``ThumbnailerImageField``,
as ``photo.avatar.url``. Options are implemented by processors you can
extend. It records sources and thumbnails in two database tables of its own,
and since 2.8.0 it can "thumbnail" SVG uploads by adjusting their size
attributes.

Fits when you like on-demand thumbnails but want a few named sizes shared by
the whole site, or when users upload SVG. README states Django 4.2 and
later; PyPI states Python 3.9 and later.

django-imagekit
===============

You define an image spec in Python: the processors to apply, the format and
the options. An ``ImageSpecField(source='avatar', processors=[ResizeToFill(100, 50)])``
on the model adds no database column and gives ``profile.avatar_thumbnail.url``.
``ProcessedImageField`` processes the upload and keeps only the result.
Specs can also be registered and used in templates with
``{% generateimage %}``, and the ``generateimages`` command makes every
registered spec ahead of time.

Fits when the sizes are part of the data model and you want them defined
once, in code, next to the field; and when you need processing beyond
resizing, since processors compose. Less of a fit when templates need to ask
for arbitrary sizes. PyPI states Python 3.9 and later.

django-versatileimagefield
==========================

A drop-in replacement for ``ImageField`` whose value exposes sizers and
filters as attributes: ``image.thumbnail.200x200``, ``image.crop.400x400``,
``image.filters.invert``, chainable. Its distinctive feature is the Primary
Point of Interest: an editor clicks the important point of the image in the
admin widget, and every crop keeps that point in frame. It integrates with
Django REST Framework to serve several sizes from one field. Images are made
on demand, and the docs explain how to turn that off and pre-create them for
production.

Fits when editors should choose what a crop keeps, or when an API has to
return several renditions of one image. The README lists Python 3.6 to 3.9
and Django 3.0 to 5.0, and the last release is from January 2024, so check
it against your versions before adopting it.

django-pictures
===============

Built for responsive images rather than thumbnails. A ``PictureField`` with
``aspect_ratios=["1/1", "16/9"]`` and the ``{% picture %}`` tag render a
``<picture>`` element with ``srcset`` and ``sizes`` computed from the grid
breakpoints and column counts you configure, in AVIF and WebP. The files are
made when the upload is saved, through Django's task framework, so no visitor
waits for a resize. It ships placeholders for local development, Django REST
Framework support, and a hook to hand processing to a CDN instead.

Fits when the goal is correct ``<picture>`` markup for every breakpoint and
the sizes follow a design grid. Less of a fit for one-off sizes decided in a
template. PyPI states Python 3.14 and later, and the task framework it uses
arrived in Django 6.0.

Deciding
========

- You want to write the size in the template and change it when the design
  changes: sorl-thumbnail or easy-thumbnails. sorl-thumbnail if media is on
  S3 or you need another image engine; easy-thumbnails if named aliases or
  SVG matter more.
- You want the sizes defined once, in code, with the model: django-imagekit,
  or django-versatileimagefield when editors should pick the point a crop
  keeps.
- You want responsive ``<picture>`` markup generated from a grid:
  django-pictures.

.. _sorl-thumbnail: https://github.com/mariocesar/sorl-thumbnail
.. _easy-thumbnails: https://github.com/SmileyChris/easy-thumbnails
.. _django-imagekit: https://github.com/matthewwithanm/django-imagekit
.. _django-versatileimagefield: https://github.com/respondcreate/django-versatileimagefield
.. _django-pictures: https://github.com/codingjoe/django-pictures
