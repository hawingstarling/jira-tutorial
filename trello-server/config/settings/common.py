import os
from configurations import Configuration
from pathlib import Path
import dj_database_url
from datetime import timedelta

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
    'rest_framework_simplejwt',
    'corsheaders',

    # Your apps
    'apps.users', # App must be before organizations
    'apps.orgs',
    'apps.boards',
    'apps.audit_logs',
    'apps.api',
    # 'organizations'
  ]

  # Custom model
  ORGANIZATIONS_ORGANIZATION_MODEL = "apps.orgs.Organization"
  ORGANIZATIONS_ORGANIZATION_USER_MODEL = "apps.orgs.OrganizationUser"
  ORGANIZATIONS_ORGANIZATION_OWNER_MODEL = "apps.orgs.OrganizationOwner"

  # User model
  # AUTH_USER_MODEL = "apps.users"

  MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
  ]

  REST_FRAMEWORK = {
    # Authentication classes
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    
    # Permission classes
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    
    # Pagination
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    
    # Filtering
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    
    # Throttling (Rate limiting)
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',  # Anonymous users
        'user': '1000/hour',  # Authenticated users
    },
    
    # Renderer classes
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    
    # Exception handler
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    
    # Datetime format
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S.%fZ',
  }

  SIMPLE_JWT = {
    # Access token lifetime
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    
    # Refresh token lifetime
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    
    # Rotate refresh tokens
    'ROTATE_REFRESH_TOKENS': True,
    
    # Blacklist after rotation (requires rest_framework_simplejwt.token_blacklist)
    'BLACKLIST_AFTER_ROTATION': True,
    
    # Algorithm
    'ALGORITHM': 'HS256',
    
    # Signing key
    'SIGNING_KEY': os.environ.get('JWT_SECRET_KEY', 'your-secret-key-here'),
    
    # Token classes
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    
    # Token header
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    
    # User ID claim
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    # Token backend
    'TOKEN_OBTAIN_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenObtainPairSerializer',
  }

  # ============================================
  # CACHE CONFIGURATION - Redis (PRODUCTION)
  # ============================================
  CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            
            # Connection pool
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            
            # Timeouts
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            
            # Serializer
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
            
            # Compression (optional)
            # 'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        },
        
        # Key prefix to avoid conflicts
        'KEY_PREFIX': 'django_org',
        
        # Default timeout (seconds)
        'TIMEOUT': 300,  # 5 minutes
    }
  }

  # Allow Next.js frontend to make requests
  CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",

    # Production domain
    # https://yourdomain.com
  ]

  # Allow credentials (cookies, auth headers)
  CORS_ALLOW_CREDENTIALS = True
  # Allow specific methods
  CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
  ]
  # Allow specific headers
  CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
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

      # Connection pooling
      # 'CONN_MAX_AGE': 600,  # Keep connections alive for 10 minutes
        
      # PostgreSQL specific options
      # 'OPTIONS': {
      #     # Enable persistent connections
      #     'connect_timeout': 10,
          
      #     # SSL mode (for production)
      #     # 'sslmode': 'require',
      # },
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
#   LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
    
#     'formatters': {
#         'verbose': {
#             'format': '{levelname} {asctime} {module} {message}',
#             'style': '{',
#         },
#         'simple': {
#             'format': '{levelname} {message}',
#             'style': '{',
#         },
#     },
    
#     'handlers': {
#         'console': {
#             'class': 'logging.StreamHandler',
#             'formatter': 'verbose',
#         },
#         'file': {
#             'class': 'logging.handlers.RotatingFileHandler',
#             'filename': os.path.join(BASE_DIR, 'logs/django.log'),
#             'maxBytes': 1024 * 1024 * 10,  # 10 MB
#             'backupCount': 5,
#             'formatter': 'verbose',
#         },
#     },
    
#     'loggers': {
#         'django': {
#             'handlers': ['console', 'file'],
#             'level': 'INFO',
#             'propagate': False,
#         },
#         'django.db.backends': {
#             'handlers': ['console'],
#             'level': 'DEBUG',  # Log all SQL queries
#             'propagate': False,
#         },
#         'your_app': {
#             'handlers': ['console', 'file'],
#             'level': 'DEBUG',
#             'propagate': False,
#         },
#     },
# }

# # ============================================
# # PERFORMANCE & OPTIMIZATION
# # ============================================

# # Use persistent connections
# CONN_MAX_AGE = 600

# # File upload settings
# FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB
# DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB

# # Security settings for production
# if not DEBUG:
#     SECURE_SSL_REDIRECT = True
#     SESSION_COOKIE_SECURE = True
#     CSRF_COOKIE_SECURE = True
#     SECURE_BROWSER_XSS_FILTER = True
#     SECURE_CONTENT_TYPE_NOSNIFF = True
#     X_FRAME_OPTIONS = 'DENY'
    
#     # HSTS settings
#     SECURE_HSTS_SECONDS = 31536000  # 1 year
#     SECURE_HSTS_INCLUDE_SUBDOMAINS = True
#     SECURE_HSTS_PRELOAD = True

# # ============================================
# # MONITORING & DEBUGGING (Development)
# # ============================================

# if DEBUG:
#     # Django Debug Toolbar
#     INSTALLED_APPS += ['debug_toolbar']
#     MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
#     INTERNAL_IPS = ['127.0.0.1']
    
#     # Show SQL queries in console
#     LOGGING['loggers']['django.db.backends']['level'] = 'DEBUG'
