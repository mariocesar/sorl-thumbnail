.. meta::
   :description: Fixes for sorl-thumbnail problems: a tag that renders nothing, thumbnails that do not update, black backgrounds, engine errors and slow S3.

***************
Troubleshooting
***************

Each section is a symptom, what causes it and what to do.

The tag renders nothing
=======================

With ``THUMBNAIL_DEBUG`` at its default ``False`` the tag never breaks a
page. An error is logged to the ``sorl.thumbnail`` logger and the tag
renders its ``{% empty %}`` block, or nothing. In development set::

    THUMBNAIL_DEBUG = True

and the error is raised where it happens, so Django's debug page shows it.
To see errors in the console instead, give the logger a handler, see
:doc:`logging`. The usual causes: the source file is missing from the
storage, the image library cannot read it, or an option is not supported by
your engine (below).

Invalid block tag 'endthumbnail'
================================

The tag has two forms. With ``as im`` it has a body and needs
``{% endthumbnail %}``. Without ``as`` it outputs the URL and takes no
closing tag, so an ``{% endthumbnail %}`` after it is an unknown tag::

    {% thumbnail item.image "100x100" as im %}<img src="{{ im.url }}">{% endthumbnail %}

    <img src="{% thumbnail item.image "100x100" %}">

I replaced the image and the thumbnail did not change
=====================================================

Once a thumbnail is in the key-value store, sorl-thumbnail never looks at
the source again, see :doc:`operation`. After replacing a source tell it::

    from sorl.thumbnail import delete

    delete(item.image, delete_file=False)

That removes the record and the thumbnail files, and the next render makes
them from the new file. Deleting the source through ``delete(item.image)``
does the same and removes the source file. For files deleted outside Django,
``manage.py thumbnail cleanup`` drops the records of sources that no longer
exist.

A transparent image has a black background
==========================================

The thumbnail is a JPEG, the default format, and JPEG has no transparency.
What shows is the color stored under the transparent pixels, usually black.
Either keep the transparency::

    {% thumbnail item.image "100x100" format="PNG" as im %}

or ``THUMBNAIL_PRESERVE_FORMAT = True`` to write PNG sources as PNG, or set
``THUMBNAIL_FLATTEN = True`` for a white background behind JPEG thumbnails.
Thumbnails made before the change keep the black background until you
delete them with ``manage.py thumbnail clear_delete_all``.

I changed a setting and the old thumbnails look the same
=========================================================

Options that are part of the thumbnail, like ``format``, ``quality`` or
``crop``, go into its file name, so a change makes a new file. Settings that
are not, ``THUMBNAIL_FLATTEN`` for example, change how the next thumbnail is
made but leave the existing files alone. Delete them::

    python manage.py thumbnail clear_delete_all

NotImplementedError, or "crop='smart' is only supported by the PIL and vips engines"
====================================================================================

The option is not implemented by the engine in ``THUMBNAIL_ENGINE``. Smart
crop, ``remove_border``, ``rounded`` and ``blur`` are PIL and vips only, and
``padding`` is PIL, convert and vips. The table under Options in
:doc:`template` lists every option per engine.

EngineError: convert is not installed or not on PATH
====================================================

The convert engine runs ImageMagick's ``convert`` and ``identify`` commands.
Install ImageMagick, or point ``THUMBNAIL_CONVERT`` and
``THUMBNAIL_IDENTIFY`` at the binaries. For GraphicsMagick they are
``gm convert`` and ``gm identify``.

Captured stderr: WARNING: The convert command is deprecated in IMv7
===================================================================

ImageMagick 7 still ships ``convert`` but warns on every call, and the
convert engine logs anything a tool prints to stderr as an error. Switch to
the ``magick`` command::

    THUMBNAIL_CONVERT = 'magick'
    THUMBNAIL_IDENTIFY = 'magick identify'

EngineError: convert did not finish in 60 seconds
=================================================

A tool call hit ``THUMBNAIL_COMMAND_TIMEOUT``. A large PDF at a high
``density``, or a hostile file, can take that long. Raise the timeout if the
source is legitimate; a lower ``density`` helps for PDF pages.

The convert command wrote JPEG instead of AVIF
==============================================

ImageMagick has no AVIF encoder on this machine, so it fell back to JPEG and
sorl-thumbnail refused the file. Install libheif with an AV1 encoder, on
Debian and Ubuntu the ``libheif-plugin-aomenc`` package, or ask for WEBP.

"Upload a valid image" for a file that opens elsewhere
======================================================

``sorl.thumbnail.ImageField`` validates the upload with the engine. The PIL
and vips engines decode the whole file and reject one that is truncated,
for example cut off by a dropped connection, even if a viewer shows most of
it. Re-export the image. The convert, wand and pgmagick engines accept such
files and fill the missing part with grey.

A portrait photo comes out squashed or rotated
==============================================

Phones store the rotation in the EXIF orientation tag, and sorl-thumbnail
applies it unless ``orientation=False`` is passed. Before 13.4.0 one such
call turned orientation off for the size of every later thumbnail in the
process. Upgrade, then delete the affected thumbnails with
``manage.py thumbnail clear_delete_all``.

Pages are slow on Amazon S3
===========================

See :doc:`s3`: what costs a request, the settings that avoid them, and how
to make the thumbnails ahead of the first visitor.

A remote image source hangs the page
====================================

A source given as a URL is downloaded with no time limit by default. Set
``THUMBNAIL_URL_TIMEOUT`` to a number of seconds.

Animated GIF thumbnails are slow
================================

With ``format="GIF"`` the PIL and vips engines thumbnail every frame, so
the cost grows with the frame count. Limit the frames when validating
uploads, or write another format to keep the first frame only.
