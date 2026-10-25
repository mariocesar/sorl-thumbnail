************
Contributing
************

Feel free to create a new Pull request if you want to propose a new feature
or fix a bug.  If you need development support or want to discuss
with other developers, join us in `GitHub Discussions`_.

Running testsuite
=================

For occasional developers we recommend using `GitHub Actions`_ to run testsuite,
for those who want to run tests locally, read on.

Since sorl-thumbnail supports a variety of image backends, python and
Django versions, we provide an easy way to test locally across all of them.
We use `Docker`_ for consistent test environments and `tox`_ for managing
python virtual environments. tox creates them with `uv`_, which also downloads
any Python version missing from your machine.

Prerequisites
-------------

* `Install Docker`_ and Docker Compose
* ``cd`` in your source directory

Running tests
-------------

Build the Docker image (first time only)::

    docker compose build

Run all tests (all tox environments)::

    docker compose run --rm test

Run tests for a specific configuration using the ``-e`` option with tox::

    docker compose run --rm test tox -e py312-django52-pil

The format is: ``py<version>-django<version>-<backend>``

For example:
- ``py312`` = Python 3.12
- ``django52`` = Django 5.2
- ``pil`` = Pillow image library backend

For a full list of tox environments, see ``tox.ini``

Running tests without Docker
----------------------------

The ``pil`` and ``vips`` environments need no system packages, so with `uv`_ installed you
can run them directly::

    uvx --with tox-uv tox -e py312-django52-pil

The ``redis`` environments need a server on ``localhost:6379``. The compose
file publishes one::

    docker compose up -d redis
    uvx --with tox-uv tox -e py312-django52-redis

Running specific tests
----------------------

To run specific tests, pass Django test labels after ``--``. Django uses dotted module names,
not file paths::

    # Run a specific test module
    docker compose run --rm test tox -e py312-django52-pil -- tests.thumbnail_tests.test_engines

Running CI target tests
-----------------------

To replicate GitHub Actions CI tests, use the ``ci`` service with the TARGET
environment variable. Available targets: ``pil``, ``imagemagick``, ``graphicsmagick``,
``redis``, ``wand``, ``dbm``, ``vips``, and ``qa`` (for quality assurance checks).

Run a specific CI target::

    TARGET=pil docker compose run --rm ci
    TARGET=imagemagick docker compose run --rm ci
    TARGET=graphicsmagick docker compose run --rm ci
    TARGET=redis docker compose run --rm ci
    TARGET=wand docker compose run --rm ci
    TARGET=dbm docker compose run --rm ci
    TARGET=vips docker compose run --rm ci
    TARGET=qa docker compose run --rm ci

Run all CI targets in sequence::

    for target in pil imagemagick graphicsmagick redis wand dbm vips qa; do
      echo "Testing $target..."
      TARGET=$target docker compose run --rm ci
    done

.. _GitHub Discussions: https://github.com/mariocesar/sorl-thumbnail/discussions
.. _GitHub Actions: https://github.com/mariocesar/sorl-thumbnail/actions
.. _Docker: https://www.docker.com/
.. _tox: https://tox.wiki/
.. _uv: https://docs.astral.sh/uv/
.. _Install Docker: https://docs.docker.com/get-docker/

Examples site
=============

The project homepage and the example galleries are a small Django project in ``demo/``,
exported to static files and published to GitHub Pages from ``main``. To work on it::

    uv run --group demo demo/manage.py runserver
    uv run --group demo demo/manage.py runserver --settings=demo.settings.wand

To export the site to ``site/`` and check it, as CI does::

    uv run --group demo demo/manage.py build

Adding an example is one template in ``demo/examples/`` and one line in
``demo/examples.py``, see ``demo/README.md``.

Sending pull requests
=====================

1. Fork the repo on GitHub and clone your fork::

    git clone git@github.com:<your-user>/sorl-thumbnail.git

2. Create a branch for your specific changes::

    $ git checkout main
    $ git pull
    $ git checkout -b feature/foobar

   To simplify things, please, make one branch per issue (pull request).
   It's also important to make sure your branch is up-to-date with upstream main,
   so that maintainers can merge changes easily.

3. Commit changes. Please update docs, if relevant.

4. Don't forget to run tests to check than nothing breaks.

5. Ideally, write your own tests for new feature/bug fix.

6. Submit a `pull request`_.

.. _pull request: https://help.github.com/articles/using-pull-requests

Keep the branch to the change. Editor settings, fonts, build leftovers and the
like get flagged by a check that lists what to remove and labels the pull
request ``needs-cleanup`` until they are gone. The same check holds anything
that hides what it is, and closes a pull request that would run code on a
maintainer's machine when the branch is opened. The check is the
`pr-hygiene`_ action; the rules this project adds live in
``.github/pr-hygiene.yml``.

.. _pr-hygiene: https://github.com/mariocesar/pr-hygiene

Using AI tools
==============

Use whatever tools you like to write the change, but you are the one sending
it. That means:

* Mention in the description if you used AI, and for what.
* Run the tests and read the diff before you open the pull request.
* Reply when someone reviews it. Pull requests nobody answers for get closed.

We don't take pull requests sent by scripts that watch the issue tracker and
send a patch minutes later, even if the patch is right. New pull requests get
checked for this and the ones that look like it are turned into drafts with
the ``needs-author-verification`` label until the author replies. If that
doesn't happen in a week they are closed. You can ask to have one reopened.
