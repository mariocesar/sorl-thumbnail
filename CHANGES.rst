=======
Changes
=======

13.4.0
======

* A project homepage with example galleries for each image engine, built from
  ``demo/`` and published to https://mariocesar.github.io/sorl-thumbnail/
* A source is downloaded once per request, with every engine. ``is_portrait``
  before the tag, or several sizes of one image, read the original once
  instead of once per use. Before, every filter and tag opened the source
  again, on S3 a full download each time. sorl-thumbnail now keeps the bytes
  of the last source it read, the source cache, until the request ends; a
  ``FieldFile`` you have open is not touched. Nothing to do on WSGI or on
  Django 6.1. On ASGI with Django 5.2 or 6.0 add
  ``sorl.thumbnail.middleware.SourceCacheMiddleware`` to ``MIDDLEWARE``. In a
  management command or a job wrap the work in ``with source_cache():``
  (`#471 <https://github.com/mariocesar/sorl-thumbnail/issues/471>`__)
* Rounded corners work with JPEG in the PIL engine. Asking for ``rounded=10``
  crashed with ``OSError: cannot write mode RGBA as JPEG`` whenever the
  thumbnail was saved as JPEG, which is the default format. JPEG can't store
  transparency, so the corners are now filled with white, or with the padding
  color when the thumbnail is padded. That is the same background
  ``THUMBNAIL_FLATTEN`` uses, and it applies whether the setting is on or not.
  For transparent corners, ask for ``format='PNG'`` or ``format='WEBP'``
  (`#849 <https://github.com/mariocesar/sorl-thumbnail/issues/849>`__)
* ``remove_border=True`` now trims the empty margins of transparent images,
  like a logo saved as PNG with space around it. It works by walking in from
  each edge and cutting strips that are a single flat color. The transparency
  channel made every strip look detailed, so nothing was ever cut. A strip now
  counts as flat when it looks flat on both a black and a white background, so
  the color a file happens to store under its transparent pixels makes no
  difference. The PIL and vips engines support ``remove_border``
* ``remove_border=True`` now cuts the border exactly. Borders thinner than
  10 px were kept, thicker ones were cut short, and wide or tall images lost
  too much. Delete old thumbnails with ``manage.py thumbnail clear_delete_all``
  to regenerate them
  (`#845 <https://github.com/mariocesar/sorl-thumbnail/issues/845>`__)
* Blurring a transparent image no longer leaves a dark outline. ``blur`` mixed
  in the color stored under the transparent pixels, usually black, so a white
  shape on a transparent background came out with grey edges. The PIL engine
  now blurs with premultiplied alpha, which weighs each pixel by how visible it
  is. Thumbnails made before the upgrade keep the outline until you delete
  them, for example with ``manage.py thumbnail clear_delete_all``
* ``orientation=False`` now applies only to the thumbnail it is given to. One
  such call used to turn off EXIF orientation for the size of every later
  thumbnail in the same process, so a photo taken in portrait could come out
  squashed or with the wrong ``is_portrait``, until the server restarted. This
  affected every engine. If you use ``orientation=False``, delete thumbnails
  made before the upgrade with ``manage.py thumbnail clear_delete_all``
  (`#843 <https://github.com/mariocesar/sorl-thumbnail/issues/843>`__)
* sorl-thumbnail's ``ImageField`` rejects a truncated upload, such as a JPEG
  cut off by a dropped connection, with "Upload a valid image". The PIL engine
  only read the file's headers, so the upload was saved and the thumbnail
  failed later with ``OSError: image file is truncated``. It now decodes the
  whole image. The other engines accept these files on purpose: ImageMagick,
  GraphicsMagick and wand make the thumbnail and fill the missing part with
  grey (`#427 <https://github.com/mariocesar/sorl-thumbnail/issues/427>`__)
* Cached thumbnails keep the ``OPTIONS`` of their ``STORAGES`` alias, like
  ``base_url`` and ``location``, when the ``BACKEND`` is written the way
  Django's docs write it, ``django.core.files.storage.FileSystemStorage``.
  The alias was found by comparing that text with the class's full path,
  ``django.core.files.storage.filesystem.FileSystemStorage``, so it never
  matched, and the second request for a thumbnail built a storage without the
  options and returned a different URL. The alias is now found by the class
  the ``BACKEND`` imports. This applies to every engine. Run
  ``manage.py thumbnail clear`` once after upgrading: it empties the key-value
  store, sorl-thumbnail's record of the thumbnails it made, without deleting
  any file
  (`#834 <https://github.com/mariocesar/sorl-thumbnail/issues/834>`__)
* The DynamoDB key-value store is removed. It was built on boto 2, which can't
  be imported on any Python sorl-thumbnail supports, so the store failed before
  making a single thumbnail: ``cannot import name 'Mapping' from
  'collections'`` on Python 3.10 and 3.11, ``No module named
  'boto.vendored.six.moves'`` from 3.12. If ``THUMBNAIL_KVSTORE`` still names
  ``sorl.thumbnail.kvstores.dynamodb_kvstore.KVStore``, remove the setting to
  use the default Cached DB store, and point ``THUMBNAIL_CACHE`` at any Django
  cache alias, a DynamoDB one included
  (`#838 <https://github.com/mariocesar/sorl-thumbnail/issues/838>`__)
* Added a libvips engine on pyvips, ``sorl.thumbnail.engines.vips_engine.Engine``.
  Install it with ``pip install sorl-thumbnail[vips]``. It implements every
  thumbnail option, including blur, padding, rounded corners, smart crop and
  ``remove_border``, keeps the ICC profile, and rejects truncated sources. It
  refuses PDF and SVG sources, use the convert engine for those
  (`#833 <https://github.com/mariocesar/sorl-thumbnail/issues/833>`__)
* The vips engine keeps animated GIFs animated when the thumbnail format is
  ``GIF``, like the PIL engine. Other formats take the first frame (`#833 <https://github.com/mariocesar/sorl-thumbnail/issues/833>`__)
* Removed the vipsthumbnail engine and its ``THUMBNAIL_VIPSTHUMBNAIL`` and
  ``THUMBNAIL_VIPSHEADER`` settings. It has failed on every thumbnail with the
  default settings since 12.6.3. Use ``sorl.thumbnail.engines.vips_engine.Engine``
  instead (`#833 <https://github.com/mariocesar/sorl-thumbnail/issues/833>`__)
* Removed the ``THUMBNAIL_LAZY_FILL_EMPTY`` setting. Nothing read it, so
  setting it never did anything
* The docs have a quickstart, a guide for Amazon S3, a troubleshooting page
  and a page on choosing a thumbnail library. Every option, filter and setting
  is documented, and the examples run as written:
  https://sorl-thumbnail.readthedocs.io/

13.3.0
======

* The convert and vipsthumbnail engines run their tools through
  ``subprocess.run``. This fixes a deadlock when a tool wrote more than the
  pipe buffer to stderr, and closes the pipes that ``is_valid_image`` and the
  size probes left open. A call that runs longer than the new
  ``THUMBNAIL_COMMAND_TIMEOUT`` setting, 60 seconds by default, is killed and
  raises ``EngineError``. Set it higher for large sources, or to ``None`` for
  the previous unbounded behaviour
* The vipsthumbnail engine no longer fails on any stderr output, which made
  every thumbnail fail on a libvips that prints a warning on startup. It checks
  the exit code like the convert engine does, and raises ``EngineError``
  instead of a bare ``Exception`` or ``AttributeError`` when ``vipsthumbnail``
  or ``vipsheader`` fail
* ``crop='smart'`` now returns the requested size. It could hang forever,
  raise ``ValueError``, or return a thumbnail that was too narrow, like
  44×200 for ``200x200`` (`#829 <https://github.com/mariocesar/sorl-thumbnail/issues/829>`__)
* Documented ``crop='smart'``. It only works with the PIL engine, and the other
  engines now say so in the error instead of raising an empty
  ``NotImplementedError``
* The convert engine raises an error when convert writes a different format
  than the one requested. Without an AVIF encoder, ImageMagick printed a
  warning, exited with 0 and wrote a JPEG, which was saved under an ``.avif``
  name (`#837 <https://github.com/mariocesar/sorl-thumbnail/issues/837>`__).
  Browsers displayed those files, so sites that ask for AVIF on such a machine
  will now see the thumbnail tag fail instead. Install ``libheif-plugin-aomenc``
  or ask for WEBP. Thumbnails created before the upgrade keep working
* The PIL engine writes a greyscale source with an alpha channel (mode ``LA``)
  as JPEG instead of raising ``OSError: cannot write mode RGBA as JPEG``
  (`#474 <https://github.com/mariocesar/sorl-thumbnail/issues/474>`__)
* The PIL and wand engines now honour ``THUMBNAIL_FLATTEN``, which is now
  documented along with the ``flatten`` option. A transparent source written as
  JPEG shows the color stored under its transparent pixels, usually black. With
  the setting on it is composited onto a white background, or the padding color
  when the thumbnail is padded (`#474 <https://github.com/mariocesar/sorl-thumbnail/issues/474>`__).
  The convert engine already flattened, and does so for every format, so its
  PNG, GIF and WEBP thumbnails lose their transparency too. ``flatten=False``
  now turns it off for one thumbnail, before only the string ``"off"`` did. The
  setting is not part of the thumbnail name, so thumbnails created before the
  upgrade keep their black background until you delete them, for example with
  ``manage.py thumbnail clear_delete_all``
* The cached DB key-value store writes every entry with a single upsert
  instead of a lookup followed by an insert or update, so creating a thumbnail
  runs six statements instead of nine. Oracle has no upsert in Django and keeps
  the two-step write (`#451 <https://github.com/mariocesar/sorl-thumbnail/issues/451>`__)
* Documented ``THUMBNAIL_FORCE_OVERWRITE`` and stopped recommending it for
  Amazon S3. On a key-value store miss it regenerates the thumbnail from the
  full-size source where the default makes one ``HEAD`` request, so with boto3
  it makes S3 slower, not faster (`#351 <https://github.com/mariocesar/sorl-thumbnail/issues/351>`__)
* The convert engine now reports the padded size when ``padding=True``, so
  ``im.width`` and ``im.height`` match the file it wrote instead of the size
  before padding (`#835 <https://github.com/mariocesar/sorl-thumbnail/issues/835>`__)
* The PIL engine keeps animated GIFs animated when the thumbnail format is
  ``GIF``. Every frame is thumbnailed, keeping its duration and the loop
  count. Other formats still take the first frame (`#687 <https://github.com/mariocesar/sorl-thumbnail/issues/687>`__)
* ``UrlStorage`` no longer escapes ``+`` and ``/`` in the query string of
  remote image URLs, which broke signed URLs. Only applies with
  ``THUMBNAIL_REMOVE_URL_ARGS = False``, the default strips the query first
* The default branch is now ``main`` instead of ``master``. GitHub redirects
  links to ``master`` to ``main``. To update an existing clone or fork::

    git branch -m master main
    git fetch origin
    git branch -u origin/main main
    git remote set-head origin -a

13.2.0
======

sorl-thumbnail is moving out of Jazzband, which is closing, and into
https://github.com/mariocesar/sorl-thumbnail. Thank you to Jazzband and to
everyone who kept the project alive there for nine years. ❤️ (`#827 <https://github.com/mariocesar/sorl-thumbnail/pull/827>`__)

* Added ``density`` and ``authenticate`` options to the convert engine, passed
  ahead of the source so PDFs rasterize at a given DPI and encrypted PDFs can
  be read, per call instead of globally through ``THUMBNAIL_CONVERT``. Errors
  from a call carrying a password omit the command line and stderr (`#783 <https://github.com/mariocesar/sorl-thumbnail/issues/783>`__, `#640 <https://github.com/mariocesar/sorl-thumbnail/issues/640>`__)
* The convert engine now raises ``EngineError`` when ``identify`` reports no
  image size, instead of crashing with ``AttributeError`` (`#640 <https://github.com/mariocesar/sorl-thumbnail/issues/640>`__)
* Added an engine ``prepare(image, options)`` hook, called before the source
  is sized, for options that change how it is read
* The ``thumbnail`` template tag now raises ``TemplateSyntaxError`` when the
  source or geometry is missing, instead of ``IndexError`` or compiling a tag
  that fails at render (`#720 <https://github.com/mariocesar/sorl-thumbnail/issues/720>`__)
* ``ImageFile.serialize_storage`` resolves the storage alias by instance instead
  of returning the first alias with the same backend class, and ``ImageFile.key``
  includes that alias for storages other than ``default`` and
  ``THUMBNAIL_STORAGE``. Same-named files on same-class storages no longer share
  a thumbnail (`#806 <https://github.com/mariocesar/sorl-thumbnail/issues/806>`__)
* The docs build again on Read the Docs and with current setuptools. The new
  ``docs`` extra installs what is needed to build them (`#823 <https://github.com/mariocesar/sorl-thumbnail/pull/823>`__)
* Added a drawing of how a thumbnail request is served to the operation docs (`#714 <https://github.com/mariocesar/sorl-thumbnail/issues/714>`__)

13.1.0
======
* The ``clear_delete_referenced`` management command now supports a ``--timeout``
  option to selectively delete thumbnails (`#721 <https://github.com/mariocesar/sorl-thumbnail/issues/721>`__)
* Added avif support through optional ``pillow-avif-plugin`` package (`#772 <https://github.com/mariocesar/sorl-thumbnail/pull/772>`__)
* ``ImageField.delete_file`` was removed (obsolete with Django > 1.2.5)
* Make ``ImageFormField`` render with ``accept="image/*"`` HTML attribute (`#731 <https://github.com/mariocesar/sorl-thumbnail/pull/731>`__)
* ``AdminImageWidget`` inherits now from Django's ``AdminFileWidget``
* Restored ``ImageFile.key`` output from the pre-13 releases, avoiding obsoleting
  legacy thumbnails (`#805 <https://github.com/mariocesar/sorl-thumbnail/issues/805>`__)
* crop='noop' now uses min-scaling like unset crop (`#812 <https://github.com/mariocesar/sorl-thumbnail/pull/812>`__)
* Added testing with Django 6.0 and 6.1, and Python 3.14.
* Dropped support for Django < 5.2.

13.0.0
======
* ``THUMBNAIL_STORAGE`` should now be an alias in the Django ``STORAGES`` setting.
  The old way of specifying a dotted path to a Storage module is still supported.
* Fixed serialization to use storage aliases instead of backend class paths, ensuring
  storage OPTIONS (like bucket names and credentials) are preserved when thumbnails are
  cached and retrieved. Fixes issues with S3, Google Cloud Storage, and other cloud backends.
* Confirmed support for Python 3.13 (on Django 5.1+).
* Drop support for Python 3.8 and 3.9.
* Add support for Django 5.2
* Accept a tuple as blur radius use GaussianBlur from PIL (`#773 <https://github.com/mariocesar/sorl-thumbnail/issues/773>`__)
* Fixed a performance issue in convert engine with _get_exif_orientation
* Reduced logging in ThumbnailBackend when THUMBNAIL_DUMMY is activated
* Privileged sRGB as default for ImageMagick colorspace

12.11.0
=======
* Deprecated ``THUMBNAIL_KVSTORE``. Only the Django cache-based store will be
  used in a future version.
* Add support for Django 5.0 and 5.1
* Add support for installing with optional dependencies.
* Drop support for Django 3.2, 4.0 and 4.1

12.10.0
=======
* Fixed safe_filter application on various thumbnail template tags.
* Fixed slow performance with external storages like S3.
* Added support for Django 4.2.
* Drop support for Python 3.7.
* Confirmed Python 3.11 support.

12.9.0
======
* Drop support for Django 2.2 and 3.1.
* Added support for Django 4.1.
* Drop support for Python 3.6.
* Fixed various Pillow deprecation warnings.

12.8.0
======
* Drop support for Django 3.0.
* Added support for Django 3.2 and 4.0.
* Confirmed Python 3.9 and 3.10 support.
* Adapted size regex getting size from the identify output. `#532 <https://github.com/mariocesar/sorl-thumbnail/issues/532>`__
* Display possible ``thumbnail`` command labels in command help.
* Added Jazzband code of conduct.


12.7.0
======
* Drop support for Django 1.11
* Added support for Django 3.1
* Moved to GitHub Action for continuous integration.
* Correction in convert_engine with unknown exif orientation
* Using more resilient _get_exif_orientation logic in convert engine
* Update wand_engine.py for ImageMagick 7
* Fix cannot write mode RGBA as JPEG when thumbnailing a GIF


12.6.3
======

* Deprecate Python 2 compatibility shims in favor of Python 3 only codebase. `#623 <https://github.com/mariocesar/sorl-thumbnail/pull/623>`__
* Fix README on notes about ImageField cleaning up references on delete. `#624 <https://github.com/mariocesar/sorl-thumbnail/pull/624>`__
* Fix image ratios with EXIF orientation. `#619 <https://github.com/mariocesar/sorl-thumbnail/pull/619>`__
* Fix test coverage tracking. `#622 <https://github.com/mariocesar/sorl-thumbnail/pull/622>`__ and `#617 <https://github.com/mariocesar/sorl-thumbnail/pull/617>`__


12.6.2
======

* Fix rST syntax errors from 12.6.0 and 12.6.1 that blocked release. `#613 <https://github.com/mariocesar/sorl-thumbnail/pull/613>`__
* Improve QA setup and add rST validation to Travis and tox test matrix. `#613 <https://github.com/mariocesar/sorl-thumbnail/pull/613>`__


12.6.1
======

* Deprecate explicit support for Python 3.4 and 3.5 in order to simplify the test matrix `#610 <https://github.com/mariocesar/sorl-thumbnail/pull/610>`__
* Add requirement for ``setuptools_scm`` to automatically resolve version from git tags `#610 <https://github.com/mariocesar/sorl-thumbnail/pull/610>`__
* Removed property ``thumbnail.__version__`` `#610 <https://github.com/mariocesar/sorl-thumbnail/pull/610>`__


12.6.0
======

* Add Cropbox feature in Wand/Convert Engine
* Add testing for Django 2.2
* Remove "django.utils.six" to support Django 3.0+
* Remove Python 2 support


12.5.0
======

* Make the template tag accept a falsey image
* Update identify (of convert_engine) for faster multi-page PDF thumbnailing
* Fix Redis KVStore timeout
* Fix format conversion in Wand engine
* Added setting THUMBNAIL_REMOVE_URL_ARGS
* Add testing for Django 2.1
* Drop support for Django < 1.11
* Added ssl parameter to Redis object instantiation
* Fix 2 ResourceWarning: unclosed file, in tests
* Fix AdminImageWidget with Django 2.1
* Test in release version of Python 3.7
* Remove unused unittest imports in thumbnail_tests.compat
* Add a __str__ method to ImageFile


12.4.1
======

sorl-thumbnail was welcomed into the `Jazzband organization and project
<https://jazzband.co/>`__. Jazzband is open to all, and any member of Jazzband
can contribute directly to sorl-thumbnail's GitHub repo. We hope this will
encourage more open source programmers to contribute. Thank you @mariocesar for
taking this step and for the years of effort in this project.

12.4.1 is the first release on PyPI since the migration to the Jazzband
project, and includes two years' worth of changes. Thank you to all
contributors. These are some of the highlights:

* Target Django versions are now 1.8, 1.10, 1.11 and 2.0
* Target Python versions are now 2.7, 3.3, 3.4, 3.5 and 3.6
* Enable GIF support (`#263 <https://github.com/mariocesar/sorl-thumbnail/issues/263>`__)
* Enable WebP support (`#460 <https://github.com/mariocesar/sorl-thumbnail/pull/460>`__)
* New ``sorl_thumbnail`` templatetag library that mirrors traditional ``thumbnail``
* Fix bug RGBA mode not compatible with JPEG on PILLOW >=3.7 (`#503 <https://github.com/mariocesar/sorl-thumbnail/issues/503>`__)
* Don't check EXIF orientation with GraphicsMagick
* Bug fix for handling non-ASCII characters in filenames (`#434 <https://github.com/mariocesar/sorl-thumbnail/pull/434>`__)
* Better error detection and handling in some cases (`#492 <https://github.com/mariocesar/sorl-thumbnail/pull/492>`__)
* Improve automated testing
* Improve documentation
