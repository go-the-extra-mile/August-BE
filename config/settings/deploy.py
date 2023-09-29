from .base import *

DEBUG = False

ALLOWED_HOSTS = [
    '223.130.139.5',
    'ec2-15-164-218-52.ap-northeast-2.compute.amazonaws.com',
]

DEPLOY_DB_USER = get_secret('DEPLOY_DB_USER')
DEPLOY_DB_PASSWORD = get_secret('DEPLOY_DB_PASSWORD')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'august-db',
        'USER': DEPLOY_DB_USER,
        'PASSWORD': DEPLOY_DB_PASSWORD,
        'HOST': 'localhost',
        'PORT': '',
    }
}

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'
