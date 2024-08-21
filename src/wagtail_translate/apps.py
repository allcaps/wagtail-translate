import wagtail

from django.apps import AppConfig


def page_patch_needed(version=wagtail.VERSION) -> bool:
    """
    Wagtail 6.2 introduces the `copy_for_translation_done` signal for **pages**.
    Older Wagtail versions need to be patched.
    """
    return version[0] < 6 or (version[0] == 6 and version[1] < 2)


def model_patch_needed(version=wagtail.VERSION) -> bool:
    """
    Wagtail 6.3 introduces the `copy_for_translation_done` signal for **models**.
    Older Wagtail versions need to be patched.
    """
    return version[0] < 6 or (version[0] == 6 and version[1] < 3)


class WagtailTranslateAppConfig(AppConfig):
    label = "wagtail_translate"
    name = "wagtail_translate"
    verbose_name = "Wagtail Translate"

    def ready(self):
        if page_patch_needed():
            from . import monkeypatch_page  # noqa
        if model_patch_needed():
            from . import monkeypatch_model  # noqa
