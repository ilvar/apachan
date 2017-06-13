"""
Django settings for apachan project.

Generated by 'django-admin startproject' using Django 1.10.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'SOME_RANDOM_KEY'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = []

INTERNAL_IPS = ['127.0.0.1']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    'pytils',
    'bootstrap_pagination',
    'bootstrap3',
    'debug_toolbar',
    'easy_thumbnails',

    'apa',
    'newapa',
    'karma',
    'inbox',
    'logs',
    'anal',
]

MIDDLEWARE = [
    'django_dont_vary_on.middleware.RemoveUnneededVaryHeadersMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'apa.middleware.AnonTrackingMiddleware',
    'apa.middleware.SettingsMiddleware',
    'newapa.middleware.FavoritesMiddleware',
    'karma.middleware.WalletMiddleware',
]

DEBUG_TOOLBAR_CONFIG = {
    'RESULTS_CACHE_SIZE': 1000,
}

ROOT_URLCONF = 'apachan.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apa.context.categories',
                'apa.context.search_question',
                'karma.context.wallet',
            ],
        },
    },
]

WSGI_APPLICATION = 'apachan.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'apachan',
        'USER': '',
        'PASSWORD': '',
    },
    'experiments': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'apachan',
        'USER': '',
        'PASSWORD': '',
    }
    
}


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

SITE_ID = 1

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/'

THUMBNAIL_EXTENSION = 'jpg'
THUMBNAIL_PRESERVE_EXTENSIONS = ('png', 'gif')

THUMBNAIL_ALIASES = {
    'newapa.NewImage.image': {
        'thumb': {'size': (200, 200), 'crop': True, 'sharpen': True},
        'preview': {'size': (600, 600), 'crop': False},
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_COOKIE_AGE = 120960000

AGE_TO_POST_MINUTES = 30

ROLLBAR = {}

try:
    from settings_local import *
except ImportError:
    pass


if not DEBUG and ROLLBAR:
    MIDDLEWARE += (
        'rollbar.contrib.django.middleware.RollbarNotifierMiddleware',
    )