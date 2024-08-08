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
            {"type": "heading", "value": "One Two Three", "id": str(uuid.uuid4())},
        ]
    )
    translation = page.copy_for_translation(LocaleFactory())
    field = translation._meta.get_field("body")
    assert isinstance(field.stream_block.child_blocks["heading"], blocks.CharBlock)
    assert translation.body[0].value == "Bar Gjb Guerr"


def test_streamfield_translate_rich_text_block():
    page = BlogPostPageFactory(
        body=[
            {
                "type": "paragraph",
                "value": "<p>One <em>Two</em></p>",
                "id": str(uuid.uuid4()),
            },
        ]
    )
    translation = page.copy_for_translation(LocaleFactory())
    field = translation._meta.get_field("body")
    assert isinstance(
        field.stream_block.child_blocks["paragraph"], blocks.RichTextBlock
    )
    assert str(translation.body[0].value).strip() == "<p>Bar <em>Gjb</em></p>"


def test_streamfield_stream_block():
    page = BlogPostPageFactory(
        body=[
            {
                "type": "stream",
                "value": [
                    {
                        "type": "paragraph",
                        "value": "One",
                        "id": str(uuid.uuid4()),
                    },
                    {
                        "type": "paragraph",
                        "value": "Two",
                        "id": str(uuid.uuid4()),
                    },
                    {
                        "type": "paragraph",
                        "value": "Three",
                        "id": str(uuid.uuid4()),
                    },
                ],
                "id": str(uuid.uuid4()),
            },
        ]
    )
    translation = page.copy_for_translation(LocaleFactory())
    field = translation._meta.get_field("body")
    assert isinstance(field.stream_block.child_blocks["stream"], blocks.StreamBlock)
    assert str(translation.body[0].value) == "\n".join(
        [
            """<div class="block-paragraph">Bar</div>""",
            """<div class="block-paragraph">Gjb</div>""",
            """<div class="block-paragraph">Guerr</div>""",
        ]
    )


def test_streamfield_stream_nested_block():
    page = BlogPostPageFactory(
        body=[
            {
                "type": "stream_nested",
                "value": [
                    {
                        "type": "stream",
                        "value": [
                            {
                                "type": "paragraph",
                                "value": "One",
                                "id": str(uuid.uuid4()),
                            },
                            {
                                "type": "paragraph",
                                "value": "Two",
                                "id": str(uuid.uuid4()),
                            },
                            {
                                "type": "paragraph",
                                "value": "Three",
                                "id": str(uuid.uuid4()),
                            },
                        ],
                        "id": str(uuid.uuid4()),
                    }
                ],
                "id": str(uuid.uuid4()),
            }
        ]
    )
    translation = page.copy_for_translation(LocaleFactory())
    field = translation._meta.get_field("body")
    assert isinstance(field.stream_block.child_blocks["stream"], blocks.StreamBlock)
    assert str(translation.body[0].value) == "".join(
        [
            """<div class="block-stream">""",
            "\n".join(
                [
                    """<div class="block-paragraph">Bar</div>""",
                    """<div class="block-paragraph">Gjb</div>""",
                    """<div class="block-paragraph">Guerr</div>""",
                ]
            ),
            """</div>""",
        ]
    )


def test_streamfield_list_block():
    page = BlogPostPageFactory(
        body=[
            {
                "type": "list",
                "value": [
                    {"type": "item", "value": "One", "id": str(uuid.uuid4())},
                    {"type": "item", "value": "Two", "id": str(uuid.uuid4())},
                    {"type": "item", "value": "Three", "id": str(uuid.uuid4())},
                ],
                "id": str(uuid.uuid4()),
            }
        ]
    )
    translation = page.copy_for_translation(LocaleFactory())
    field = translation._meta.get_field("body")
    assert isinstance(field.stream_block.child_blocks["stream"], blocks.StreamBlock)
    assert list(translation.body[0].value) == [
        "Bar",
        "Gjb",
        "Guerr",
    ]


def test_streamfield_list_nested_block():
    page = BlogPostPageFactory(
        body=[
            {
                "type": "list_nested",
                "value": [
                    {
                        "type": "item",
                        "value": [
                            {
                                "type": "item",
                                "value": "One 1",
                                "id": str(uuid.uuid4()),
                            },
                            {
                                "type": "item",
                                "value": "Two 1",
                                "id": str(uuid.uuid4()),
                            },
                            {
                                "type": "item",
                                "value": "Three 1",
                                "id": str(uuid.uuid4()),
                            },
                        ],
                        "id": str(uuid.uuid4()),
                    },
                    {
                        "type": "item",
                        "value": [
                            {
                                "type": "item",
                                "value": "One 2",
                                "id": str(uuid.uuid4()),
                            },
                            {
                                "type": "item",
                                "value": "Two 2",
                                "id": str(uuid.uuid4()),
                            },
                            {
                                "type": "item",
                                "value": "Three 2",
                                "id": str(uuid.uuid4()),
                            },
                        ],
                        "id": str(uuid.uuid4()),
                    },
                ],
                "id": str(uuid.uuid4()),
            }
        ]
    )
    translation = page.copy_for_translation(LocaleFactory())
    field = translation._meta.get_field("body")
    assert isinstance(field.stream_block.child_blocks["stream"], blocks.StreamBlock)
    assert [list(item) for item in translation.body[0].value] == [
        [
            "Bar 1",
            "Gjb 1",
            "Guerr 1",
        ],
        [
            "Bar 2",
            "Gjb 2",
            "Guerr 2",
        ],
    ]


# TODO: test_streamfield_image_struct_block
# TODO: test_streamfield_raw_block
# TODO: test_streamfield_blockquoteblock_block
# TODO: test_streamfield_page_block
# TODO: test_streamfield_document_block
# TODO: test_streamfield_image_chooser_block
# TODO: test_streamfield_snippet_block
