****************
Errors & Logging
****************

.. highlight:: python

Background
==========
When ``THUMBNAIL_DEBUG = False`` errors will be suppressed if they are raised
during rendering the ``thumbnail`` tag or raised within the included filters.
This is the recommended production setting. However it can still be useful to be
notified of those errors. Thus sorl-thumbnail logs errors to a logger and
provides a log handler that sends emails to ``settings.ADMINS``.

In development set ``THUMBNAIL_DEBUG = True`` so the error is raised and
Django's debug page shows it. To see the errors in the console instead, give
the ``sorl.thumbnail`` logger a handler in ``LOGGING``::

    LOGGING = {
        'version': 1,
        'handlers': {'console': {'class': 'logging.StreamHandler'}},
        'loggers': {'sorl.thumbnail': {'handlers': ['console'], 'level': 'ERROR'}},
    }


How to setup logging
====================
To enable logging you need to add a handler to the 'sorl.thumbnail' logger.
The following example adds the provided handler that sends emails to site admins
in case an error is raised with debugging off::

    import logging
    from sorl.thumbnail.log import ThumbnailLogHandler


    handler = ThumbnailLogHandler()
    handler.setLevel(logging.ERROR)
    logging.getLogger('sorl.thumbnail').addHandler(handler)


You will need to load this code somewhere in your django project, it could be
in urls.py, settings.py or project/app __init__.py file for example. You could
of course also provide your own logging handler.

