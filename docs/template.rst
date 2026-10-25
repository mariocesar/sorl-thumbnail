*************************
Template tags and filters
*************************

.. highlight:: html+django

Sorl-thumbnail comes with one template tag `thumbnail`_ and three filters:
`is_portrait`_, `margin`_ and `resolution`_. To use any of them in you
templates you first need to load them::

    {% load thumbnail %}


.. _thumbnail:

thumbnail
=========

Syntax::

    {% thumbnail source geometry [key1=value1, key2=value2...] as var %}
    {% endthumbnail %}

Alternative syntax using empty::

    {% thumbnail source geometry [key1=value1, key2=value2...] as var %}
    {% empty %}
    {% endthumbnail %}

The ``{% empty %}`` section is rendered if the thumbnail source is resolved to
an empty value or an invalid image source, you can think of it as rendering
when the thumbnail becomes undefined.

.. _source:

Source
------

.. highlight:: python

Source can be an ImageField, FileField, a file name (assuming default_storage),
a url. What we need to know is name and storage, see how ImageFile figures
these things out::

    from django.utils.encoding import force_str

    class ImageFile(BaseImageFile):
        _size = None

        def __init__(self, file_, storage=None):
            if not file_:
                raise ThumbnailError('File is empty.')
            # figure out name
            if hasattr(file_, 'name'):
                self.name = file_.name
            else:
                self.name = force_str(file_)
            # figure out storage
            if storage is not None:
                self.storage = storage
            elif hasattr(file_, 'storage'):
                self.storage = file_.storage
            elif url_pat.match(self.name):
                self.storage = UrlStorage()
            else:
                self.storage = default_storage

Format
------

sorl-thumbnail supports these formats:

#. jpg, jpeg
#. png
#. gif
#. webp
#. avif  (the PIL engine needs pillow-avif-plugin, ImageMagick needs an AVIF encoder, see :ref:`image-library`)

to use different format for your images set this variable in your settings.

.. code-block:: python
     
    THUMBNAIL_FORMAT = 'JPEG'

Geometry
--------

.. highlight:: html+django

Geometry is specified as ``widthxheight``, ``width`` or ``xheight``.
Width and height are in pixels. Geometry can either be a string or resolve
into a valid geometry string. Examples::

    {% thumbnail item.image "200x100" as im %}
        <img src="{{ im.url }}">
    {% endthumbnail %}

    {% thumbnail item.image "200" as im %}
        <img src="{{ im.url }}">
    {% endthumbnail %}

    {% thumbnail item.image "x100" as im %}
        <img src="{{ im.url }}">
    {% endthumbnail %}

    {% thumbnail item.image geometry as im %}
        <img src="{{ im.url }}">
    {% endthumbnail %}

If width and height are given the image is rescaled to maximum values of height
and width given. Aspect ratio preserved.


Options
-------
Options are passed on to the backend and engine, the backend generates the
thumbnail filename from it and the engine can use it for processing. Option
keys are not resolved in context but values are. Passing all options to the
engine means that you can easily subclass an engine and create new features
like rounded corners or what ever processing you like. The options described
below are how they are used and interpreted in the shipped engines.

``cropbox``
^^^^^^^^^^^
This option is used to crop to a specific set of coordinates. ``cropbox`` takes
``x, y, x2, y2`` as arguments to crop the image down via those set of coordinates.
Note that ``cropbox`` is applied before ``crop``.

.. code-block:: python
    
    img = get_thumbnail(sorl_img, cropbox="{0},{1},{2},{3}".format(
                        x, y, x2, y2))

``crop``
^^^^^^^^
This option is only used if both width and height is given. Crop behaves much
like `css background-position`_.  The image is first rescaled to minimum values
of height and width given, this will be equivalent to the `padding box` in the
above text. After it is rescaled it will apply the cropping options. There are
some differences to the `css background-position`_:

- Only % and px are valid lengths (units)
- ``noop`` (No Operation) is a valid option which means there is no
  cropping after the initial rescaling to minimum of width and height.
- ``smart`` crops away the parts of the image with the least detail instead of
  cropping at a fixed position. It trims whichever side has less entropy, 10px
  at a time, until the image has the requested aspect ratio. The PIL and vips
  engines support it, vips with its own entropy measure, so it may keep a
  different part of the image. The other engines raise
  ``NotImplementedError``.

There are many overlapping options here for example ``center`` is equivalent to
``50%``. There is not a problem with that in it self but it is a bit of a
problem if you will for sorl-thumbnail. Sorl-thumbnail will generate a new
thumbnail for every unique source, geometry and options.  This is a design
choice because we want to stay flexible with the options and not interpret them
anywhere else but in the engine methods. In clear words, be consistent in your
cropping options if you don't want to generate unnecessary thumbnails. In case
you are wondering, sorl-thumbnail sorts the options so the order does not
matter, same options but in different order will generate only one thumbnail.

``remove_border``
^^^^^^^^^^^^^^^^^
Cuts away a plain border before the image is scaled, like the white margin of
a scanned page or the empty space around a logo::

    {% thumbnail item.image "100x100" remove_border=True as im %}

It walks in from each edge and cuts the strips that have almost no detail,
stopping where the picture starts. On a transparent image a strip counts as
plain when it looks plain on both a black and a white background. It cuts at
most 28% of the width or height from each side, so an image that is plain all
over is kept. Default value is ``False``. The PIL and vips engines support it.
The vips engine cuts the rows and columns that match the top left pixel's
color, so the two can differ by a few pixels. The other engines raise
``NotImplementedError``.

``upscale``
^^^^^^^^^^^
Upscale is a boolean and controls if the image can be upscaled or not. For
example if your source is 100x100 and you request a thumbnail of size 200x200
and upscale is False this will return a thumbnail of size 100x100. If upscale
was True this would result in a thumbnail size 200x200 (upscaled). The default
value is ``True``.

``quality``
^^^^^^^^^^^
Quality is a value between 0-100 and controls the thumbnail write quality.
Default value is ``95``.

``progressive``
^^^^^^^^^^^^^^^
This controls whether to save jpeg thumbnails as progressive jpegs. Default
value is ``True``.

``orientation``
^^^^^^^^^^^^^^^
This controls whether to orientate the resulting thumbnail with respect to the
source EXIF tags for orientation. Default value is ``True``.

``format``
^^^^^^^^^^
This controls the write format and thumbnail extension. Supported formats are
``'JPEG'``, ``'PNG'``, ``'GIF'``, ``'WEBP'`` and ``'AVIF'``. Default value is
``'JPEG'``.

JPEG has no transparency, so a transparent source written as JPEG shows the
color stored under its transparent pixels, which is usually black. Set
``THUMBNAIL_FLATTEN`` to get a white background instead, or write PNG with
``format='PNG'`` or ``THUMBNAIL_PRESERVE_FORMAT``, or flatten the image before
uploading it.

``colorspace``
^^^^^^^^^^^^^^
This controls the resulting thumbnails color space, valid values are: ``'RGB'``
and ``'GRAY'``. Default value is ``'RGB'``.

``padding``
^^^^^^^^^^^
Padding is a boolean and controls if the image should be padded to fit the
specified geometry.

If your image is ``200x100``::

  {% thumbnail image "100x100" padding=True as im %}

``im`` will be ``100x100`` with white padding at the top and bottom. The color
of the padding can be controlled with ``padding_color`` or the setting
``THUMBNAIL_PADDING_COLOR`` which defaults to ``#ffffff``.

Images are not padded by default, but this can be changed by setting
``THUMBNAIL_PADDING`` to ``True``.

``padding_color``
^^^^^^^^^^^^^^^^^
This is the color to use for padding the image. It defaults to ``#ffffff`` and
can be globally set with the setting ``THUMBNAIL_PADDING_COLOR``.

``flatten``
^^^^^^^^^^^
Pass ``flatten=False`` to write one thumbnail without the background that
``THUMBNAIL_FLATTEN`` adds::

    {% thumbnail item.image "100x100" flatten=False as im %}

``flatten="off"`` does the same. The PIL, wand, convert and vips engines honour
it, every other engine ignores it.

``density``
^^^^^^^^^^^
Resolution, in dots per inch, at which vector sources such as PDF, EPS or SVG
are rasterized before thumbnailing. ImageMagick and GraphicsMagick default to
``72``, which is far too coarse for a PDF page on a high resolution display::

    {% thumbnail doc.file "400x400" density=300 as im %}

Only the convert engine honours the special case for this option, other engines
will pass the option in the order given. It is passed to both ``convert``
and ``identify`` ahead of the source file, so sizing and output agree. It does
not change the pixel size of raster sources.

``authenticate``
^^^^^^^^^^^^^^^^
Password for reading an encrypted PDF::

    {% thumbnail doc.file "400x400" authenticate=doc.password as im %}

Only the convert engine with ImageMagick honours this option. GraphicsMagick's
``identify`` has no such flag, so it cannot size an encrypted PDF at all. The
``EngineError`` messages for a call carrying this option leave out the command
line and the tool's output, so the password never appears in them. Like every
thumbnail option it is still written to the ``sorl.thumbnail`` debug log.

``options``
^^^^^^^^^^^
Yes this option is called ``options``. This needs to be a context variable that
resolves to a dictionary. This dictionary can contain multiple options, for
example::

    options = {'colorspace': 'GRAY', 'quality': 75, 'crop': 'center'}

You can use this option together with the other options but beware that the
order will matter. As soon as the keyword ``options`` is encountered all the
options that have a key in ``options`` are overwritten. Similarly, options in
the ``options`` dict will be overwritten by options set after the options
keyword argument to the thumbnail tag.


is_portrait
===========
This filter returns True if the image height is larger than the image width.
Examples::

    {% thumbnail item.image "100x100" %}
    {% if item.image|is_portrait %}
        <div class="portrait">
            <img src="{{ im.url }}">
        </div>
    {% else %}
        <div class="landscape">
            <img src="{{ im.url }}">
        </div>
    {% endif %}
    {% endthumbnail %}

    {% if item.image|is_portrait %}
        {% thumbnail item.image "100x200" crop="center" %}
            <img src="{{ im.url }}">
        {% endthumbnail %}
    {% else %}
        {% thumbnail item.image "200x100" crop="center" %}
            <img src="{{ im.url }}">
        {% endthumbnail %}
    {% endif %}

The filter and the tag share one download of the source, so their order does
not matter. See :ref:`source-cache`.


margin
======
Margin is a filter for calculating margins against a padding box. For example
lets say you have an image ``item.image`` and you want to pad it vertically in
a 1000x1000 box, you would simply write::

    <div class="millxmill">
        <img src="{{ item.image.url }}" style="margin:{{ item.image|margin:"1000x1000" }}">
    </div>

The above is a rather synthetic example the more common use case is when you want
boxes of images of a certain size but you do not want to crop them::

    {% for profile in profiles %}
    <div>
        {% thumbnail profile.photo "100x100" as im %}
            <img src="{{ im.url }}" style="margin:{{ im|margin:"100x100" }}">
        {% empty %}
            <img src="ghost100x100.jpg">
        {% endthumbnail %}
    </div>
    {% enfor %}

The more problematic is to get the top margin, however the margin filter
outputs all values.

.. _css background-position: https://www.w3.org/TR/CSS2/colors.html#propdef-background-position

resolution
==========
Resolution is a filter for obtaining alternative resolution versions of the
thumbnail.  Your provided resolution must be one of the
``THUMBNAIL_ALTERNATIVE_RESOLUTIONS`` settings values (default: no alternative resolutions)

For example, let's say you have an image ``item.image`` and you want to
get the 2x DPI version of it.  You would simply write::

    <div class="millxmill">
        <img src="{{ item.image.url|resolution:"2x" }}">
    </div>
