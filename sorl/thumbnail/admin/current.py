import logging

from django.contrib.admin.widgets import AdminFileWidget
from django.utils.safestring import mark_safe

from sorl.thumbnail.fields import ImageField
from sorl.thumbnail.shortcuts import get_thumbnail

logger = logging.getLogger(__name__)


class AdminImageWidget(AdminFileWidget):
    """
    An ImageField Widget for django.contrib.admin that shows a thumbnailed
    image as well as a link to the current one if it hase one.
    """

    def render(self, name, value, attrs=None, **kwargs):
        output = super().render(name, value, attrs, **kwargs)
        if value and hasattr(value, 'url'):
            ext = 'JPEG'
            try:
                aux_ext = str(value).split('.')
                if aux_ext[len(aux_ext) - 1].lower() == 'png':
                    ext = 'PNG'
                elif aux_ext[len(aux_ext) - 1].lower() == 'gif':
                    ext = 'GIF'
            except Exception:
                pass
            try:
                mini = get_thumbnail(value, 'x80', upscale=False, format=ext, raise_errors=False)
            except Exception as e:
                logger.warning("Unable to get the thumbnail", exc_info=e)
            else:
                try:
                    output = (
                        '<div style="float:left">'
                        '<a style="width:%spx;display:block;margin:0 0 10px" class="thumbnail" '
                        'target="_blank" href="%s">'
                        '<img src="%s"></a>%s</div>'
                    ) % (mini.width, value.url, mini.url, output)
                except (AttributeError, TypeError):
                    pass
        return mark_safe(output)


class AdminImageMixin:
    """
    This is a mix-in for InlineModelAdmin subclasses to make ``ImageField``
    show nicer form widget
    """

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if isinstance(db_field, ImageField):
            return db_field.formfield(widget=AdminImageWidget)
        return super().formfield_for_dbfield(db_field, request, **kwargs)
