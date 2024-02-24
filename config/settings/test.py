from .base import *

DEBUG = True

ALLOWED_HOSTS = [
    '127.0.0.1',
]

DEPLOY_DB_NAME = get_secret('DEPLOY_DB_NAME')
DEPLOY_DB_USER = get_secret('DEPLOY_DB_USER')
DEPLOY_DB_PASSWORD = get_secret('DEPLOY_DB_PASSWORD')
DEPLOY_DB_HOST = get_secret('DEPLOY_DB_HOST')
DEPLOY_DB_PORT = get_secret('DEPLOY_DB_PORT')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': DEPLOY_DB_NAME,
        'USER': DEPLOY_DB_USER,
        'PASSWORD': DEPLOY_DB_PASSWORD,
        'HOST': DEPLOY_DB_HOST,
        'PORT': DEPLOY_DB_PORT,
    }
}

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


MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = "media/"

SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = timedelta(hours=1)