## Customise Wagtail Translate

Multi-language projects often have specific requirements for the translation process.
This page provides examples of how to customize Wagtail Translate to fit your project's needs.

### Custom translator

A custom translator allows you to integrate with any machine translation service.

To create a custom translator, subclass the `BaseTranslator`  and override `translate`. In `your_app/translators.py`:

```python
from wagtail_translate.translators.base import BaseTranslator

import foo_translation_service

class FooTranslator(BaseTranslator):
    def translate(self, source_string: str) -> str:
        # Use the translation service to translate the text
        translation = foo_translation_service(
            source_string,
            self.source_language_code,
            self.target_language_code
        )
        return translation
```

In your settings, define `WAGTAIL_TRANSLATE_TRANSLATOR = "your_app.translators.FooTranslator"`.


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
from wagtail_translate.translators.deepl import DeepLTranslator

# Wagtail 6.2 introduces the `copy_for_translation_done` signal.
try:
    from wagtail.signals import copy_for_translation_done
except ImportError:
    from wagtail_translate.signals import copy_for_translation_done

@receiver(copy_for_translation_done)
def translation_done_receiver(sender, source_obj, target_obj, **kwargs):
    # Get the source and target language codes
    source_language_code = source_obj.locale.language_code
    target_language_code = target_obj.locale.language_code

    # Initialize the translator, and translate.
    translator = DeepLTranslator(source_language_code, target_language_code)
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

DeepL doesn't support Icelandic. So, we want to use some `CustomIcelandicTranslator` for Icelandic translations and `DeeplTranslator` for all other languages.

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
        translator_class = DeeplTranslator

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
