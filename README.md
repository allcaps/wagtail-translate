# Wagtail Translate

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/wagtail-translate.svg)](https://badge.fury.io/py/wagtail-translate)
[![Translate CI](https://github.com/allcaps/wagtail-translate/actions/workflows/test.yml/badge.svg)](https://github.com/allcaps/wagtail-translate/actions/workflows/test.yml)

**Wagtail Translate** adds machine translation to Wagtail.
It listens for Wagtail's [`copy_for_translation_done`](https://docs.wagtail.org/en/stable/reference/signals.html#copy-for-translation-done)
signal. Wagtail emits this signal after it copies an object to another locale.
Wagtail Translate sends the supported content to a translation backend and applies the result to the copy.

[Wagtail Simple Translation](https://docs.wagtail.org/en/stable/reference/contrib/simple_translation.html)
is a good fit for this workflow. It provides the user interface to copy content to another locale.

Wagtail Translate collects the content from a page or snippet in one translation document structured as HTML.
This document keeps titles, fields, rich text, and StreamField blocks together.
It gives the backend maximum context while preserving data that should not be translated.

For example, the title `The match` can describe a sports game or a stick used to
start a fire. Content elsewhere on the page tells the backend whether to use
`Le match` or `L’allumette` in French.

Wagtail Translate validates the returned document and restores the preserved data.
It then updates the copied object.

Wagtail Translate includes backends for:

- [DeepL](https://www.deepl.com)
- [OpenAI-compatible LLMs](#openai-compatible-llm), including [Ollama](https://docs.ollama.com/api/openai-compatibility) models
- ROT13 for tests and demonstrations

You can also write your own custom backend.

Wagtail Translate is developed and tested on Python 3.14.
Python versions >=3.10 should work but are not tested.

## Internationalisation and Simple Translation

Configure your project for authoring content in multiple languages.

See Wagtail documentation on [internationalization](https://docs.wagtail.org/en/stable/advanced_topics/i18n.html) and [Simple Translation](https://docs.wagtail.org/en/stable/reference/contrib/simple_translation.html).

For short:

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "wagtail.contrib.simple_translation",
    "wagtail.locales",
    # ...
]

USE_I18N = True
WAGTAIL_I18N_ENABLED = True

LANGUAGE_CODE = "en"
WAGTAIL_CONTENT_LANGUAGES = LANGUAGES = [
    ("en", "English"),
    ("fr", "French"),
]
MIDDLEWARE = [
    # ...
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    # ...
]
```
```python
# urls.py
from django.conf.urls.i18n import i18n_patterns
from django.urls import include, path
from wagtail import urls as wagtail_urls

urlpatterns += i18n_patterns(
    path("", include(wagtail_urls)),
)
```

Run migrations: `python manage.py migrate`.

Create locales at: `/admin/locales/new/`.

## Installation

Install Wagtail Translate:

```sh
pip install wagtail-translate
```

Add to to `INSTALLED_APPS` and define a `WAGTAIL_TRANSLATE_TRANSLATOR`.

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "wagtail_translate",
    "wagtail_translate.default_behaviour",
    # ...
]

WAGTAIL_TRANSLATE_TRANSLATOR = "wagtail_translate.translators.rot13.ROT13HTMLDocumentTranslator"
```

In the Wagtail admin interface, go to the homepage, in the dot-dot-dot-menu, choose "Translate".

The contents should be translated! 🥳

## Translation backends

### DeepL

Install the DeepL extra:

```shell
pip install "wagtail-translate[deepl]"
```

Add the backend and API key to your settings:

```python
WAGTAIL_TRANSLATE_TRANSLATOR = (
    "wagtail_translate.translators.deepl.DeepLHTMLDocumentTranslator"
)
WAGTAIL_TRANSLATE_DEEPL_KEY = "your-api-key"
```

### OpenAI-compatible LLM

Install the LLM extra:

```shell
pip install "wagtail-translate[llm]"
```

The backend uses an _OpenAI-compatible Chat Completions API_. The default endpoint is a local Ollama server.

Configure a local model:

```python
WAGTAIL_TRANSLATE_TRANSLATOR = (
    "wagtail_translate.translators.openai_compatible.LLMHTMLDocumentTranslator"
)
WAGTAIL_TRANSLATE_LLM_MODEL = "translategemma:27b"
WAGTAIL_TRANSLATE_LLM_BASE_URL = "http://localhost:11434/v1/"
WAGTAIL_TRANSLATE_LLM_API_KEY = "ollama"
```

### ROT13

`ROT13HTMLDocumentTranslator` replaces each letter with the letter 13 positions
later in the alphabet. Applying ROT13 twice restores the original text.

This backend is deterministic and does not use an external service. Use it for
tests and demonstrations, not for real translations.

## Default behaviour

The `wagtail_translate.default_behaviour` app adds the `copy_for_translation_done` signal handler.

The handler initiates the translation and saves the Wagtail object.

Use a custom app if you'd like to customize. For more details:

- [How to customize Wagtail Translate](docs/customise_wagtail_translate.md)
- [Design and behavior](docs/explanation.md)

## Development and testing

Install the package with its test dependencies:

```shell
make install
```

Activate the virtual environment:

```shell
source .venv/bin/activate
```

Run all checks and tests:

```shell
make test
```

Fix code style:

```shell
make fix-codestyle
```

## Demo project

Use the `tests/testproject` Django and Wagtail project for manual tests and
demonstrations:

```shell
python tests/testproject/manage.py migrate
python tests/testproject/manage.py createsuperuser
python tests/testproject/manage.py createcontent
python tests/testproject/manage.py runserver
```

The `createcontent` command resets the demo page tree. It then creates pages
with ambiguous words, rich text, nested StreamField blocks, images, documents,
and related snippets.

The demo uses the ROT13 backend by default. Change the translator settings in
`tests/testproject/settings.py` to test DeepL or a local LLM.

## Release

GitHub Actions publishes a release to PyPI when a `v*` tag is pushed.

Update the project version with uv:

```shell
uv version 1.0.0
git add pyproject.toml
git commit -m "Release 1.0.0"
git tag v1.0.0
git push
git push origin v1.0.0
```

The Git tag must match the package version with a `v` prefix. For example,
`version = "1.0.0"` uses the tag `v1.0.0`.

You can create a GitHub Release after you push the tag. If GitHub creates the
tag, make sure that the version commit is already on the target branch.

Build and inspect the package locally before a release:

```shell
uv build
```

This command writes the release artifacts to `dist/`. Check the generated files
and make sure that they contain the package modules:

```shell
tar -tf dist/wagtail_translate-*.tar.gz
unzip -l dist/wagtail_translate-*.whl
```
