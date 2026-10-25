|pypi| |python-badge| |django-badge| |docs| |gh-actions| |codecov| |precommit|

Thumbnails for Django.

Website, with examples for every image engine: https://mariocesar.github.io/sorl-thumbnail/

Features at a glance
====================

- Support for Django 5.2, 6.0, and 6.1 following the `Django supported versions policy`_
- Storage support
- Pluggable Engine support for `Pillow`_, `ImageMagick`_, `PIL`_, `Wand`_, `pgmagick`_, and `libvips`_
- Pluggable Key Value Store support (cached db and redis)
- Pluggable Backend support
- Admin integration with possibility to delete
- Dummy generation (placeholders)
- Flexible, simple syntax, generates no html
- CSS style cropping options
- Back smart cropping, and remove borders from the images when cropping
- Margin calculation for vertical positioning
- Alternative resolutions versions of a thumbnail

Read more in `the documentation (latest version) <https://sorl-thumbnail.readthedocs.io/>`_

Developers
==========

By contributing you agree to abide by the
`Code of Conduct <https://github.com/mariocesar/sorl-thumbnail/blob/main/CODE_OF_CONDUCT.md>`_.
To report a security issue, follow the
`security policy <https://github.com/mariocesar/sorl-thumbnail/blob/main/SECURITY.md>`_
instead of opening a public issue.

Feel free to create a new Pull request if you want to propose a new feature.
If you need development support or want to discuss with other developers
join us in `GitHub Discussions`_.

Tests
-----
The tests run with tox, which uses `uv <https://docs.astral.sh/uv/>`_ to create its environments.
With uv installed, `uvx --with tox-uv tox` will run all tests for all environments.
However, it is possible to run a certain environment with `uvx --with tox-uv tox -e <env>`, a list of all environments
can be found with `uvx --with tox-uv tox -l`. These tests require the dependencies of the different engines defined in
the documentation. The easiest way to run tests is using Docker - see the `contributing documentation <https://sorl-thumbnail.readthedocs.io/en/latest/contributing.html#running-testsuite>`_
for detailed instructions on running tests locally with Docker.

User Support
============

If you need help using sorl-thumbnail ask in the Q&A category of `GitHub Discussions`_.


How to Use
==========

Get the code
------------

Getting the code for the latest stable release use 'pip'. ::

   $ pip install sorl-thumbnail

Install in your project
-----------------------

Then register 'sorl.thumbnail', in the 'INSTALLED_APPS' section of
your project's settings. ::

    INSTALLED_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',

        'sorl.thumbnail',
    ]


Templates Usage
---------------

All of the examples assume that you first load the thumbnail template tag in
your template.::

    {% load thumbnail %}


A simple usage. ::

    {% thumbnail item.image "100x100" crop="center" as im %}
        <img src="{{ im.url }}" width="{{ im.width }}" height="{{ im.height }}">
    {% endthumbnail %}

See more examples in the section `Template examples`_ in the Documentation

Model Usage
-----------

You can use ``sorl.thumbnail.ImageField`` in your models::

    from django.db import models
    from sorl.thumbnail import ImageField

    class Item(models.Model):
        image = ImageField(upload_to='whatever')

See more examples in the section `Model examples`_ in the Documentation

Low level API
-------------

You can use the 'get_thumbnail'::

    from sorl.thumbnail import get_thumbnail
    from sorl.thumbnail import delete

    im = get_thumbnail(my_file, '100x100', crop='center', quality=99)
    delete(my_file)

See more examples in the section `Low level API examples`_ in the Documentation

Using in combination with other thumbnailers
--------------------------------------------

Alternatively, you load the templatetags by {% load sorl_thumbnail %}
instead of traditional {% load thumbnail %}. It's especially useful in
projects that do make use of multiple thumbnailer libraries that use the
same name (``thumbnail``) for the templatetag module::

    {% load sorl_thumbnail %}
    {% thumbnail item.image "100x100" crop="center" as im %}
        <img src="{{ im.url }}" width="{{ im.width }}" height="{{ im.height }}">
    {% endthumbnail %}

Frequently asked questions
==========================

Is it slow on Amazon S3?
------------------------

Once a thumbnail is in the key-value store, rendering it makes no request to
the storage at all. A slow page means thumbnails are being generated, or the
key-value store was cleared or lost. Generating a thumbnail reads the source
once and writes the result once, which is as little as it can be.

Older versions of this FAQ recommended ``THUMBNAIL_FORCE_OVERWRITE = True``.
That advice dates from boto 2. With boto3 it makes things worse: on a key-value
store miss it regenerates the thumbnail from the full-size source instead of
making one ``HEAD`` request for the file that is already there. See
`THUMBNAIL_FORCE_OVERWRITE`_ before enabling it.


.. |gh-actions| image:: https://github.com/mariocesar/sorl-thumbnail/workflows/Test/badge.svg
    :target: https://github.com/mariocesar/sorl-thumbnail/actions
.. |docs| image:: https://readthedocs.org/projects/sorl-thumbnail/badge/?version=latest
    :alt: Documentation for latest version
    :target: https://sorl-thumbnail.readthedocs.io/en/latest/
.. |pypi| image:: https://img.shields.io/pypi/v/sorl-thumbnail.svg
    :target: https://pypi.python.org/pypi/sorl-thumbnail
    :alt: sorl-thumbnail on PyPI
.. |python-badge| image:: https://img.shields.io/pypi/pyversions/sorl-thumbnail.svg
    :target: https://pypi.python.org/pypi/sorl-thumbnail
    :alt: Supported Python versions
.. |django-badge| image:: https://img.shields.io/pypi/djversions/sorl-thumbnail.svg
    :target: https://pypi.python.org/pypi/sorl-thumbnail
    :alt: Supported Django versions
.. |codecov| image:: https://codecov.io/gh/mariocesar/sorl-thumbnail/graph/badge.svg?token=YSN2eCESQT 
    :target: https://codecov.io/gh/mariocesar/sorl-thumbnail
    :alt: Coverage
.. |precommit| image:: https://results.pre-commit.ci/badge/github/mariocesar/sorl-thumbnail/main.svg
   :target: https://results.pre-commit.ci/latest/github/mariocesar/sorl-thumbnail/main
   :alt: pre-commit.ci status

.. _`Pillow`: https://pillow.readthedocs.io/
.. _`ImageMagick`: https://imagemagick.org/
.. _`PIL`: https://python-pillow.org/
.. _`Wand`: https://docs.wand-py.org/
.. _`pgmagick`: https://pgmagick.readthedocs.io/
.. _`libvips`: https://www.libvips.org/

.. _`Template examples`: https://sorl-thumbnail.readthedocs.io/en/latest/examples.html#template-examples
.. _`Model examples`: https://sorl-thumbnail.readthedocs.io/en/latest/examples.html#model-examples
.. _`Low level API examples`: https://sorl-thumbnail.readthedocs.io/en/latest/examples.html#low-level-api-examples
.. _`GitHub Discussions`: https://github.com/mariocesar/sorl-thumbnail/discussions
.. _`THUMBNAIL_FORCE_OVERWRITE`: https://sorl-thumbnail.readthedocs.io/en/latest/reference/settings.html#thumbnail-force-overwrite
.. _`Django supported versions policy`: https://www.djangoproject.com/download/#supported-versions
