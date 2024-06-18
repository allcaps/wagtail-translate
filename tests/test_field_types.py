import pytest

from django.db import models
from wagtail.fields import RichTextField

from tests.factories import BlogPostPageFactory, LocaleFactory


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
