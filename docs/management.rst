*******************
Management commands
*******************

.. highlight:: python

.. _thumbnail-cleanup:

thumbnail cleanup
=================
``python manage.py thumbnail cleanup``

This cleans up the Key Value Store from stale cache. It removes references to
images that do not exist and thumbnail references and their actual files for
images that do not exist. It removes thumbnails for unknown images. It also
removes references to images on a storage that is no longer in ``STORAGES`` or
in your code, as those files can't be reached anymore. Thumbnails already made
from them are left in place.


.. _thumbnail-clear:

thumbnail clear
===============
``python manage.py thumbnail clear``

This totally empties the Key Value Store of all keys that start with the
``settings.THUMBNAIL_KEY_PREFIX``. It does not delete any files. The Key Value
store will update when you hit the template tags, and if the thumbnails files
still exist they will be used and not overwritten/regenerated. This can be
useful if your Key Value Store has garbage data not dealt with by cleanup or
you're switching Key Value Store backend.


.. _thumbnail-clear-delete-referenced:

thumbnail clear_delete_referenced
=================================
``python manage.py thumbnail clear_delete_referenced``

Equivalent to ``clear`` but first it will delete all thumbnail files
referenced by the Key Value Store. It is generally safe to run this if you do
not reference the generated thumbnails by name somewhere else in your code. As
long as all the original images still exist this will trigger a regeneration of
all the thumbnails the Key Value Store knows about.

The command supports an optional ``--timeout`` parameter that can specify a
date filter criteria when deciding to delete a thumbnail. The timeout value can
be either a number of seconds or an ISO 8601 duration string supported by
``django.utils.dateparse.parse_duration``. For example, running
``python manage.py thumbnail clear_delete_referenced --timeout=P90D`` will
delete all thumbnails that were created more than 90 days ago.


.. _thumbnail-clear-delete-all:

thumbnail clear_delete_all
==========================
``python manage.py thumbnail clear_delete_all``

Equivalent to to ``clear`` but afterwards it will delete all thumbnail files
including any orphans not in the Key Value Store. This can be thought of as a
more aggressive version of ``clear_delete_referenced``. Caution should be
exercised with this command if multiple Django sites (as in ``SITE_ID``) or
projects are using the same ``MEDIA_ROOT`` since this will clear out absolutely
everything in the thumbnail cache directory causing thumbnail regeneration for
all sites and projects. When file system storage is used, it is equivalent to
``rm -rf MEDIA_ROOT + THUMBNAIL_PREFIX`` 
