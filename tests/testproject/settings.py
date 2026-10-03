import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = "wagtail-exact-crop-test-key"  # noqa S105
DEBUG = True
ALLOWED_HOSTS = ["*"]
ROOT_URLCONF = "tests.testproject.urls"
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

INSTALLED_APPS = [
    "tests.testproject.demoapp.apps.DemoAppConfig",
    "wagtail_translate",
    "wagtail_translate.default_behaviour",
    "wagtail.contrib.simple_translation",
    "wagtail.locales",
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",
    "modelcluster",
    "taggit",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": [],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]


LANGUAGE_CODE = "en"
TIME_ZONE = "UTC"
USE_I18N = True
WAGTAIL_I18N_ENABLED = True
WAGTAIL_CONTENT_LANGUAGES = LANGUAGES = [
    (LANGUAGE_CODE, "English"),
    ("fr", "French"),
    ("nl", "Dutch"),
    ("is", "Icelandic"),
    ("de", "German"),
    ("it", "Italian"),
]

MIDDLEWARE += [
    "django.middleware.locale.LocaleMiddleware",
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/stable/howto/static-files/
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = "/static/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

WAGTAIL_SITE_NAME = "Wagtail Translate Test Project"
WAGTAILADMIN_BASE_URL = "http://127.0.0.1:8000"


# ROT13HTMLDocumentTranslator for testing purposes.
# Is deterministic and does not depend on external services.
# ----------------------------
WAGTAIL_TRANSLATE_TRANSLATOR = (
    "wagtail_translate.translators.rot13.ROT13HTMLDocumentTranslator"
)

# Deepl
# ----------------------------
# WAGTAIL_TRANSLATE_TRANSLATOR = (
#     "wagtail_translate.translators.deepl.DeepLHTMLDocumentTranslator"
# )
# WAGTAIL_TRANSLATE_DEEPL_KEY = os.environ.get("WAGTAIL_TRANSLATE_DEEPL_KEY", "")

# Ollama local model Translategemma 27b
# ----------------------------
# WAGTAIL_TRANSLATE_TRANSLATOR = (
#     "wagtail_translate.translators.openai_compatible.LLMHTMLDocumentTranslator"
# )
# WAGTAIL_TRANSLATE_LLM_MODEL = os.environ.get(
#     "WAGTAIL_TRANSLATE_LLM_MODEL", "translategemma:27b"
# )
# WAGTAIL_TRANSLATE_LLM_BASE_URL = os.environ.get(
#     "WAGTAIL_TRANSLATE_LLM_BASE_URL", "http://localhost:11434/v1/"
# )
# WAGTAIL_TRANSLATE_LLM_API_KEY = os.environ.get(
#     "WAGTAIL_TRANSLATE_LLM_API_KEY", "ollama"
# )
# # TODO, should this be a dict with instruction per target language?
# WAGTAIL_TRANSLATE_LLM_INSTRUCTIONS = os.environ.get(
#     "WAGTAIL_TRANSLATE_LLM_INSTRUCTIONS"
# )
