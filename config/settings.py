"""
Django settings for the Human vs AI Art Detector.

Local single-page tool: no database, no auth, no sessions.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# Set SECRET_KEY in the environment for deployment; the default is dev-only.
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure--)3rz@wvab6fy%9im4))+k)&)icr%(2_68**k(7++(8llw+s_t',
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# App has no auth/DB; the HF Space subdomain varies, so accept any host.
ALLOWED_HOSTS = ['*']

# Behind HF Spaces' HTTPS proxy: trust the forwarded scheme + Space origin
# so CSRF checks pass on the POST forms in /detect/.
CSRF_TRUSTED_ORIGINS = ['https://*.hf.space']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# Send cookies only over HTTPS in production (served HTTPS-only on HF Spaces).
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG

INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'detector',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {}

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# Uploaded artwork stays in memory; generous cap for phone photos.
DATA_UPLOAD_MAX_MEMORY_SIZE = 15 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 15 * 1024 * 1024

# Model source. In deployment, set ML_MODEL_REPO to a Hugging Face model repo
# (e.g. "user/human-vs-ai-art"); get_model() downloads + caches the weights.
# Without it, fall back to the local file for development.
ML_MODEL_REPO = os.environ.get('ML_MODEL_REPO')
ML_MODEL_FILENAME = os.environ.get('ML_MODEL_FILENAME', 'best_model.keras')
ML_MODEL_PATH = BASE_DIR / 'models' / 'best_model.keras'
