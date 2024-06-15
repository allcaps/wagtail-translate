import uuid

import pytest

from wagtail import blocks
from wagtail.fields import StreamField

from tests.factories import BlogPostPageFactory, LocaleFactory


pytestmark = pytest.mark.django_db


def test_body_field_is_streamfield():
    page = BlogPostPageFactory()
    field = page._meta.get_field("body")
    assert isinstance(field, StreamField)


def test_streamfield_translate_char_block():
    page = BlogPostPageFactory(
        body=[
            {"type": "heading", "value": "Hello heading", "id": str(uuid.uuid4())},
        ]
    )
    translation = page.copy_for_translation(LocaleFactory())
    field = translation._meta.get_field("body")
    assert isinstance(field.stream_block.child_blocks["heading"], blocks.CharBlock)
    assert translation.body[0].value == "Uryyb urnqvat"


def test_streamfield_translate_rich_text_block():
    page = BlogPostPageFactory(
        body=[
            {
                "type": "paragraph",
                "value": "<p>Hello <em>richtext</em></p>",
                "id": str(uuid.uuid4()),
            },
        ]
    )
    translation = page.copy_for_translation(LocaleFactory())
    field = translation._meta.get_field("body")
    assert isinstance(
        field.stream_block.child_blocks["paragraph"], blocks.RichTextBlock
    )
    assert str(translation.body[0].value) == "<p>Uryyb <em>evpugrkg</em></p>"
