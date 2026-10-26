import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_SOURCE = os.environ.get("THEATRE_DATA_SOURCE", "sqlite")
SQLITE_PATH = Path(os.environ.get(
    "THEATRE_SQLITE_PATH", str(DATA_DIR / "theatre.sqlite"),
))
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "theatre-local-development-key-for-pr5",
)
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "homepage.apps.HomepageConfig",
    "repertoire.apps.RepertoireConfig",
    "performances.apps.PerformancesConfig",
    "reservations.apps.ReservationsConfig",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "theatre.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "homepage.context_processors.project",
            ],
        },
    },
]
WSGI_APPLICATION = "theatre.wsgi.application"
ASGI_APPLICATION = "theatre.asgi.application"
DATABASES = {}
LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
