from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from demo import views

urlpatterns = [
    path('', views.home),
    path('index.html', views.home),
    path('demo-<str:engine>.html', views.gallery),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
