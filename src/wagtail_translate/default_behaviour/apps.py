from django.apps import AppConfig


class TestAppAppConfig(AppConfig):
    name = "wagtail_translate.default_behaviour"

    def ready(self):
        from . import signals  # noqa
