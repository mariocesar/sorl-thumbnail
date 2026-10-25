from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template import loader

from .models import Item


def direct_to_template(request, template, mimetype=None, **kwargs):
    t = loader.get_template(template)
    return HttpResponse(t.render({'request': request}), content_type=mimetype)


def item(request, pk):
    return render(request, 'item.html', {'item': get_object_or_404(Item, pk=pk)})
