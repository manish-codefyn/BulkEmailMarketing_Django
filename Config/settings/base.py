import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-default-key-for-dev-only')

DEBUG = False

ALLOWED_HOSTS = []

# Add to your existing email settings
SITE_URL = os.getenv('SITE_URL', 'http://localhost:8000')

# Email sending throttling (optional)


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',
    
    # Third-party apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_quill',
    # Local apps
    'campaigns',
    'subscribers',
    'core',
]

DEFAULT_CONFIG = {
    "theme": "snow",
    "modules": {
        "syntax": True,
        "toolbar": [
            [
                {"font": []},
                {"header": []},
                {"align": []},
                "bold",
                "italic",
                "underline",
                "strike",
                "blockquote",
                {"color": []},
                {"background": []},
            ],
            ["code-block", "link", "image", "video"],
            ["clean"],
        ],
        # quill-image-compress
        "imageCompressor": {
            "quality": 0.8,
            "maxWidth": 2000,
            "maxHeight": 2000,
            "imageType": "image/jpeg",
            "debug": False,
            "suppressErrorLogging": True,
        },
        # quill-resize
        "resize": {
            "showSize": True,
            "locale": {},
        },
    },
}
MEDIA_JS = [
    # syntax-highlight
    "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/highlight.min.js",
    # quill
    "https://cdn.quilljs.com/1.3.7/quill.min.js",
    # quill-image-compress
    "https://cdn.jsdelivr.net/npm/quill-image-compress@1.2.21/dist/quill.imageCompressor.min.js",
    # quill-resize
    "https://cdn.jsdelivr.net/npm/@botom/quill-resize-module@2.0.0/dist/quill-resize-module.min.js",
    # custom
    "django_quill/django_quill.js",
]
MEDIA_CSS = [
    # syntax-highlight
    "https://cdn.quilljs.com/1.3.7/quill.snow.css",
    "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/styles/darcula.min.css",
    # quill-resize
    "https://cdn.jsdelivr.net/npm/quill-resize-module@1.2.4/dist/resize.min.css",
    # custom
    "django_quill/django_quill.css",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'Config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                 'utils.context_processors.site_settings',  
            ],
              'libraries': {  
                'custom_filters': 'templatetags.custom_filters',
            }
        },
    },
]

WSGI_APPLICATION = 'Config.wsgi.application'

DATABASES = {
    'default': {

        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        # 'ENGINE': 'django.db.backends.postgresql',
        # 'NAME': os.getenv('DB_NAME', 'email_marketing'),
        # 'USER': os.getenv('DB_USER', 'postgres'),
        # 'PASSWORD': os.getenv('DB_PASSWORD', ''),
        # 'HOST': os.getenv('DB_HOST', 'localhost'),
        # 'PORT': os.getenv('DB_PORT', '5432'),
    }
}

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

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]


MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Allauth settings
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1


# --- Django AllAuth modern settings ---
ACCOUNT_LOGIN_METHODS = {'username', 'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']

# ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True
ACCOUNT_SESSION_REMEMBER = True
from django.urls import reverse_lazy
LOGIN_REDIRECT_URL = reverse_lazy('core:dashboard')
LOGOUT_REDIRECT_URL = 'account_login'
# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"





SITE_NAME = 'Default Site'
DEFAULT_LOGO_URL = '/static/image/logo.png'
DEFAULT_FAVICON_URL= '/static/image/favicon/favicon.ico'
SITE_EMAIL = 'info@example.com'
SITE_MOBILE = ''
SITE_ADDRESS = 'Siliguri'
# settings.py

SITE_NAME = "Codefyn Software Solutions"
SITE_DESCRIPTION = "Powerful email marketing for businesses of all sizes. Boost your business with our cutting-edge email tools."


# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = os.getenv('EMAIL_PORT', 587)
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', True)
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'no-reply@codefyn.com')
EMAIL_THROTTLE = int(os.getenv('EMAIL_THROTTLE', 10))  # Emails per second (0 for no limit)
EMAIL_TIMEOUT = 30  # Increase timeout for bulk sending

# Security settings (override in production)
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False


# Celery settings
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
# CELERY_WORKER_PREFETCH_MULTIPLIER = 1
# CELERY_ACKS_LATE = True

if 'sqlite' in DATABASES['default']['ENGINE']:
    CELERY_TASK_ALWAYS_EAGER = True  # Run tasks synchronously in development
CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5 minutes
CELERY_TASK_TIME_LIMIT = 600  # 10 minutes
CELERY_TASK_ACKS_LATE = True  # Matches your acks_late=True
# Email sending configuration
EMAIL_BATCH_SIZE = 50  # Number of emails per batch
EMAIL_THROTTLE = 0.1  # Seconds between batches (0 for no delay)

# Logging configuration
import os

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',  # You can adjust the level as per your need (DEBUG, INFO, etc.)
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/email_campaigns.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'campaigns': {
            'handlers': ['file', 'console'],
            'level': 'INFO',  # You can change this to DEBUG for more verbose logs in your email campaign tasks
            'propagate': False,
        },
        'celery': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',  # Log all Celery-related events (debug level will give the most detail)
            'propagate': True,
        },
    },
}


# Custom error pages
handler404 = 'core.views.handler404'
handler500 = 'core.views.handler500'


