from .base import *

DEBUG = True

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware", # required by django-debug-toolbar
] + MIDDLEWARE

INTERNAL_IPS = [
    '127.0.0.1', # required by django-debug-toolbar
]

DJANGO_APPS = [
    'django.contrib.staticfiles', # required by django-debug-toolbar
] + DJANGO_APPS

THIRD_PARTY_APPS = [
    'debug_toolbar',
] + THIRD_PARTY_APPS

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

STATIC_URL = "static/" # required by django-debug-toolbar

ALLOWED_HOSTS = [
    '223.130.139.5', 
    '127.0.0.1',
]

MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = "media/"