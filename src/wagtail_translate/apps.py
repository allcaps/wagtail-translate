import wagtail

from django.apps import AppConfig


def patch_needed(version=wagtail.VERSION) -> bool:
    """
    Wagtail 6.2 introduces the `copy_for_translation_done` signal.
    Older Wagtail versions need to be patched.
    """
    return version[0] < 6 or (version[0] == 6 and version[1] < 2)


class WagtailTranslateAppConfig(AppConfig):
    label = "wagtail_translate"
    name = "wagtail_translate"
    verbose_name = "Wagtail Translate"

    def ready(self):
        if patch_needed():
            from . import monkeypatches  # noqa
