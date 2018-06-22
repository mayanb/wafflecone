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

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_PASSWORD = os.environ.get("WAFFLE_ADMIN_EMAIL_PASSWORD")
EMAIL_HOST_USER = os.environ.get("WAFFLE_ADMIN_EMAIL_USER")
EMAIL_PORT = 587
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: change this before deploying to production!
SECRET_KEY = os.environ.get("WAFFLE_DJANGO_SECRET_KEY", '1234')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'rest_framework_docs',
    'rest_framework',
    'ics',
    'qr',
    'django_filters',
    'storages',
    'corsheaders',
    'gauth',
    'graphs',
    'rest_auth',
    #'dashboard', 
    #'silk',
)

MIDDLEWARE_CLASSES = (
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    #'silk.middleware.SilkyMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # 'social_django.middleware.SocialAuthExceptionMiddleware',
)


ROOT_URLCONF = 'logistics.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': True,
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

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
        'NAME': os.environ.get("WAFFLE_DB_NAME", ''),
        'USER': os.environ.get("WAFFLE_DB_USER", ''),
        'PASSWORD': os.environ.get("WAFFLE_DB_PASSWORD", ''),
        'HOST': os.environ.get("WAFFLE_DB_HOST", ''),
        'PORT': os.environ.get("WAFFLE_DB_PORT", ''),
    }
}

db_from_env = dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(db_from_env)

if 'test' in sys.argv:
    DATABASES['default']['NAME'] = 'ics'
    DATABASES['default']['USER'] = 'testuser'
    DATABASES['default']['HOST'] = 'localhost'
    DATABASES['default']['PORT'] = '5432'

#DATABASES['default'] =  dj_database_url.config()

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
}

REST_SESSION_LOGIN = False
REST_USE_JWT = True
JWT_AUTH = {
    'JWT_EXPIRATION_DELTA' : datetime.timedelta(days=7),
    'JWT_ALLOW_REFRESH' : True,
    'JWT_REFRESH_EXPIRATION_DELTA' : datetime.timedelta(days=21),
}
REST_AUTH_SERIALIZERS = {
    'USER_DETAILS_SERIALIZER': 'ics.v11.serializers.UserDetailSerializer',
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

# Allow all host headers
ALLOWED_HOSTS = ['*']

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_ROOT = os.path.join(PROJECT_ROOT, 'staticfiles')
# STATIC_URL = '/static/'

# Extra places for collectstatic to find static files.
STATICFILES_DIRS = (
     os.path.join(PROJECT_ROOT, 'static'),
 )

# Simplified static file serving.
# https://warehouse.python.org/project/whitenoise/
#STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'


#django-storages setup for leveraging s3
AWS_STORAGE_BUCKET_NAME = os.environ.get("WAFFLE_S3_BUCKET_NAME", '')
AWS_ACCESS_KEY_ID = os.environ.get("WAFFLE_AWS_ACCESS", '')
AWS_SECRET_ACCESS_KEY = os.environ.get("WAFFLE_AWS_SECRET", '')

 # Tell django-storages that when coming up with the URL for an item in S3 storage, keep
    # it simple - just use this domain plus the path. (If this isn't set, things get complicated).
    # This controls how the `static` template tag from `staticfiles` gets expanded, if you're using it.
    # We also use it in the next setting.
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

    # This is used by the `static` template tag from `static`, if you're using that. Or if anything else
    # refers directly to STATIC_URL. So it's safest to always set it.
STATIC_URL = "https://%s/static/" % AWS_S3_CUSTOM_DOMAIN

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
