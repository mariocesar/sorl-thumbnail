.. meta::
   :description: Thumbnails for Django made in the template with Pillow, libvips or ImageMagick, stored on any Django storage including Amazon S3.

*************************************
sorl-thumbnail: thumbnails for Django
*************************************

You write the size in the template, or ask for it in Python, and
sorl-thumbnail makes the thumbnail on first use, saves it on your media
storage and remembers it in a key-value store, so later renders cost no image
work and no storage request. It resizes with Pillow by default, or with
libvips, ImageMagick, GraphicsMagick, Wand or pgmagick, and writes to any
Django storage, Amazon S3 included.

New here? Start with :doc:`quickstart`.

.. toctree::
   :maxdepth: 2

   quickstart
   installation
   requirements
   template
   examples
   management
   logging
   operation
   s3
   troubleshooting
   reference/index
   choosing
   contributing


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
