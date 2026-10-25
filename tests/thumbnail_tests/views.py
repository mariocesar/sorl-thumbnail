from asgiref.sync import sync_to_async
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template import loader

from sorl.thumbnail import get_thumbnail
from sorl.thumbnail.templatetags.thumbnail import is_portrait

from .models import Item


def direct_to_template(request, template, mimetype=None, **kwargs):
    t = loader.get_template(template)
    return HttpResponse(t.render({'request': request}), content_type=mimetype)


def item(request, pk):
    return render(request, 'item.html', {'item': get_object_or_404(Item, pk=pk)})


async def item_async(request, pk):
    item = await Item.objects.aget(pk=pk)
    # Two worker thread calls, as an async view uses sorl
    portrait = await sync_to_async(is_portrait)(item.image)
    im = await sync_to_async(get_thumbnail)(item.image, '100x100')
    return HttpResponse('%s %s' % ('portrait' if portrait else 'landscape', im.url))
