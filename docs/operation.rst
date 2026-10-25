***************************
How sorl-thumbnail operates
***************************

.. highlight:: python

When you use the ``thumbnail`` template tag sorl-thumbnail looks up the
thumbnail in a :ref:`kvstore-requirements`. The key for a thumbnail is
generated from its filename and storage. The thumbnail filename in turn is
generated from the source and requested thumbnail size and options.  If the key
for the thumbnail is found in the |kvstore|, the serialized thumbnail
information is fetched from it and returned. If the thumbnail key is not found
there sorl-thumbnail continues to generate the thumbnail and stores necessary
information in the |kvstore|.  It is worth noting that sorl-thumbnail does not
check if source or thumbnail exists if the thumbnail key is found in the
|kvstore|.

.. graphviz:: operation.dot
   :caption: How a thumbnail request is served. Green is your template, blue
             the Key Value Store, yellow the file storage and grey the image
             engine.

.. note:: This means that if you change or delete a source file or delete the
    thumbnail, sorl-thumbnail will still fetch from the |kvstore|.
    Therefore it is important that if you delete or change a source or
    thumbnail file notify the |kvstore|.

If you change or delete a source or a thumbnail for some reason, you can use
the ``delete`` method of the ``ThumbnailBackend`` class or subclass::

    from sorl.thumbnail import delete

    # Delete the Key Value Store reference but **not** the file.
    # Use this if you have changed the source
    delete(my_file, delete_file=False)

    # Delete the Key Value Store reference and the file
    # Use this if you want to delete the source file
    delete(my_file) # delete_file=True is default


The ``sorl.thumbnail.delete`` method always deletes the input files thumbnail
Key Value Store references as well as thumbnail files, and drops the file from
the source cache (see :ref:`source-cache`). You can use this method on
thumbnails as well as source files. Alternatively if you have **deleted** a
file you can use the management command :ref:`thumbnail-cleanup`.

**Why you ask?** Why go through all the trouble with a |kvstore| and risk
stale cache? Why not use a database to cache if you are going to do that?

The reason is speed and especially with storages other than local file storage.
Checking if a file exists before serving it will cost too much. Speed is also
the reason for not choosing to use a standard database for this kind of
persistent caching. However sorl-thumbnail does ship with a *cached* database
|kvstore|.

.. note:: We have to assume the thumbnail exists if the thumbnail key exists in
    the |kvstore|

**There are bonuses**. We can store meta data in the |kvstore| that would be
too costly to retrieve even for local file storage. Today this meta data
consists only of the image size but this could be expanded to for example EXIF
data. The other bonus is that we can keep track of what thumbnails has been
generated from a particular source and deleting them too when the source is
deleted.

.. _source-cache:

Reading the source once
=======================

The thumbnail tag reads the source file when it has to make a thumbnail, and
``is_portrait`` and the margin filters read it when the |kvstore| has no size
for it yet. A template that runs a filter and then the tag, or makes three
sizes of one image, used to download the original once per use. Now
sorl-thumbnail keeps the bytes of the last source it read until the request
ends, and every use in between is served from that copy. This is the source
cache. It holds one file at a time and takes no more memory than making one
thumbnail already does. It works with every engine and needs no setting.

The cache reads through the storage, never through your file object, so a
``FieldFile`` you have open keeps its position and stays open.

If you replace a source during a request that already read it, the cache
still holds the old bytes. Call ``delete(my_file, delete_file=False)`` as
above and the next read fetches the new file.

Outside a request nothing is cached. In a management command or a background
job wrap the work in ``source_cache``, see :ref:`source-cache-in-a-job`.

Under ASGI the request scope needs Django 6.1. On Django 5.2 or 6.0 add the
middleware from :doc:`installation`.

.. |kvstore| replace:: Key Value Store
