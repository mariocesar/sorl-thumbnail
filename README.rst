|pypi| |python-badge| |django-badge| |docs| |gh-actions| |codecov| |precommit|

==============
sorl-thumbnail
==============

Thumbnails for Django. You write the size in the template, or ask for it in
Python, and sorl-thumbnail makes the thumbnail on first use with Pillow,
libvips or ImageMagick, saves it on your media storage and remembers it in a
key-value store, so later renders cost no image work and no storage request.

- Website, with an example gallery for every image engine:
  https://mariocesar.github.io/sorl-thumbnail/
- Documentation: https://sorl-thumbnail.readthedocs.io/

Quick start
===========

Install sorl-thumbnail with Pillow::

    pip install "sorl-thumbnail[pil]"

Add ``'sorl.thumbnail'`` to ``INSTALLED_APPS``::

    INSTALLED_APPS = [
        ...
        'sorl.thumbnail',
    ]

and create its table::

    python manage.py migrate

Then, in a template::

    {% load thumbnail %}

    {% thumbnail item.image "100x100" crop="center" as im %}
        <img src="{{ im.url }}" width="{{ im.width }}" height="{{ im.height }}">
    {% endthumbnail %}

``item.image`` can be an ``ImageField``, a path in your media storage or the
URL of an image. The same from Python::

    from sorl.thumbnail import get_thumbnail

    im = get_thumbnail(item.image, '100x100', crop='center', quality=99)

The `quickstart`_ walks through this. The documentation covers the
`template tag and its options`_, every `setting`_, `thumbnails on Amazon S3`_
and `troubleshooting`_.

Features
========

- Resize to a box, a width or a height. Crop by position, percentage, pixels
  or a crop box, crop to the busiest part of the image, or cut plain borders
  first.
- JPEG, PNG, GIF, WEBP and AVIF output, with quality, progressive JPEG,
  grayscale, padding, rounded corners and blur. Animated GIFs stay animated
  with Pillow and libvips.
- Follows the EXIF orientation of photos.
- Any Django storage for sources and thumbnails, Amazon S3 included. The
  key-value store, your database read through your cache or Redis, remembers
  every thumbnail, so a cached one costs no storage request.
- An ``ImageField`` that validates uploads, an admin widget with a preview,
  and placeholder images for developing without the real media.
- Alternative resolutions for high-density screens, and the ``is_portrait``
  and ``margin`` filters for layout.
- Django 5.2, 6.0 and 6.1, following the `Django supported versions
  policy`_, on Python 3.10 and later.

Engines
=======

The engine does the resizing. Set it with ``THUMBNAIL_ENGINE``; Pillow is the
default.

- `Pillow`_, the default: ``pip install "sorl-thumbnail[pil]"``.
- `libvips`_ through pyvips: ``pip install "sorl-thumbnail[vips]"``.
- `ImageMagick`_, through its ``convert`` and ``identify`` commands. Also
  reads PDF pages.
- `GraphicsMagick`_, the same engine through ``gm convert`` and
  ``gm identify``.
- `Wand`_, a Python binding for ImageMagick: ``pip install "sorl-thumbnail[wand]"``.
- `pgmagick`_, a Python binding for GraphicsMagick:
  ``pip install "sorl-thumbnail[pgmagick]"``.

Each engine has an example gallery on the `website`_, and the documentation
lists which options each one supports.

Using it next to another thumbnail library
==========================================

Other libraries also register a ``thumbnail`` template library. Load
sorl-thumbnail's tags as ``sorl_thumbnail`` instead, the tag is the same::

    {% load sorl_thumbnail %}

Help
====

Ask in the Q&A category of `GitHub Discussions`_. Report bugs in the
`issue tracker`_.

Contributing
============

Pull requests are welcome. The `contributing guide`_ explains how to run the
tests and send a change. Using AI tools is fine if you say so and test the
change yourself; pull requests sent by scripts are closed. By contributing
you agree to the `Code of Conduct`_. To report a security issue, follow the
`security policy`_ instead of opening a public issue.

The tests run with tox through `uv`_, one environment per Python, Django and
engine::

    uvx --with tox-uv tox -l
    uvx --with tox-uv tox -e py312-django52-pil

The Pillow and libvips environments need nothing else. The others need the
engine's tools, see the `requirements`_, or run them in Docker as the
contributing guide shows.

License
=======

BSD 3-Clause, see the `LICENSE file <https://github.com/mariocesar/sorl-thumbnail/blob/main/LICENSE>`_.


.. |gh-actions| image:: https://github.com/mariocesar/sorl-thumbnail/actions/workflows/test.yml/badge.svg
    :target: https://github.com/mariocesar/sorl-thumbnail/actions/workflows/test.yml
    :alt: Test status
.. |docs| image:: https://readthedocs.org/projects/sorl-thumbnail/badge/?version=latest
    :target: https://sorl-thumbnail.readthedocs.io/en/latest/
    :alt: Documentation for the latest version
.. |pypi| image:: https://img.shields.io/pypi/v/sorl-thumbnail.svg
    :target: https://pypi.org/project/sorl-thumbnail/
    :alt: sorl-thumbnail on PyPI
.. |python-badge| image:: https://img.shields.io/pypi/pyversions/sorl-thumbnail.svg
    :target: https://pypi.org/project/sorl-thumbnail/
    :alt: Supported Python versions
.. |django-badge| image:: https://img.shields.io/pypi/djversions/sorl-thumbnail.svg
    :target: https://pypi.org/project/sorl-thumbnail/
    :alt: Supported Django versions
.. |codecov| image:: https://codecov.io/gh/mariocesar/sorl-thumbnail/graph/badge.svg
    :target: https://codecov.io/gh/mariocesar/sorl-thumbnail
    :alt: Test coverage
.. |precommit| image:: https://results.pre-commit.ci/badge/github/mariocesar/sorl-thumbnail/main.svg
    :target: https://results.pre-commit.ci/latest/github/mariocesar/sorl-thumbnail/main
    :alt: pre-commit.ci status

.. _Pillow: https://pillow.readthedocs.io/
.. _libvips: https://www.libvips.org/
.. _ImageMagick: https://imagemagick.org/
.. _GraphicsMagick: http://www.graphicsmagick.org/
.. _Wand: https://docs.wand-py.org/
.. _pgmagick: https://pgmagick.readthedocs.io/
.. _uv: https://docs.astral.sh/uv/
.. _website: https://mariocesar.github.io/sorl-thumbnail/

.. _quickstart: https://sorl-thumbnail.readthedocs.io/en/latest/quickstart.html
.. _template tag and its options: https://sorl-thumbnail.readthedocs.io/en/latest/template.html
.. _setting: https://sorl-thumbnail.readthedocs.io/en/latest/reference/settings.html
.. _thumbnails on Amazon S3: https://sorl-thumbnail.readthedocs.io/en/latest/s3.html
.. _troubleshooting: https://sorl-thumbnail.readthedocs.io/en/latest/troubleshooting.html
.. _requirements: https://sorl-thumbnail.readthedocs.io/en/latest/requirements.html
.. _contributing guide: https://sorl-thumbnail.readthedocs.io/en/latest/contributing.html
.. _Django supported versions policy: https://www.djangoproject.com/download/#supported-versions
.. _GitHub Discussions: https://github.com/mariocesar/sorl-thumbnail/discussions
.. _issue tracker: https://github.com/mariocesar/sorl-thumbnail/issues
.. _Code of Conduct: https://github.com/mariocesar/sorl-thumbnail/blob/main/CODE_OF_CONDUCT.md
.. _security policy: https://github.com/mariocesar/sorl-thumbnail/blob/main/SECURITY.md
