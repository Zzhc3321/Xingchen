import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-change-me-in-production'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'daphne',  # Must be before staticfiles — enables ASGI runserver for WS
    'simpleui',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'rest_framework',
    'myapp',
    'myapp.members',
    'myapp.chat',
    'myapp.events',
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

ROOT_URLCONF = 'myapp.urls'
ASGI_APPLICATION = 'myapp.asgi.application'
WSGI_APPLICATION = 'myapp.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'myapp' / 'templates', BASE_DIR / 'dist'],
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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'myweb',
        'USER': 'myweb',
        'PASSWORD': 'NhknwSe8eMjYsX58',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}

AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'dist', BASE_DIR / 'myapp' / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'members.User'
AUTHENTICATION_BACKENDS = ['myapp.members.auth_backend.PhoneOrUsernameModelBackend']
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
REDIS_URL = 'redis://127.0.0.1:6379/0'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [{'address': 'redis://127.0.0.1:6379/0', 'socket_timeout': None}],
        },
    },
}
LOGIN_URL = '/auth/login/'
SESSION_COOKIE_AGE = 86400 * 30  # 30 天（记住我时）
SESSION_SAVE_EVERY_REQUEST = True  # 每次请求刷新 session 有效期
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.SessionAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
}

# AI Robot — Dify Workflow API (星辰AI助手，群聊回复)
AI_ROBOT_API_URL = os.environ.get('AI_ROBOT_API_URL', 'http://81.70.230.110:8088/v1/workflows/run')
AI_ROBOT_API_KEY = os.environ.get('AI_ROBOT_API_KEY', 'app-MmyRsdQxDXpTzBKRORvb9akd')

# 生成报告专用 API (app-gOpM9ADb6GdeJRhIA9zJmqb7, input_text → text)
REPORT_API_KEY = os.environ.get('REPORT_API_KEY', 'app-gOpM9ADb6GdeJRhIA9zJmqb7')

# 群聊编报专用 API (app-Gyqotj43SHI3xR5wihDYwCU7, input_text → text)
GROUP_REPORT_API_KEY = os.environ.get('GROUP_REPORT_API_KEY', 'app-Gyqotj43SHI3xR5wihDYwCU7')

# External API Key for event creation from external systems
EXTERNAL_API_KEY = os.environ.get('EXTERNAL_API_KEY', 'default-key-change-me')
