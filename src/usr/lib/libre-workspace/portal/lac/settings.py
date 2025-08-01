"""
Django settings for lac project.

Generated by 'django-admin startproject' using Django 3.2.19.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

from pathlib import Path
import os
import ldap
from django_auth_ldap.config import LDAPSearch, GroupOfNamesType, LDAPGroupQuery
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-c7&zjd(1l0)(&z2n4&t=g8im6$(tconv@y-$3ic+hhlo%x3fh-'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1"
]

CSRF_TRUSTED_ORIGINS = [
    'http://localhost',
    'http://127.0.0.1',
]


# Add the ip address of the server to the allowed hosts
_ip_adresses = os.popen("hostname -I").read().split(" ")
for _ip in _ip_adresses:
    # Check if its a ipv6 address
    if ":" in _ip:
        CSRF_TRUSTED_ORIGINS.append(f"https://[{_ip}]")
        ALLOWED_HOSTS.append(f"[{_ip}]")
    else:
        CSRF_TRUSTED_ORIGINS.append(f"https://{_ip}")
        ALLOWED_HOSTS.append(_ip)
# Get the domain name in the caddyfile
if os.path.exists("/etc/caddy/Caddyfile"):
    with open("/etc/caddy/Caddyfile", "r") as f:
        _caddyfile = f.readlines()
        for line in _caddyfile:
            _words = line.split(" ")
            for i in range(len(_words)):
                if "portal." in _words[i]:
                    domain = _words[i].replace(";", "")
                    ALLOWED_HOSTS.append(domain)
                    CSRF_TRUSTED_ORIGINS.append(f"https://{domain}")
# Add all hosts from the environment variable separated by a comma
_hosts = os.getenv("ALLOWED_HOSTS", "").split(",")
for host in _hosts:
    if host.strip() != "":
        ALLOWED_HOSTS.append(host)


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'oidc_provider',
    'rest_framework',
    'drf_spectacular',

    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_hotp',
    'django_otp.plugins.otp_static',

    'idm',
    'app_dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
     'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'lac.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / "idm/templates",
            BASE_DIR / "unix/templates",
            BASE_DIR / "lac/templates",
            BASE_DIR / "welcome/templates",
            BASE_DIR / "app_dashboard/templates",
            BASE_DIR / "addon_center/templates",
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'lac.context_processors.global_settings', # My custom context processor
            ],
        },
    },
]

AUTH_LDAP_ENABLED = os.getenv("AUTH_LDAP_SERVER_URI", "") != ""

if AUTH_LDAP_ENABLED:
    AUTHENTICATION_BACKENDS = ["django_auth_ldap.backend.LDAPBackend"]
else:
    AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

INITIAL_ADMIN_PASSWORD_WITHOUT_LDAP = os.getenv("INITIAL_ADMIN_PASSWORD_WITHOUT_LDAP", "admin")

# LDAP Settings
AUTH_LDAP_SERVER_URI = os.getenv("AUTH_LDAP_SERVER_URI", "")
AUTH_LDAP_DC = os.getenv("AUTH_LDAP_DC")
AUTH_LDAP_BIND_DN = os.getenv("AUTH_LDAP_BIND_DN")
AUTH_LDAP_BIND_PASSWORD = os.getenv("AUTH_LDAP_BIND_PASSWORD")
AUTH_LDAP_USER_DN_TEMPLATE = os.getenv("AUTH_LDAP_USER_DN_TEMPLATE")
AUTH_LDAP_GROUP_ADMIN_DN = os.getenv("AUTH_LDAP_GROUP_ADMIN_DN")

AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    os.getenv("AUTH_LDAP_GROUP_SEARCH_BASE"),
    ldap.SCOPE_SUBTREE
)
AUTH_LDAP_GROUP_TYPE = GroupOfNamesType(name_attr="cn")
AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    # "is_active": "cn=active,ou=groups,dc=example,dc=com",
    "is_staff": AUTH_LDAP_GROUP_ADMIN_DN,
    "is_superuser": AUTH_LDAP_GROUP_ADMIN_DN,
}
# Allow self signed certificates
ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_ALLOW)

# Optional hide some more users from the admin interface
HIDDEN_LDAP_USERS = os.getenv("HIDDEN_LDAP_USERS", "")


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"django_auth_ldap": {"level": "DEBUG", "handlers": ["console"]}},
}

WSGI_APPLICATION = 'lac.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/var/lib/libre-workspace/portal/db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.2/topics/i18n/

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

# Set the default language code to German for older systems (which are all german and dont have set an environment variable via portal.conf yet.)
LANGUAGE_CODE = os.environ.get("LANGUAGE_CODE", "de")

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

LANGUAGES = (
    ('en', _("language.en")),
    ('de', _("language.de")),
)

USE_I18N = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATICFILES_DIRS = [
    BASE_DIR / "lac/static",
]

# Needed for gunicon
STATIC_ROOT = '/var/www/libre-workspace-static/'

MEDIA_URL = 'media/'
MEDIA_ROOT = '/var/lib/libre-workspace/portal/media/'
# Make sure the media directory exists
os.makedirs(MEDIA_ROOT, exist_ok=True)

# Email Settings
EMAIL_HOST = os.getenv("EMAIL_HOST")                 # <- host name [e.g. smtp.gmail.com for gmail]
_email_port_string = os.getenv("EMAIL_PORT", "465")
if not _email_port_string.isnumeric():
    _email_port_string = "465"
EMAIL_PORT = int(_email_port_string)               # <- smtp port [e.g. 587]
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")          # <- username usually the same as email
EMAIL_HOST_EMAIL = os.getenv("EMAIL_HOST_EMAIL")          # <- email
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")  # <- password
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS") == "True"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL") == "True"

# Other Enviromental Settings
NEXTCLOUD_INSTALLATION_DIRECTORY = os.getenv("NEXTCLOUD_INSTALLATION_DIRECTORY", "/var/www/nextcloud/")

LINUX_ARBEITSPLATZ_CONFIGURED = os.getenv("LINUX_ARBEITSPLATZ_CONFIGURED", "false").lower() == "true"

LOGIN_URL="/idm/login"

OIDC_USERINFO = 'idm.oidc_provider_settings.userinfo'
OIDC_EXTRA_SCOPE_CLAIMS = 'idm.oidc_provider_settings.CustomScopeClaims'
OIDC_IDTOKEN_INCLUDE_CLAIMS = True

# To be disabled in production
ADMIN_ENABLED = True


# REST API Settings
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'idm.api_authentication.ApiKeyAuthentication'
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Libre Workspace API',
    'DESCRIPTION': 'Ignore the Authorize button and curl code snippets.<br>Documentation available at <a href="https://docs.libre-workspace.org/modules/libre-workspace-portal.html#api" target="_blank">Libre Workspace Portal API Documentation</a>.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
    },
}