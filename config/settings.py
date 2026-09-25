"""
Django settings for SGFT.

Every secret or environment-specific value comes from environment variables:
a .env file in development (see .env.example) and the host's settings in production.
"""
import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(name, default=None, required=False):
    value = os.environ.get(name, default)
    if required and not value:
        raise ImproperlyConfigured(f"Missing environment variable {name}. See .env.example.")
    return value


def env_bool(name, default=False):
    return str(env(name, str(default))).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name):
    return [item.strip() for item in env(name, "").split(",") if item.strip()]


# --- Core -------------------------------------------------------------------

SECRET_KEY = env("DJANGO_SECRET_KEY", required=True)
DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "django_htmx",
    # Project apps. Dependency rules between them: estructura-y-flujo-datos-SGFT.md §3
    # (inventory never imports pos; reports only reads).
    "apps.core",
    "apps.accounts",
    "apps.catalog",
    "apps.inventory",
    "apps.pos",
    "apps.reports",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Templates live inside each app (templates/<app>/ and templates/<app>/partials/);
        # the shared base.html lives in apps/core/templates/ (WBS 2.1).
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Database (WBS 5.2) -------------------------------------------------------

DATABASES = {
    "default": dj_database_url.parse(
        env("DATABASE_URL", required=True),
        conn_max_age=600,
        conn_health_checks=True,
    )
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Authentication (WBS 3.1.1) -------------------------------------------------

# Custom user model defined BEFORE the first migration; changing it later is very costly.
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
# LOGIN_URL / LOGIN_REDIRECT_URL are set by WBS 3.1.2 once the login view exists.

# --- Language and time ------------------------------------------------------------

LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Ciudad_Juarez"
USE_I18N = True
USE_TZ = True  # timestamps stored in UTC; required for the two sale timestamps (CLAUDE.md §5 rule 7)

# --- Static files (WBS 5.3) --------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]  # static/pos/: offline shell (ADR-02)
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # No manifest hashing on purpose: the service worker needs a stable URL and Workbox
    # handles cache revisions (revision-tecnica-offline-SGFT.md §3). Revisit in WBS 3.4.2.
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

# --- Security (CLAUDE.md §10; full review in WBS 4.4) ----------------------------------

# static/pos/db.js reads the csrftoken cookie to send X-CSRFToken (contrato-sync-pdv.md §2).
CSRF_COOKIE_HTTPONLY = False

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", False)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
