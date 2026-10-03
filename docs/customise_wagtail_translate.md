## How to customise Wagtail Translate

Multi-language projects often have specific requirements for the translation process.
This page provides examples of how to customize Wagtail Translate to fit your project's needs.

### Custom translator

A custom translator allows you to integrate with any machine translation service.

To create a custom translator, subclass `HTMLDocumentTranslator` and implement one
method that translates a complete protected HTML document:

```python
from wagtail_translate.translators.document import HTMLDocumentTranslator

import foo_translation_service

class FooTranslator(HTMLDocumentTranslator):
    def translate_document_html(self, html: str) -> str:
        return foo_translation_service(
            html,
            self.source_language_code,
            self.target_language_code
        )
```

In your settings, define `WAGTAIL_TRANSLATE_TRANSLATOR = "your_app.translators.FooTranslator"`.

### Whole-document translation with a local LLM

The optional LLM translator sends the protected HTML document to an
OpenAI-compatible Chat Completions endpoint. It defaults to local Ollama:

```sh
python -m pip install "wagtail-translate[llm]"
```

Configure the translator and model:

```python
WAGTAIL_TRANSLATE_TRANSLATOR = (
    "wagtail_translate.translators.openai_compatible.LLMHTMLDocumentTranslator"
)
WAGTAIL_TRANSLATE_LLM_MODEL = "translategemma:4b"
WAGTAIL_TRANSLATE_LLM_BASE_URL = "http://localhost:11434/v1/"
WAGTAIL_TRANSLATE_LLM_API_KEY = "ollama"
```

You can add project-specific translation guidance without replacing the package's
structural instructions:

```python
WAGTAIL_TRANSLATE_LLM_INSTRUCTIONS = """
Use formal Dutch. Keep product names and ACME untranslated.
"""
```

The translator validates the complete HTML response before changing the target
object. Field, block, attribute, and opaque-node references must remain complete
and unique, and HTML elements must retain the same structure.

If the model request or validation still fails, the translator raises a
`DocumentTranslationRequestError` or `DocumentTranslationValidationError`. It
does not partially apply fields. Wagtail has already created the target copy when
the translation signal runs, so that untranslated copy remains available for
review or retry.

The default signal handler remains synchronous. Use a custom signal handler, as
described below, when requests need to run through a background worker or custom
retry policy.

### Advanced custom behaviour

For fine-grained control over how translations are handled, and other translation behaviours, you can replace the default behaviour with a custom signal handler.

In `settings.py` remove the default behaviour:
- From `INSTALLED_APPS` remove `"wagtail_translate.default_behaviour"`
- Remove `WAGTAIL_TRANSLATE_TRANSLATOR = "..."`

Create and enable the custom signal handler, in `your_app/apps.py`:

```python
from django.apps import AppConfig


class YourAppConfig(AppConfig):
    name = "your_app"

    def ready(self):
        from . import signals  # noqa
```
Add `your_app/signals.py`:

```python
from django.dispatch import receiver
from wagtail.models import Page

# Direct import of the translator class,
# makes the WAGTAIL_TRANSLATE_TRANSLATOR setting redundant.
from wagtail_translate.translators.deepl import DeepLHTMLDocumentTranslator

from wagtail.signals import copy_for_translation_done

@receiver(copy_for_translation_done)
def translation_done_receiver(sender, source_obj, target_obj, **kwargs):
    # Get the source and target language codes
    source_language_code = source_obj.locale.language_code
    target_language_code = target_obj.locale.language_code

    # Initialize the translator, and translate.
    translator = DeepLHTMLDocumentTranslator(
        source_language_code, target_language_code
    )
    translated_obj = translator.translate_obj(source_obj, target_obj)

    # Save the translated object
    if isinstance(translated_obj, Page):
        translated_obj.save_revision()
    else:
        translated_obj.save()
```

You now have ejected from the Wagtail Translate default behaviour and can customize translation process and other behaviours.

### Using different translation services for different languages

Using different translation services for different languages allows you to choose the best tool for each language, improving translation accuracy and reliability.

If one service does not support a language, select a custom translator for that
language and `DeepLHTMLDocumentTranslator` for the others.

```python
...

ICELANDIC = "is"

@receiver(copy_for_translation_done)
def translation_done_receiver(sender, source_obj, target_obj, **kwargs):
    source_language_code = source_obj.locale.language_code
    target_language_code = target_obj.locale.language_code

    # Select the appropriate translator based on the language
    if source_language_code == ICELANDIC or target_language_code == ICELANDIC:
        translator_class = CustomIcelandicTranslator
    else:
        translator_class = DeepLHTMLDocumentTranslator

    translator = translator_class(source_language_code, target_language_code)
    translated_obj = translator.translate_obj(source_obj, target_obj)

    # Save the translated object
    if isinstance(translated_obj, Page):
        translated_obj.save_revision()
    else:
        translated_obj.save()
```

### Direct publishing of translations

By default, Wagtail Translate saves the translated page as a draft. This allows content editors to review the translation before publishing it. Here we enable direct publishing of the translated page.

First, eject from the default behaviour, like described in "Advanced custom behaviour".

Add `.publish()` to the `save_revision` method:

```python
    ...
    translated_obj.save_revision().publish()
```

### Store the source locale on the translated object

Storing the source locale on the translated object helps content editors to understand the context of the translation.

First, eject from the default behaviour, like described in "Advanced custom behaviour".

Add a `source_locale` field to your model:

```python

@register_snippet
class Advert(TranslatableMixin, models.Model):
    name = models.CharField(max_length=255)
    source_locale = models.ForeignKey(
        Locale,
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )
    ...

    panels = [
        FieldPanel("name"),
        FieldPanel("source_locale", readonly=True),
    ]
```
Run `makemigrations` and `migrate` to add the field to the database.

Set the `source_locale` field:

```python
@receiver(copy_for_translation_done)
def translation_done_receiver(sender, source_obj, target_obj, **kwargs):
    ...
    translated_obj.source_locale = source_obj.locale
    translated_obj.save()
```
