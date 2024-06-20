import importlib

from django.conf import settings
from django.dispatch import receiver
from wagtail.models import Page


# Wagtail 6.2 introduces the `copy_for_translation_done` signal.
try:
    from wagtail.signals import copy_for_translation_done
except ImportError:
    from wagtail_translate.signals import copy_for_translation_done


def load_class(class_path):
    parts = class_path.rsplit(".", 1)
    module_path = parts[0]
    class_name = parts[1]
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


@receiver(copy_for_translation_done)
def handle_translation_done_signal(sender, source_obj, target_obj, **kwargs):
    # Get the source and target language codes
    source_language_code = source_obj.locale.language_code
    target_language_code = target_obj.locale.language_code

    # Initialize the translator, and translate.
    loaded_class = load_class(settings.WAGTAIL_TRANSLATE_TRANSLATOR)
    translator = loaded_class(source_language_code, target_language_code)
    translated_obj = translator.translate_obj(source_obj, target_obj)

    # Differentiate between regular Django model and Wagtail Page.
    # - Page instances have `save_revision` and `publish` methods.
    # - Regular Django model (aka Wagtail Snippet) has a `save` method.
    if isinstance(translated_obj, Page):
        translated_obj.save_revision()
    else:
        translated_obj.save()
