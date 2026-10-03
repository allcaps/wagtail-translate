## How to customise Wagtail Translate

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

### Whole-document translation with Pydantic AI

The optional document translator sends the selected text for one page or snippet
to one Pydantic AI model run. It is provider-neutral. Install the package extra
and the Pydantic AI integration for the provider you want to use. For example:

```sh
python -m pip install "wagtail-translate[llm]" "pydantic-ai-slim[openai]"
```

Configure the translator and a Pydantic AI `provider:model` identifier:

```python
WAGTAIL_TRANSLATE_TRANSLATOR = (
    "wagtail_translate.translators.pydantic_ai.PydanticAIDocumentTranslator"
)
WAGTAIL_TRANSLATE_LLM_MODEL = "openai:gpt-5-mini"
```

Provider credentials use the provider's standard configuration. For OpenAI, for
example, set `OPENAI_API_KEY` in the process environment.

You can add project-specific translation guidance without replacing the package's
structural instructions:

```python
WAGTAIL_TRANSLATE_LLM_INSTRUCTIONS = """
Use formal Dutch. Keep product names and ACME untranslated.
"""
```

The translator validates the complete structured response before changing the
target object. Fragment references must be complete and unique, HTML elements
must retain the same structure, and protected attributes must retain their local
references. Pydantic AI gets one repair attempt when these checks fail.

If the model request or validation still fails, the translator raises a
`DocumentTranslationRequestError` or `DocumentTranslationValidationError`. It
does not partially apply fields. Wagtail has already created the target copy when
the translation signal runs, so that untranslated copy remains available for
review or retry.

The default signal handler remains synchronous. Use a custom signal handler, as
described below, when requests need to run through a background worker or custom
retry policy.

#### Local Ollama

Ollama exposes an OpenAI-compatible endpoint, so its Pydantic AI integration uses
the `openai` provider dependency. Install the convenience extra:

```sh
python -m pip install "wagtail-translate[ollama]"
```

Start Ollama, make sure the model is installed, and configure its endpoint:

```sh
ollama pull translategemma:4b
export OLLAMA_BASE_URL="http://localhost:11434/v1"
```

Then select it in Django:

```python
WAGTAIL_TRANSLATE_TRANSLATOR = (
    "wagtail_translate.translators.pydantic_ai.PydanticAIDocumentTranslator"
)
WAGTAIL_TRANSLATE_LLM_MODEL = "ollama:translategemma:4b"
```

No Hugging Face tokenizer or `AutoModelForCausalLM` is needed: Ollama owns model
loading and inference. The translator automatically uses Ollama's native JSON
schema output instead of tool calling, which allows completion-only models such
as TranslateGemma to return the required structured response.


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
