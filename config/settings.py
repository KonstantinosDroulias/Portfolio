"""konstantinosdroulias.com — settings come from the environment (.env loaded by systemd)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).lower() in ("1", "true", "yes", "on")


DEBUG = env_bool("DEBUG", False)
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-not-secret" if DEBUG else "")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set")

SITE_URL = os.environ.get("SITE_URL", "https://konstantinosdroulias.com").rstrip("/")
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "konstantinosdroulias.com,www.konstantinosdroulias.com,localhost,testserver").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS if h not in ("localhost", "testserver")]
# Hosts that must never be indexed (preview addresses).
NOINDEX_HOSTS = [h.strip() for h in os.environ.get("NOINDEX_HOSTS", "").split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
    "kd",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "kd.middleware.RobotsHeaderMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "kd.context_processors.site",
    ]},
}]

DATABASES = {"default": {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": DATA_DIR / "db.sqlite3",
    "OPTIONS": {"init_command": "PRAGMA journal_mode=WAL;", "transaction_mode": "IMMEDIATE"},
}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]
LOGIN_URL = "cms:login"
LOGIN_REDIRECT_URL = "cms:dashboard"

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Europe/Athens"
USE_I18N = False
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = DATA_DIR / "static"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = DATA_DIR / "media"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": (
        "django.contrib.staticfiles.storage.StaticFilesStorage" if DEBUG
        else "django.contrib.staticfiles.storage.ManifestStaticFilesStorage")},
}
FILE_UPLOAD_PERMISSIONS = 0o640
DATA_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024

# Mail: contact messages are always saved in the CMS; they are also emailed when SMTP is set.
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "465"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_SSL = EMAIL_PORT == 465
EMAIL_USE_TLS = EMAIL_PORT == 587
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "me@konstantinosdroulias.com")
EMAIL_BACKEND = ("django.core.mail.backends.smtp.EmailBackend" if EMAIL_HOST
                 else "django.core.mail.backends.dummy.EmailBackend")

CACHES = {"default": {"BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
                      "LOCATION": DATA_DIR / "cache"}}

SESSION_COOKIE_AGE = 60 * 60 * 24 * 30
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
    SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

LOGGING = {
    "version": 1, "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
}
