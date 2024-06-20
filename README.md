# Wagtail Translate

Use Wagtail Translate to machine translate your Wagtail contents.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/wagtail-translate.svg)](https://badge.fury.io/py/wagtail-translate)
[![Translate CI](https://github.com/allcaps/wagtail-translate/actions/workflows/test.yml/badge.svg)](https://github.com/allcaps/wagtail-translate/actions/workflows/test.yml)

## Links

- [Documentation](https://github.com/allcaps/wagtail-translate/blob/main/README.md)
- [Changelog](https://github.com/allcaps/wagtail-translate/blob/main/CHANGELOG.md)
- [Contributing](https://github.com/allcaps/wagtail-translate/blob/main/CONTRIBUTING.md)
- [Issues](https://github.com/allcaps/wagtail-translate/issues)
- [Security](https://github.com/allcaps/wagtail-translate/security)

## Supported versions

- Python 3.8 - 3.12
- Django 4.2 - 5.0
- Wagtail 5.2 - 6.0

## Internationalization

You need to configure your project for authoring content in multiple languages.
See Wagtail documentation on [internationalization](https://docs.wagtail.org/en/stable/advanced_topics/i18n.html).


### TL;DR

```python
# settings.py
USE_I18N = True
WAGTAIL_I18N_ENABLED = True
USE_L10N = True

LANGUAGE_CODE = 'en'
WAGTAIL_CONTENT_LANGUAGES = LANGUAGES = [
    (LANGUAGE_CODE, "English"),
    ('fr', "French"),
]

INSTALLED_APPS += [
    "wagtail.locales",
    "wagtail.contrib.simple_translation",
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
from wagtail.models import Page
from wagtail_translate.translators.rot13 import ROT13Translator as Translator

# Wagtail 6.2 introduces the `copy_for_translation_done` signal
try:
    from wagtail.signals import copy_for_translation_done
except ImportError:
    from wagtail_translate.signals import copy_for_translation_done


@receiver(copy_for_translation_done)
def handle_translation_done_signal(sender, source_obj, target_obj, **kwargs):
    source_language_code = source_obj.locale.language_code
    target_language_code = target_obj.locale.language_code

    translator = Translator(source_language_code, target_language_code)
    translated_obj = translator.translate_obj(source_obj, target_obj)

    if isinstance(translated_obj, Page):
        translated_obj.save_revision()
    else:
        translated_obj.save()
```
In the Wagtail admin interface, go to the homepage, in the dot-dot-dot-menu, choose "Translate".

The contents should be translated! 🥳

This example uses the `ROT13Translator`. It shifts each letter by 13 places. Applying it twice will return the text to its original form. So ROT13 is good for testing and evaluation, but not for real-world use.

## Deepl

Wagtail Translation has a [DeepL](https://www.deepl.com/) translator.
Install and configure it as follows:

- `pip install deepl`
- Get a DeepL API key from https://www.deepl.com/pro#developer
- Add `WAGTAIL_TRANSLATE_DEEPL_KEY = "..."` to your settings.
- In your `signals.py` change the import to `from wagtail_translate.translators.deepl import DeeplTranslator as Translator`

## Customizing Translation Logic

Multi-language projects often have specific requirements for the translation process. The signal receiver allows developers to tailor the translation process to their needs. For instance, you can customize the translator or adjust other aspects of the translation logic.

The following sections provide examples of how to customize the translation logic. These are illustrations and not mandatory for using this package.

### Using a custom translation service

You might want to connect to your preferred machine translation service, subclass BaseTranslator:

```python
# your_app/translators.py

from wagtail_translate.translators.base import BaseTranslator

class CustomTranslator(BaseTranslator):
    def translate(self, source_string: str) -> str:
        """
        Translate, a function that does the actual translation.
        Add a call to your preferred translation service.

        You'd supply the following values to the translation service:
        - source_string
        - self.source_language_code
        - self.target_language_code
        """
        translation = ...  # Your translation logic here
        return translation
```
To use the custom translator in your `signals.py` update the import statement to:

```python
from your_app.translators import CustomTranslator as Translator
```

### Using different translation services for various languages

For example, DeepL doesn't support Icelandic. So, we want to use some `CustomIcelandicTranslator` for Icelandic translations and `DeeplTranslator` for other languages.

```python
...

@receiver(copy_for_translation_done)
def my_translation_done_receiver(sender, source_obj, target_obj, **kwargs):
    source_language_code = source_obj.locale.language_code
    target_language_code = target_obj.locale.language_code

    if source_language_code == "is" or target_language_code == "is":
        translator_class = CustomIcelandicTranslator
    else:
        translator_class = DeeplTranslator

    translator = translator_class(source_language_code, target_language_code)
    translated_obj = translator.translate_obj(source_obj, target_obj)

    if isinstance(translated_obj, Page):
        translated_obj.save_revision()
    else:
        translated_obj.save()
```

### Direct publishing of translations

Change `translated_obj.save_revision()` to `translated_obj.save_revision().publish()` to publish the translated page directly.

### Store the source locale on the translated object

Sometimes it is useful to content editors to know the source language of the translated object. This can be done by adding a `source_locale` field to the model:

```python
class MyTranslatedModel(models.Model):
    source_locale = models.ForeignKey(Locale, blank=True, null=True, on_delete=models.SET_NULL)
    ...

    panels = [
        FieldPanel("source_locale", readonly=True),
    ]
```
Run `makemigrations` and `migrate` to add the field to the database.

Set the field in the signal receiver:

```python
@receiver(copy_for_translation_done)
def my_translation_done_receiver(sender, source_obj, target_obj, **kwargs):
    ...
    translated_obj.source_locale = source_obj.locale
    translated_obj.save()
```


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
