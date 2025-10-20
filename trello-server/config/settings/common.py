from configurations import Configuration
from pathlib import Path
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

class Common(Configuration):

  # Application definition
  INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'rest_framework',            # utilities for rest apis
    'rest_framework.authtoken',  # token authentication

    # Your apps
    'apps.users',
    'apps.organizations',
    'apps.boards',
    'apps.audit_logs'
  ]

  MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
  ]

  ALLOWED_HOSTS = ["*"]
  ROOT_URLCONF = 'config.urls'
  # SECURITY WARNING: keep the secret key used in production secret!
  SECRET_KEY = 'django-insecure-kq4z@g$)c(*j&bppmsrb_ygmnv5-1r=@tg=%6#h%o_2b20^+(#'
  WSGI_APPLICATION = 'config.wsgi.application'

  # Email

  # Postgres
  DATABASES = {
    # 'default': dj_database_url.config(
    #         default='postgres://postgres:@postgres:5432/postgres',
    #         conn_max_age=int(os.getenv('POSTGRES_CONN_MAX_AGE', 600))
    #     )
    'default': {
      'ENGINE': 'django.db.backends.postgresql_psycopg2',
      'NAME': 'trello_tutorial',
      'USER': 'postgres',
      'PASSWORD': 'hungdat!234',
      'HOST': 'localhost',
      'PORT': '5433'
    }
  }

  # General
  TIME_ZONE = 'UTC'
  LANGUAGE_CODE = 'en-us'
  # If you set this to False, Django will make some optimizations so as not
  # to load the internationalization machinery.
  USE_I18N = False
  USE_L10N = True
  USE_TZ = True

  # Static files (CSS, JavaScript, Images)
  # https://docs.djangoproject.com/en/2.0/howto/static-files/
  STATIC_URL = 'static/'

  # Default primary key field type
  # https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field
  DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

  # Media files

  TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
  ]
  
  DEBUG = True

  # Password validation
  # https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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

# Logging

