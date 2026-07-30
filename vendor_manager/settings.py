"""Django settings for vendor_manager project.

Environment variables:
    DJANGO_SECRET_KEY     (required in non-DEBUG; must not be empty)
    DJANGO_DEBUG          "true"/"1"/"yes" enables DEBUG; default False
    DJANGO_ALLOWED_HOSTS  comma-separated list; required when DEBUG is False
    CSRF_TRUSTED_ORIGINS  comma-separated list; optional
    FORCE_SCRIPT_NAME     mount prefix; defaults to "/"
    DATABASE_ENGINE       "sqlite" (default) or "postgresql"
                          PostgreSQL requires DATABASE_NAME, DATABASE_USERNAME,
                          DATABASE_PASSWORD, DATABASE_HOST, DATABASE_PORT.
    SPECTACULAR_SERVERS   comma-separated OpenAPI server URLs; optional

MSSQL is no longer supported (see docs/REQUIREMENTS.md NFR-23).
"""

from __future__ import annotations

import os
from pathlib import Path

from django.contrib.messages import constants as message_constants
from django.core.exceptions import ImproperlyConfigured

from vendor_manager import __version__

# ---------------------------------------------------------------------------
# Environment helpers
# ---------------------------------------------------------------------------


def env_bool(name: str, default: bool = False) -> bool:
    """Return True iff the env var is set to a truthy string.

    Truthy: "1", "true", "yes", "on" (case-insensitive). Anything else
    (including "", "0", "false", "no", unset) returns False. This fixes the
    historical bug where ``DEBUG = os.environ.get("DJANGO_DEBUG")`` treated
    the empty string as falsy but any non-empty value as truthy.
    """
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: list[str] | None = None) -> list[str]:
    """Return a comma-separated env var as a list of stripped, non-empty items."""
    raw = os.environ.get(name, "")
    items = [item.strip() for item in raw.split(",") if item.strip()]
    if items:
        return items
    return list(default) if default is not None else []


def env_required(name: str) -> str:
    """Return the env var value; raise ImproperlyConfigured if unset or empty."""
    value = os.environ.get(name, "").strip()
    if not value:
        raise ImproperlyConfigured(f"Environment variable {name!r} is required and must not be empty.")
    return value


BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Core security settings
# ---------------------------------------------------------------------------

DEBUG = env_bool("DJANGO_DEBUG", default=False)

# In DEBUG we accept a dev-only default so ``manage.py runserver`` works out of
# the box. In production the env var MUST be set.
if DEBUG:
    SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or "dev-only-insecure-secret-key-do-not-use-in-production"
else:
    SECRET_KEY = env_required("DJANGO_SECRET_KEY")

if DEBUG:
    ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])
else:
    ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")
    if not ALLOWED_HOSTS:
        raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must be set when DEBUG is False.")

FORCE_SCRIPT_NAME = os.environ.get("FORCE_SCRIPT_NAME", "/")

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

# Production hardening — inert under DEBUG so runserver works over plain HTTP.
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", default=False)
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "0"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)
    SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", default=False)
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"


# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "vendor_manager",
    "people",
    "orders",
    "companies",
    "undertakings",
    "engagements",
    "leaves",
    "contracts",
    "rolepermissions",
    "rest_framework",
    "django_filters",
    "drf_spectacular",
    "crispy_forms",
    "crispy_bootstrap5",
    "django_tables2",
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

DJANGO_TABLES2_TEMPLATE = "django_tables2/bootstrap5.html"

X_FRAME_OPTIONS = "DENY"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "vendor_manager.logging.RequestContextMiddleware",
]

ROOT_URLCONF = "vendor_manager.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "vendor_manager", "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "vendor_manager.navigation.nav_context_processor",
            ],
        },
    },
]

ROLEPERMISSIONS_MODULE = "vendor_manager.roles"

WSGI_APPLICATION = "vendor_manager.wsgi.application"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = FORCE_SCRIPT_NAME
LOGOUT_REDIRECT_URL = FORCE_SCRIPT_NAME

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
        "vendor_manager.api_permissions.HasLinkedPerson",
    ],
    "DEFAULT_PAGINATION_CLASS": "vendor_manager.api_pagination.DefaultPageNumberPagination",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "vendor_manager.api_exceptions.drf_exception_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Vendor Manager API",
    "DESCRIPTION": "REST API for vendor_manager.",
    "VERSION": __version__,
    "SERVERS": [{"url": url} for url in env_list("SPECTACULAR_SERVERS")],
}

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
# Supported values for DATABASE_ENGINE:
#   "sqlite"      — file-based, for local dev and CI (default when unset).
#   "postgresql"  — production and Docker Compose dev. Requires DATABASE_NAME,
#                   DATABASE_USERNAME, DATABASE_PASSWORD, DATABASE_HOST,
#                   DATABASE_PORT.
#
# MSSQL is intentionally not supported (see docs/REQUIREMENTS.md NFR-23).

DATABASE_ENGINE = os.environ.get("DATABASE_ENGINE", "sqlite").strip().lower()

if DATABASE_ENGINE in {"sqlite", "django.db.backends.sqlite3"}:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
elif DATABASE_ENGINE in {
    "postgresql",
    "postgres",
    "django.db.backends.postgresql",
    "django.db.backends.postgresql_psycopg2",
}:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env_required("DATABASE_NAME"),
            "USER": env_required("DATABASE_USERNAME"),
            "PASSWORD": env_required("DATABASE_PASSWORD"),
            "HOST": env_required("DATABASE_HOST"),
            "PORT": os.environ.get("DATABASE_PORT", "5432"),
        }
    }
else:
    raise ImproperlyConfigured(f"Unsupported DATABASE_ENGINE {DATABASE_ENGINE!r}. Use 'sqlite' or 'postgresql'.")


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = FORCE_SCRIPT_NAME.rstrip("/") + "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [os.path.join(BASE_DIR, "vendor_manager/static/")]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_ENGINE = "django.contrib.sessions.backends.db"

# Silence deploy-check warnings that are addressed by later phases (Phase 9
# flips CI's `check --deploy` to `--fail-level=WARNING` and closes the
# rest via env config).
SILENCED_SYSTEM_CHECKS: list[str] = []

MESSAGE_TAGS = {
    message_constants.DEBUG: "debug",
    message_constants.INFO: "info",
    message_constants.SUCCESS: "success",
    message_constants.WARNING: "warning",
    message_constants.ERROR: "danger",
}


# ---------------------------------------------------------------------------
# Logging — structured JSON to stdout (NFR-27, NFR-36, NFR-37)
# ---------------------------------------------------------------------------
# All loggers propagate to a single stdout handler using python-json-logger.
# Under DEBUG we swap to a plain human-readable formatter for local dev.
#
# Django's AdminEmailHandler is intentionally NOT enabled. Unhandled exceptions
# reach the "django" logger at ERROR level with traceback included.

LOG_LEVEL = os.environ.get("DJANGO_LOG_LEVEL", "DEBUG" if DEBUG else "INFO").upper()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_context": {
            "()": "vendor_manager.logging.RequestContextFilter",
        },
    },
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.json.JsonFormatter",
            "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s %(user_id)s %(request_id)s",
            "rename_fields": {
                "asctime": "timestamp",
                "levelname": "level",
                "name": "logger",
            },
        },
        "plain": {
            "format": "%(asctime)s %(levelname)s %(name)s [%(user_id)s %(request_id)s] %(message)s",
        },
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "plain" if DEBUG else "json",
            "filters": ["request_context"],
        },
    },
    "root": {
        "handlers": ["stdout"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["stdout"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "django.request": {
            "handlers": ["stdout"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["stdout"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.db.backends": {
            # Very noisy; only interesting when explicitly requested.
            "handlers": ["stdout"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
