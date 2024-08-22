# Wagtail Translate

**Wagtail Translate** adds machine translations to your Wagtail site, with built-in support for [DeepL](https://www.deepl.com) and the flexibility to integrate other translation services.
It automatically detects when a page is copied to a new locale and initiates the translation process.

[Wagtail Localize](https://wagtail-localize.org/) and [Wagtail Simple Translation](https://docs.wagtail.org/en/stable/reference/contrib/simple_translation.html) are the go-to solutions for multi-language Wagtail projects.
Wagtail Localize offers advanced features that may be excessive for many projects, while Wagtail Simple Translation only copies pages to new locales, requiring manual translation.

**Wagtail Translate** adds machine translations to Wagtail.
It works in combination with Simple Translation, offering the ideal solution for projects seeking a simple interface with powerful translation support.

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

In summary:

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

Create the French locale at: `/admin/locales/new/`.


## Installation

```sh
python -m pip install wagtail-translate
```

``` python
INSTALLED_APPS = [
    "wagtail_translate",
    "wagtail_translate.default_behaviour",
    ...
]

WAGTAIL_TRANSLATE_TRANSLATOR = "wagtail_translate.translators.rot13.ROT13Translator"
```


In the Wagtail admin interface, go to the homepage, in the dot-dot-dot-menu, choose "Translate".

The contents should be translated! 🥳

### ROT13Translator

The installation example uses the `ROT13Translator`. It shifts each letter by 13 places.
Applying it twice will return the text to its original form.
ROT13 is good for testing and evaluation, but not for real-world use.

### DeepLTranslator

Wagtail Translation has a [DeepL](https://www.deepl.com) translator.
Install and configure it as follows:

- `pip install deepl`
- Get a DeepL API key from https://www.deepl.com/pro#developer
- Add `WAGTAIL_TRANSLATE_DEEPL_KEY = "..."` to your settings.
- Set `WAGTAIL_TRANSLATE_TRANSLATOR = "wagtail_translate.translators.deepl.DeepLTranslator"`

## Documentation

- This readme for installation and basic usage.
- [How to customise Wagtail Translate](https://github.com/allcaps/wagtail-translate/tree/main/docs/customise_wagtail_translate.md)
- [Explanation](https://github.com/allcaps/wagtail-translate/tree/main/docs/explanation.md)

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
python -m pip install --upgrade pip
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
cd wagtail-translate
# initialize pre-commit
pre-commit install

# Optional, run all checks once for this, then the checks will run only on the changed files
git ls-files --others --cached --exclude-standard | xargs pre-commit run --files
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
