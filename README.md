# Wagtail Translate

Use Wagtail Translate to machine translate your Wagtail contents.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/wagtail-translate.svg)](https://badge.fury.io/py/wagtail-translate)
[![Translate CI](https://github.com/allcaps/wagtail-translate/actions/workflows/test.yml/badge.svg)](https://github.com/allcaps/wagtail-translate/actions/workflows/test.yml)

## Links

- [Documentation](https://github.com/allcaps/wagtail-translate/blob/main/README.md)
- [Changelog](https://github.com/allcaps/wagtail-translate/blob/main/CHANGELOG.md)
- [Contributing](https://github.com/allcaps/wagtail-translate/blob/main/CONTRIBUTING.md)
- [Discussions](https://github.com/allcaps/wagtail-translate/discussions)
- [Security](https://github.com/allcaps/wagtail-translate/security)

## Supported versions

- Python ...
- Django ...
- Wagtail ...

## Setup i18n

First, set up your project following the official Wagtail i18n instructions:
https://docs.wagtail.org/en/stable/advanced_topics/i18n.html

### TL;DR

```python
# settings.py
USE_I18N = True
WAGTAIL_I18N_ENABLED = True
USE_L10N = True

LANGUAGE_CODE = 'en'
WAGTAIL_CONTENT_LANGUAGES = LANGUAGES = [
    ('en', "English"),
    ('fr', "French"),
]

INSTALLED_APPS += [
    "wagtail.locales",
]

MIDDLEWARE += [
    'django.middleware.locale.LocaleMiddleware',
]

# urls.py
from django.conf.urls.i18n import i18n_patterns

urlpatterns += i18n_patterns(
    path("", include(wagtail_urls)),
)
```

Create the French locale at: `/admin/locales/new/`


## Installation


```sh
python -m pip install wagtail-translate
```

``` python
INSTALLED_APPS = [
    "wagtail_translate",
    "wagtail.contrib.simple_translation",
    ...
]
```

In your `apps.py`:

``` python
from django.apps import AppConfig


class YourAppConfig(AppConfig):
    ...

    def ready(self):
        from . import signals  # noqa
```
Create a `signals.py`:

```python
from django.dispatch import receiver
from wagtail.models import Page, TranslatableMixin
from wagtail_translate.translators.rot13 import ROT13Translator as Translator
import django.dispatch

copy_for_translation_done = django.dispatch.Signal()


@receiver(copy_for_translation_done)
def actual_translation(sender, source_obj, target_obj, **kwargs):
    """
    Perform actual translation.

    Wagtail triggers the copy_for_translation_done signal,
    and this signal handler translates the contents.

    The source_obj must be a subclass of TranslatableMixin.

    Integrators are expected to define their own signal receiver.
    This receiver allows easy customization of behaviors:

    - A custom Translator class can be specified.
    - Pages can be saved as drafts (to be reviewed)
      or published (directly visible to the public).
    - Custom workflows can be triggered.
    - Data can be post-processed.
    - And more ...
    """

    if not issubclass(target_obj.__class__, TranslatableMixin):
        raise Exception(
            "Object must be a subclass of TranslatableMixin. "
            f"Got {type(target_obj)}."
        )

    # Get the source and target language codes
    source_language_code = source_obj.locale.language_code
    target_language_code = target_obj.locale.language_code

    # Initialize the translator, and translate.
    translator = Translator(source_language_code, target_language_code)
    translated_obj = translator.translate_obj(source_obj, target_obj)

    # Differentiate between regular Django model and Wagtail Page.
    # - Page instances have `save_revision` and `publish` methods.
    # - Regular Django model (aka Wagtail Snippet) need to be saved.
    if isinstance(translated_obj, Page):
        # Calling `publish` is optional,
        # and will publish the translated page.
        # Without, the page will be in draft mode.
        translated_obj.save_revision().publish()
    else:
        translated_obj.save()
```

In Wagtail admin interface, go to the homepage `/admin/pages/2/`, in the dot-dot-dot-menu, choose "Translate".

The contents should be translated.

## Deepl

Install and configure [DeepL](https://www.deepl.com/) translator:

- `pip install deepl`
- Get a DeepL API key from https://www.deepl.com/pro#developer
- Add `WAGTAIL_TRANSLATE_DEEPL_KEY` to your settings.
- In your `signals.py`: `from wagtail_translate.translators.deepl import DeeplTranslator as Translator`

## Contributing

### Install

To make changes to this project, first clone this repository:

```sh
git clone https://github.com/allcaps/wagtail-translate.git
cd wagtail-translate
```

With your preferred virtualenv activated, install testing dependencies:

#### Using pip

```sh
python -m pip install --upgrade pip>=21.3
python -m pip install -e '.[testing]' -U
```

#### Using flit

```sh
python -m pip install flit
flit install
```

### pre-commit

Note that this project uses [pre-commit](https://github.com/pre-commit/pre-commit).
It is included in the project testing requirements. To set up locally:

```sh
# go to the project directory
$ cd wagtail-translate
# initialize pre-commit
$ pre-commit install

# Optional, run all checks once for this, then the checks will run only on the changed files
$ git ls-files --others --cached --exclude-standard | xargs pre-commit run --files
```

### How to run tests

Now you can run tests as shown below:

```sh
tox
```

or, you can run them for a specific environment `tox -e python3.11-django4.2-wagtail5.1` or specific test
`tox -e python3.11-django4.2-wagtail5.1-sqlite wagtail-translate.tests.test_file.TestClass.test_method`

To run the test app interactively, use `tox -e interactive`, visit `http://127.0.0.1:8000/admin/` and log in with `admin`/`changeme`.

### Project template

This project has been created with [Cruft](https://pypi.org/project/cruft/), a drop-in replacement for Cookiecutter.

```sh
cruft create git@github.com:wagtail/cookiecutter-wagtail-package.git
```

The "cookiecutter answers" are stored in `.cruft.json`. To update the project to the latest template, run:

```sh
cruft update
```
