from .base import *

DEBUG = True

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware", # required by django-debug-toolbar
] + MIDDLEWARE

# required by django-debug-toolbar
INTERNAL_IPS = [
    '127.0.0.1', 
]

THIRD_PARTY_APPS = [
    'debug_toolbar',
] + THIRD_PARTY_APPS

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS