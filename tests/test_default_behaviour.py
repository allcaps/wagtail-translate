from unittest.mock import Mock

from wagtail.models import Locale

from tests.testproject.demoapp.models import BlogPostPage
from wagtail_translate.default_behaviour import signals


def test_unpublished_page_translation_uses_latest_revision(monkeypatch):
    source = BlogPostPage(
        title="Stored title",
        locale=Locale(language_code="nl"),
        live=False,
    )
    latest_source = BlogPostPage(
        title="Latest draft title",
        locale=source.locale,
        live=False,
    )
    source.get_latest_revision_as_object = Mock(return_value=latest_source)
    target = BlogPostPage(locale=Locale(language_code="fr"))

    translated_obj = Mock()
    translator = Mock()
    translator.translate_obj.return_value = translated_obj
    translator_class = Mock(return_value=translator)
    monkeypatch.setattr(signals, "load_class", Mock(return_value=translator_class))

    signals.handle_translation_done_signal(
        sender=object(), source_obj=source, target_obj=target
    )

    translator_class.assert_called_once_with("nl", "fr")
    translator.translate_obj.assert_called_once_with(latest_source, target)
    translated_obj.save.assert_called_once_with()


def test_published_page_translation_uses_published_page(monkeypatch):
    source = BlogPostPage(
        title="Published title",
        locale=Locale(language_code="nl"),
        live=True,
    )
    source.get_latest_revision_as_object = Mock()
    target = BlogPostPage(locale=Locale(language_code="fr"))

    translated_obj = Mock()
    translator = Mock()
    translator.translate_obj.return_value = translated_obj
    translator_class = Mock(return_value=translator)
    monkeypatch.setattr(signals, "load_class", Mock(return_value=translator_class))

    signals.handle_translation_done_signal(
        sender=object(), source_obj=source, target_obj=target
    )

    source.get_latest_revision_as_object.assert_not_called()
    translator_class.assert_called_once_with("nl", "fr")
    translator.translate_obj.assert_called_once_with(source, target)
    translated_obj.save.assert_called_once_with()
