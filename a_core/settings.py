
import os
from pathlib import Path
from environ import Env

BASE_DIR = Path(__file__).resolve().parent.parent

env = Env()
env.read_env(os.path.join(BASE_DIR, ".env"))

ENVIRONMENT = env('ENVIRONMENT', default="production")
# ENVIRONMENT = "development"




# Project title displayed in the header
PROJECT_TITLE = "Chat App"


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')


# SECURITY WARNING: don't run with debug turned on in production!
if ENVIRONMENT == 'development':
    DEBUG = True
else:
    DEBUG = False


ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'chat-app-mvol.onrender.com']

CSRF_TRUSTED_ORIGINS = [ 'https://chat-app-mvol.onrender.com' ]


# Application definition

INSTALLED_APPS = [
    'daphne',
    'channels',
    'channels_redis',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_cleanup.apps.CleanupConfig',
    'django_htmx',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    # My apps
    'a_home',
    'a_users',
    'a_rtchat', 
    
    # Third party
    'django_browser_reload',
    'cloudinary_storage',
    'cloudinary',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

if DEBUG:
    MIDDLEWARE += ['django_browser_reload.middleware.BrowserReloadMiddleware']


AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ROOT_URLCONF = 'a_core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ BASE_DIR / 'templates' ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'a_home.cprocs.project_title',
                'a_rtchat.context_processors.user_groupchats',
            ],
        },
    },
]

# WSGI_APPLICATION = 'a_core.wsgi.application'

ASGI_APPLICATION = 'a_core.asgi.application'

# In settings.py
if ENVIRONMENT == 'development':
    CHANNEL_LAYERS = {
        'default': {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [env('REDIS_URL')],  
            },
        },
    }

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

if ENVIRONMENT == 'development':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(env('DATABASE_URL'))
    }

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/' 
STATICFILES_DIRS = [ BASE_DIR / 'static' ]
STATIC_ROOT = BASE_DIR / 'staticfiles'


# settings.py
if ENVIRONMENT == 'development':
    MEDIA_ROOT = BASE_DIR / 'media'
    MEDIA_URL = '/media/'
else:
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    CLOUDINARY_STORAGE = {
        'CLOUDINARY_URL': env('CLOUDINARY_URL'),
        'SECURE': True,
        'MEDIA_TAG': 'media',
        'INVALID_VIDEO_ERROR_MESSAGE': 'Please upload a valid video file.',
        'EXCLUDE_DELETE_ORPHANED_MEDIA_PATHS': (),
        'STATICFILES_MANIFEST_ROOT': None
    }
    MEDIA_URL = '/media/'  

    
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = '/'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST='smtp.gmail.com'
EMAIL_HOST_USER=env('EMAIL_ADDRESS')
EMAIL_HOST_PASSWORD=env('EMAIL_HOST_PASSWORD')
EMAIL_PORT=587
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=f"chatapp(env('EMAIL_HOST_PASSWORD'))"
ACCOUNT_EMAIL_SUBJECT_PREFIX=''

ACCOUNT_LOGIN_METHODS = {'email', 'username'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']


# Add this to your settings.py to debug Redis connection
import logging
logger = logging.getLogger('channels_redis')
logger.setLevel(logging.DEBUG)