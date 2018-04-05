import sys

"""
Django settings for logistics project, on Heroku. For more info, see:
https://github.com/heroku/heroku-django-template
For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/
For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

import os
import dj_database_url
import datetime

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: change this before deploying to production!
SECRET_KEY = os.environ.get("WAFFLE_DJANGO_SECRET_KEY", '1234')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False


# Application definition

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.postgres',
    'ics',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
)

ROOT_URLCONF = 'logistics.urls'


WSGI_APPLICATION = 'logistics.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': 'ics',
#         'USER': 'ishita',
#         'PASSWORD': '',
#         'HOST': 'localhost',
#         'PORT': '',
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'ics',
        'USER': 'testuser',
        'PASSWORD': os.environ.get("WAFFLE_DB_PASSWORD", ''),
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalizationx
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


#django-storages setup for leveraging s3
AWS_STORAGE_BUCKET_NAME = os.environ.get("WAFFLE_S3_BUCKET_NAME", '')

 # Tell django-storages that when coming up with the URL for an item in S3 storage, keep
    # it simple - just use this domain plus the path. (If this isn't set, things get complicated).
    # This controls how the `static` template tag from `staticfiles` gets expanded, if you're using it.
    # We also use it in the next setting.
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME


AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
    # Tell the staticfiles app to use S3Boto storage when writing the collected static files (when
    # you run `collectstatic`).
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_S3_HOST = "s3-us-west-1.amazonaws.com"
S3_USE_SIGV4 = True

GOOGLE_OAUTH2_CLIENT_ID = os.environ.get("WAFFLE_GOOGLE_OAUTH2_CLIENT_ID", '')
GOOGLE_OAUTH2_CLIENT_SECRET = os.environ.get("WAFFLE_GOOGLE_OAUTH2_CLIENT_SECRET", '')
GOOGLE_OAUTH2_API_KEY = os.environ.get("WAFFLE_GOOGLE_OAUTH2_API_KEY", '')
GOOGLEAUTH_CALLBACK_DOMAIN = os.environ.get("WAFFLE_GOOGLEAUTH_CALLBACK_DOMAIN", '')

GOOGLEAUTH_SCOPE = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/plus.login',
    'https://www.googleapis.com/auth/plus.me',
    'https://www.googleapis.com/auth/drive'
]

CORS_ORIGIN_ALLOW_ALL = True
#CORS_ORIGIN_WHITELIST = os.environ.get("WAFFLE_CORS_ORIGIN_WHITELIST", '').split(' ')
CORS_ALLOW_CREDENTIALS = True

from corsheaders.defaults import default_headers

CORS_ALLOW_HEADERS = default_headers + (
    'process-data',
    'processData'
)



CSRF_TRUSTED_ORIGINS = os.environ.get("WAFFLE_CORS_ORIGIN_WHITELIST", '').split(' ')

INTERNAL_IPS = ['127.0.0.1', '192.168.0.119', '10.0.1.184']

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

import logging
#logging.disable(logging.CRITICAL)

