import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
STANDALONE = os.environ.get('PORTAL_STANDALONE') == '1'
DEBUG = os.environ.get('APP_ENV', 'development') == 'development'
DATA_DIR = Path(os.environ.get('DATA_DIR', str(BASE_DIR / 'data')))
DATA_DIR.mkdir(parents=True, exist_ok=True)
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if not DEBUG and not STANDALONE:
        raise ImproperlyConfigured('SECRET_KEY is required in production.')
    from django.core.management.utils import get_random_secret_key
    key_file = DATA_DIR / '.secret'
    if not key_file.exists():
        key_file.write_text(get_random_secret_key(), encoding='utf-8')
    SECRET_KEY = key_file.read_text(encoding='utf-8')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1,localhost,testserver').split(',')
INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'accounts', 'evaluations', 'exports',
]
MIDDLEWARE = [
    'accounts.maintenance.LocalMaintenanceMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'schoolportal.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'], 'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
        'evaluations.context.portal_context',
    ]}}]
WSGI_APPLICATION = 'schoolportal.wsgi.application'
if os.environ.get('PGHOST'):
    DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.environ['PGHOST'], 'PORT': os.environ.get('PGPORT', '5432'),
        'NAME': os.environ.get('PGDATABASE', 'schoolportal'),
        'USER': os.environ.get('PGUSER', 'schoolportal'),
        'PASSWORD': os.environ.get('PGPASSWORD', ''),
        'OPTIONS': {'sslmode': os.environ.get('PGSSLMODE', 'require')}}}
elif DEBUG or STANDALONE:
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DATA_DIR / 'schoolportal.sqlite3', 'OPTIONS': {'timeout': 20}}}
else:
    raise ImproperlyConfigured('Configure PostgreSQL for production (PGHOST).')
AUTH_USER_MODEL = 'accounts.User'
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE = 'nl-be'
TIME_ZONE = 'Europe/Brussels'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
DATA_UPLOAD_MAX_NUMBER_FIELDS = 20000
LOGIN_URL = '/aanmelden/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/aanmelden/'
SESSION_COOKIE_HTTPONLY = True
if STANDALONE:
    SESSION_COOKIE_NAME = 'portal_desktop_session'
    CSRF_COOKIE_NAME = 'portal_desktop_csrf'
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 28800
X_FRAME_OPTIONS = 'DENY'
if not DEBUG and not STANDALONE:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    CSRF_TRUSTED_ORIGINS = [s for s in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if s]
