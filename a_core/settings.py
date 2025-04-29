import os
from pathlib import Path
from decouple import config
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-4z9z$ol)gal^i34j9)jgd*$grj7uawm18whufdwk70ath662v2'

# SECURITY WARNING: don't run with debug turned on in production!
ENVIRONMENT = config('ENVIRONMENT')

print(f"ENVIRONMENT: {ENVIRONMENT}")

GEMINI_API_KEY = config('GEMINI_API_KEY')

INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]

if ENVIRONMENT == 'development':
    DEBUG = True
else:
    DEBUG = False

ALLOWED_HOSTS = ['127.0.0.1', 'memento-vault.onrender.com']

CSRF_TRUSTED_ORIGINS = [ 'https://*' ]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # cloudinary
    # 'cloudinary_storage',
    # 'cloudinary',

    # allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    # my_apps
    'users.apps.UsersConfig',
    'vaults.apps.VaultsConfig',
    'a_auth.apps.AAuthConfig',

    # instlled apps
    'active_link',
    'django_htmx',
    'django.contrib.humanize',
    'taggit',
    'storages',
    'debug_toolbar',
]

SITE_ID = 1


# Allauth Provider specific settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
            'prompt': 'consent',
        }
    }
}


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',

    "allauth.account.middleware.AccountMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
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
            ],
        },
    },
]

WSGI_APPLICATION = 'a_core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases


# sqlite3 DB
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

#
if ENVIRONMENT == 'production':
    DATABASES['default'] = dj_database_url.parse(config('DATABASE_URL'))


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

POSTGRES_LOCALLY = False
#
if ENVIRONMENT == 'production' or POSTGRES_LOCALLY:
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
        },
        "staticfiles": {
            # "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
            "BACKEND": "storages.backends.s3.S3Storage",
        },
    }
    
    AWS_ACCESS_KEY_ID=config('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY=config('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME=config('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME=config('AWS_S3_REGION_NAME')
    AWS_S3_CUSTOM_DOMAIN = config('AWS_S3_CUSTOM_DOMAIN')
    AWS_S3_FILE_OVERWRITE = False
    AWS_LOCATION = 'media'
else:
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True

# Allauth settings
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_AUTO_SIGNUP = True
ACCOUNT_UNIQUE_EMAIL = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"

ACCOUNT_ADAPTER = "a_auth.adapters.CustomAccountAdapter"
SOCIALACCOUNT_ADAPTER = "a_auth.adapters.SocialAccountAdapter"


LOGIN_REDIRECT_URL = '/dashboard/'


# CORS settings
CORS_ALLOWED_ORIGINS = ['https://memento-vault.onrender.com']
CSRF_TRUSTED_ORIGINS = ['https://memento-vault.onrender.com']



