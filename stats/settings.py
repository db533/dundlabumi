"""
Django settings for stats project.

"""

from pathlib import Path
# https://djangostars.com/blog/configuring-django-settings-best-practices/
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
#print('BASE_DIR:',BASE_DIR)

root = environ.Path(__file__) - 3  # get root of the project
SITE_ROOT = root()
#print('SITE_ROOT:',SITE_ROOT)

env = environ.Env()
environ.Env.read_env(overwrite=True)  # reading .env file

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str('django_secret_key', default='django-insecure-edp-tk4w825yawt1=#4=k&k6($x)69at_0_cx=e6r2y20it@ye')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('debug', default=False)
TEMPLATE_DEBUG = DEBUG
#print('debug:',DEBUG)

ALLOWED_HOSTS = env('allowed_hosts', cast=[str])
ALLOWED_HOSTS.append("www."+ALLOWED_HOSTS[0])
ALLOWED_HOSTS.append("dundlabumi.lv")
#print('ALLOWED_HOSTS:',ALLOWED_HOSTS)

# Get the IP address of this host
import socket
hostname = socket.gethostname()
IP = socket.gethostbyname(hostname)
HOSTED = env.bool('HOSTED', default=False)
#print('HOSTED:',HOSTED)
if HOSTED:
    # .env file states this environment is hosted, so use the retrieved IP address.
    host_ip=IP
else:
    host_ip='127.0.0.1'
#print('host_ip:',host_ip)

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dati.apps.DatiConfig',
    'rest_framework.authtoken',
    'rest_framework',
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

ROOT_URLCONF = 'stats.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'stats.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env.str('MYSQL_DB_NAME', default='stats_local'),
        'USER': env.str('MYSQL_DB_USER', default='root'),
        'PASSWORD': env.str('MYSQL_PWD'),
        'HOST': host_ip,
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"
        }
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Riga'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

public_root = root.path('public/')
MEDIA_ROOT = public_root('media')
MEDIA_URL = env.str('MEDIA_URL', default='media/')
STATIC_ROOT = public_root(env.str('static_root', default='static'))
STATIC_URL = env.str('STATIC_URL', default='static/')

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

EMAIL_BACKEND = 'django_smtp_ssl.SSLEmailBackend'
EMAIL_HOST = 'mail.dundlabumi.lv'
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
EMAIL_PORT = 465
EMAIL_HOST_USER = env.str('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD=env.str('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env.str('EMAIL_HOST_USER')
SERVER_EMAIL = env.str('EMAIL_HOST_USER')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
	'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ] # Added this based on ChatGPT suggestion
}
APPEND_SLASH=False

# Set the session engine to use cookies
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    # other authentication backends if any
]

#LOGGING = {
#    'version': 1,
#    'disable_existing_loggers': False,
#    'handlers': {
#        'file': {
#            'level': 'DEBUG',
#            'class': 'logging.FileHandler',
#            'filename': 'django.log',
#        },
#    },
#   'loggers': {
#        'django': {
#            'handlers': ['file'],
#            'level': 'DEBUG',
#        },
#    },
#}
