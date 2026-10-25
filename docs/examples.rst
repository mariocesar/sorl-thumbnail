********
Examples
********

Template examples
=================

.. highlight:: html+django

All of the examples assume that you first load the ``thumbnail`` template tag in
your template::

    {% load thumbnail %}

Simple::

    {% thumbnail item.image "100x100" crop="center" as im %}
        <img src="{{ im.url }}" width="{{ im.width }}" height="{{ im.height }}">
    {% endthumbnail %}

    
Crop using margin filter, x, y aliases::

    {% thumbnail item.image "100x700" as im %}
        <img style="margin:{{ im|margin:"100x700" }}" src="{{ im.url }}" width="{{ im.x }}" height="{{ im.y }}">
    {% endthumbnail %}

Using external images and advanced cropping::

    {% thumbnail "http://www.aino.se/media/i/logo.png" "40x40" crop="80% top" as im %}
        <img src="{{ im.url }}">
    {% endthumbnail %}

Using the empty feature, the empty section is rendered when the source is
resolved to an empty value or an invalid image source, you can think of it as
rendering when the thumbnail becomes undefined::

    {% thumbnail item.image my_size_string crop="left" as im %}
        <img src="{{ im.url }}">
    {% empty %}
        <p>No image</p>
    {% endthumbnail %}

Nesting tags and setting size (geometry) for width only::

    {% thumbnail item.image "1000" as big %}
        {% thumbnail item.image "50x50" crop="center" as small %}
            <a href="{{ big.url}}" title="look ma!"><img src="{{ small.url }}"></a>
        {% endthumbnail %}
    {% endthumbnail %}

Setting geometry for height only::

    {% thumbnail item.image "x300" as im %}
        <img src="{{ im.url }}">
    {% endthumbnail %}

Setting format and using the is_portrait filter::

    {% if item.image|is_portrait %}
        <div class="portrait">
        {% thumbnail item.image "100" crop="10px 10px" format="PNG" as im %}
            <img src="{{ im.url }}">
        {% endthumbnail %}
        </div>
    {% else %}
        <div class="landscape">
        {% thumbnail item.image "50" crop="bottom" format="PNG" as im %}
            <img src="{{ im.url }}">
        {% endthumbnail %}
        </div>
        <div>
            <p>Undefined behaviour</p>
        </div>
    {% endif %}

Using HTML filter::

    {{ text|html_thumbnails }}

Using markdown filter::

    {{ text|markdown_thumbnails }}

.. highlight:: python

Model examples
==============
Using ``sorl.thumbnail.ImageField`` in your models::

    from django.db import models
    from sorl.thumbnail import ImageField

    class Item(models.Model):
        image = ImageField(upload_to='whatever')


.. note:: You do not need to use the ``sorl.thumbnail.ImageField`` to use
    ``sorl.thumbnail``. The standard ``django.db.models.ImageField`` is fine
    except that using the ``sorl.thumbnail.ImageField`` lets you plugin the
    nice admin addition explained in the next section.


Another example on how to use ``sorl.thumbnail.ImageField`` in your existing
project with only small code changes::

    # util/models.py
    from django.db.models import *
    from sorl.thumbnail import ImageField

    # myapp/models.py
    from util import models

    class MyModel(models.Model):
        logo = ImageField(upload_to='/dev/null')


Admin examples
==============
Recommended usage using ``sorl.thumbnail.admin.AdminImageMixin`` (note that this requires use of ``sorl.thumbnail.ImageField`` in your models as explained above)::

    # myapp/admin.py
    from django.contrib import admin
    from myapp.models import MyModel
    from sorl.thumbnail.admin import AdminImageMixin

    class MyModelAdmin(AdminImageMixin, admin.ModelAdmin):
        pass

And the same thing For inlines::

    # myapp/admin.py
    from django.contrib import admin
    from myapp.models import MyModel, MyInlineModel
    from sorl.thumbnail.admin import AdminImageMixin

    class MyInlineModelAdmin(AdminImageMixin, admin.TabularInline):
        model = MyInlineModel

    class MyModelAdmin(admin.ModelAdmin):
        inlines = [MyInlineModelAdmin]

Easy to plugin solution example with little code to change::

    # util/admin.py
    from django.contrib.admin import *
    from sorl.thumbnail.admin import AdminImageMixin

    class ModelAdmin(AdminImageMixin, ModelAdmin):
        pass

    class TabularInline(AdminImageMixin, TabularInline):
        pass

    class StackedInline(AdminImageMixin, StackedInline):
        pass

    # myapp/admin.py
    from util import admin
    from myapp.models import MyModel

    class MyModelAdmin(admin.ModelAdmin):
        pass


Low level API examples
======================
How to get make a thumbnail in your python code::

    from sorl.thumbnail import get_thumbnail

    im = get_thumbnail(my_file, '100x100', crop='center', quality=99)


How to delete a file, its thumbnails as well as references in the Key Value
Store::

    from sorl.thumbnail import delete

    delete(my_file)


.. _source-cache-in-a-job:

Reading a source once in a job
------------------------------
Within a request sorl-thumbnail downloads a source once however many
thumbnails and filters use it (see :ref:`source-cache`). A management command
or a background job has no request, so wrap the work for each image in
``source_cache``::

    from sorl.thumbnail import get_thumbnail, source_cache

    for item in Item.objects.all():
        with source_cache():
            for geometry in ('100x100', '400x400', '800x800'):
                get_thumbnail(item.image, geometry)

The block keeps the last source read and drops it when the block ends, also
when it raises.

