from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SITE_DIR = BASE_DIR.parent / 'site'

SECRET_KEY = 'demo-only'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']

INSTALLED_APPS = [
    'sorl.thumbnail',
    'demo',
]
ROOT_URLCONF = 'demo.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'APP_DIRS': True,
}]

MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
        # Relative URLs, so the exported pages work under any path
        'OPTIONS': {'location': MEDIA_ROOT, 'base_url': 'media/'},
    },
}

THUMBNAIL_DEBUG = True
THUMBNAIL_KVSTORE = 'sorl.thumbnail.kvstores.dbm_kvstore.KVStore'
