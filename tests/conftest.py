import pytest


@pytest.fixture(autouse=True)
def temporary_media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"


@pytest.fixture(autouse=True)
def deterministic_translator(settings):
    settings.WAGTAIL_TRANSLATE_TRANSLATOR = (
        "wagtail_translate.translators.rot13.ROT13HTMLDocumentTranslator"
    )
