import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-default-key')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = 'pos'

# Session optimization
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = False  # ← SỬA: Chỉ save khi có thay đổi
SESSION_COOKIE_AGE = 12000
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'app_quan_ly',
    'django.contrib.humanize',
]

# ← BỎ LOGGING khi production (chỉ để local debug)
if DEBUG:
    LOGGING = {
        'version': 1,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'django.db.backends': {
                'handlers': ['console'],
                'level': 'DEBUG',
            },
        },
    }

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',  # ← THÊM LẠI
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
# Whitenoise settings (gộp lại, bỏ duplicate)
WHITENOISE_AUTOREFRESH = DEBUG
WHITENOISE_USE_FINDERS = DEBUG
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_ALLOW_ALL_ORIGINS = True
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = []
WHITENOISE_MAX_AGE = 31536000

if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
else:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

# Database
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'postgres'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', '210219'),
            'HOST': os.getenv('DB_HOST', '127.0.0.1'),
            'PORT': os.getenv('DB_PORT', '5433'),
            'CONN_MAX_AGE': 600,
        }
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Security (production)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True