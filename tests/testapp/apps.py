from django.apps import AppConfig


class TestAppAppConfig(AppConfig):
    label = "testapp"
    name = "tests.testapp"
    verbose_name = "Test App"
    default_auto_field = "django.db.models.BigAutoField"
