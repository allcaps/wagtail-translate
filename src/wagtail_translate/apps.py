from django.apps import AppConfig


class WagtailTranslateAppConfig(AppConfig):
    label = "wagtail_translate"
    name = "wagtail_translate"
    verbose_name = "Wagtail Translate"

    def ready(self):
        # We patch Wagtail to inject the copy_for_translation_done signal.
        from . import monkeypatches  # noqa
