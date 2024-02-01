from .base import *

DEBUG = False

ALLOWED_HOSTS = [
    get_secret('DEPLOY_HOST'),
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

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'

DJANGO_APPS += [
    'django.contrib.staticfiles'
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

CSRF_TRUSTED_ORIGINS = [
    get_secret('DEPLOY_HOST_PORT'),
]
