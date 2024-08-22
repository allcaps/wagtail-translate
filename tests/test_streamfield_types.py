import uuid

import pytest

from wagtail.fields import StreamField
from wagtail_factories import DocumentFactory

from tests.factories import BlogPostPageFactory, ImageFactory, LocaleFactory
from tests.testapp.models import BlogCategory


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


def test_streamfield_image_struct_block():
    image = ImageFactory()
    page = BlogPostPageFactory(
        body=[
            {
                "type": "image_struct",
                "value": {"image": image.pk, "caption": "One Two Three"},
                "id": str(uuid.uuid4()),
            }
        ]
    )
    translation = page.copy_for_translation(LocaleFactory())
    assert translation.body[0].value["image"] == image
    assert translation.body[0].value["caption"] == "Bar Gjb Guerr"


def test_streamfield_raw_block():
    page = BlogPostPageFactory(
        body=[
            {
                "type": "raw",
                "value": '<p data-test="One" title="Two">Three</p>',
                "id": str(uuid.uuid4()),
            }
        ]
    )
    translation = page.copy_for_translation(LocaleFactory())
    # Only stings, title and alt attributes are translated
    assert translation.body[0].value == '<p data-test="One" title="Gjb">Guerr</p>'


def test_streamfield_blockquote_block():
    page = BlogPostPageFactory(
        body=[
            {"type": "block_quote", "value": "One Two Three", "id": str(uuid.uuid4())}
        ]
    )
    translation = page.copy_for_translation(LocaleFactory())
    assert translation.body[0].value == "Bar Gjb Guerr"


def test_streamfield_page_block():
    locale_en = LocaleFactory(language_code="en")  # the default language
    locale_fr = LocaleFactory(language_code="fr")
    target_page = BlogPostPageFactory()
    page = BlogPostPageFactory(
        body=[{"type": "page", "value": target_page.pk, "id": str(uuid.uuid4())}]
    )
    translation = page.copy_for_translation(locale_fr)

    # Since there is NO translation, the original target page is used.
    assert translation.body[0].value.locale == locale_en
    assert translation.body[0].value.specific == target_page

    # Create a translation for the target page, the translated page is used.
    translation.delete()
    target_page_translation = target_page.copy_for_translation(locale_fr)
    target_page_translation.save_revision().publish()
    translation = page.copy_for_translation(locale_fr)
    assert translation.body[0].value.locale == locale_fr
    assert translation.body[0].value.specific == target_page_translation


def test_streamfield_document_block():
    document = DocumentFactory()
    page = BlogPostPageFactory(
        body=[{"type": "document", "value": document.pk, "id": str(uuid.uuid4())}]
    )
    translation = page.copy_for_translation(LocaleFactory())
    assert translation.body[0].value == document


def test_streamfield_image_chooser_block():
    image = ImageFactory()
    page = BlogPostPageFactory(
        body=[{"type": "image_chooser", "value": image.pk, "id": str(uuid.uuid4())}]
    )
    translation = page.copy_for_translation(LocaleFactory())
    assert translation.body[0].value == image


def test_streamfield_snippet_block():
    locale_en = LocaleFactory(language_code="en")  # the default language
    locale_fr = LocaleFactory(language_code="fr")
    snippet = BlogCategory.objects.create(name="One Two Three")
    page = BlogPostPageFactory(
        body=[{"type": "snippet", "value": snippet.pk, "id": str(uuid.uuid4())}]
    )
    translation = page.copy_for_translation(locale_fr)

    # Since there is NO translation, the original snippet is used.
    assert translation.body[0].value == snippet
    assert translation.body[0].value.locale == locale_en

    # Create a translation for the target page, the translated page is used.
    translation.delete()
    snippet_translation = snippet.copy_for_translation(locale_fr)
    translation = page.copy_for_translation(locale_fr)
    assert translation.body[0].value == snippet_translation
    assert translation.body[0].value.locale == locale_fr
