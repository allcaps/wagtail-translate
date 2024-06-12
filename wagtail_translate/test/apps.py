from django.apps import AppConfig


class WagtailTranslateTestAppConfig(AppConfig):
    label = "wagtail_translate_test"
    name = "wagtail_translate.test"
    verbose_name = "Wagtail Translate tests"

    def ready(self):
        # We patch Wagtail to inject the copy_for_translation_done signal.
        from . import signals  # noqa
