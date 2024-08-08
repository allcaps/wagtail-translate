import pytest

from django.db import models
from wagtail.fields import RichTextField

from tests.factories import BlogPostPageFactory, LocaleFactory
from tests.testapp.models import BlogCategory, BlogPostPage


pytestmark = pytest.mark.django_db


def test_translate_charfield():
    page = BlogPostPageFactory(title="Hello first post")
    translation = page.copy_for_translation(LocaleFactory())
    field = translation._meta.get_field("title")
    assert isinstance(field, models.CharField)
    assert translation.title == "Uryyb svefg cbfg"


def test_translate_rich_text_field():
    page = BlogPostPageFactory(intro="<p>Hello <em>world</em></p>")
    translation = page.copy_for_translation(LocaleFactory())
    field = translation._meta.get_field("intro")
    assert isinstance(field, RichTextField)
    assert translation.intro == "<p>Uryyb <em>jbeyq</em></p>"


def test_translate_fk_snippet():
    locale_en = LocaleFactory(language_code="en")  # the default language
    locale_fr = LocaleFactory(language_code="fr")
    category = BlogCategory.objects.create(name="One Two Three")
    page = BlogPostPageFactory(title="One", category=category)
    translated_page = page.copy_for_translation(locale_fr)

    # Since there is NO translation, the original snippet is used.
    assert translated_page.category == category
    assert translated_page.category.locale == locale_en

    # Create a translation for the target page, the translated page is used.
    translated_page.delete()
    translated_snippet = category.copy_for_translation(locale_fr)

    assert BlogPostPage.objects.count() == 1
    assert BlogCategory.objects.count() == 2

    translated_page = page.copy_for_translation(locale_fr)
    assert translated_page.category == translated_snippet
    assert translated_page.category.locale == locale_fr
