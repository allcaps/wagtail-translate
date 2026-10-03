# ruff: noqa: E402

import copy

import pytest


pytest.importorskip("pydantic_ai")

from django.core.exceptions import ImproperlyConfigured
from pydantic_ai import ModelResponse
from pydantic_ai.messages import ToolCallPart
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.models.test import TestModel
from pydantic_ai.output import NativeOutput
from wagtail import blocks

from tests.testapp.models import BlogPostPage
from wagtail_translate.translators.exceptions import (
    DocumentTranslationRequestError,
    DocumentTranslationValidationError,
)
from wagtail_translate.translators.pydantic_ai import (
    DocumentFragment,
    PydanticAIDocumentTranslator,
    TranslatedFragment,
    TranslationDocument,
    TranslationResponse,
    TranslationRun,
    prepare_html,
    restore_html,
)


pytestmark = pytest.mark.django_db


def make_translator(settings):
    settings.WAGTAIL_TRANSLATE_LLM_MODEL = "test:test"
    return PydanticAIDocumentTranslator("en", "fr")


def test_translate_object_in_one_run_and_ignore_response_order(settings):
    source = BlogPostPage(
        title="Hello",
        intro="<p>The <em>black</em> cat</p>",
        body=[
            ("heading", "Introduction"),
            ("list_nested", [["One", "Two"]]),
            ("struct", {"paragraph": "Caption", "image": None}),
        ],
    )
    target = copy.copy(source)
    translator = make_translator(settings)
    run = translator._extract_document(source)

    translated_text = {
        "field:title": "Bonjour",
        "field:intro": "[[E0]]Le chat [[E1]]noir[[/E1]][[/E0]]",
        "field:body/block:0:heading": "Présentation",
        "field:body/block:1:list_nested/item:0/item:0": "Un",
        "field:body/block:1:list_nested/item:0/item:1": "Deux",
        "field:body/block:2:struct/child:paragraph": "Légende",
    }
    response = {
        "fragments": [
            {"ref": fragment.ref, "text": translated_text[fragment.ref]}
            for fragment in reversed(run.fragments)
        ]
    }

    with translator.agent.override(model=TestModel(custom_output_args=response)):
        result = translator.translate_obj(source, target)

    assert result is target
    assert target.title == "Bonjour"
    assert target.intro == "<p>Le chat <em>noir</em></p>"
    assert target.body[0].value == "Présentation"
    assert [list(items) for items in target.body[1].value] == [["Un", "Deux"]]
    assert target.body[2].value["paragraph"] == "Légende"
    assert target.body.raw_data[0]["value"] == "Présentation"

    assert source.title == "Hello"
    assert source.intro == "<p>The <em>black</em> cat</p>"
    assert source.body[0].value == "Introduction"
    assert [list(items) for items in source.body[1].value] == [["One", "Two"]]


def test_arbitrarily_nested_struct_blocks_are_traversed(settings):
    nested_block = blocks.StructBlock(
        [
            (
                "outer",
                blocks.StructBlock(
                    [("inner", blocks.StructBlock([("text", blocks.CharBlock())]))]
                ),
            )
        ]
    )
    value = nested_block.to_python({"outer": {"inner": {"text": "Hello"}}})
    translator = make_translator(settings)
    fragments = []

    translator._extract_block(nested_block, value, "field:nested", fragments, {})

    assert [fragment.ref for fragment in fragments] == [
        "field:nested/child:outer/child:inner/child:text"
    ]


def test_html_attributes_and_technical_content_are_restored():
    source = (
        '<p class="lede">Hello <a linktype="page" id="123" '
        'title="The link">world</a><!-- editor note -->'
        '<code data-language="python">print("hello")</code></p>'
    )
    prepared, preservation, has_content = prepare_html(source)

    assert has_content is True
    assert "linktype" not in prepared
    assert 'id="123"' not in prepared
    assert "The link" in prepared
    assert 'class="lede"' not in prepared
    assert "data-wagtail-translate-ref" not in prepared
    assert "editor note" not in prepared
    assert 'print("hello")' not in prepared

    translated = prepared.replace("Hello", "Bonjour")
    translated = translated.replace("The link", "Le lien")
    translated = translated.replace("world", "monde")
    restored = restore_html(translated, preservation)

    assert '<p class="lede">' in restored
    assert 'linktype="page"' in restored
    assert 'id="123"' in restored
    assert 'title="Le lien"' in restored
    assert "<!-- editor note -->" in restored
    assert '<code data-language="python">print("hello")</code>' in restored
    assert "data-wagtail-translate-ref" not in restored


def test_nested_technical_subtree_uses_one_preservation_reference():
    source = "<p>Hello</p><pre><code>print('hello')</code></pre>"

    prepared, preservation, _ = prepare_html(source)
    restored = restore_html(prepared.replace("Hello", "Bonjour"), preservation)

    preserved_subtrees = [
        element.subtree_html
        for element in preservation.elements
        if element.subtree_html is not None
    ]
    assert preserved_subtrees == ["<pre><code>print('hello')</code></pre>"]
    assert restored == "<p>Bonjour</p><pre><code>print('hello')</code></pre>"


def test_model_authored_html_is_escaped():
    source = '<p class="lede">Hello <em>world</em></p>'
    prepared, preservation, _ = prepare_html(source)

    translated = prepared.replace("Hello", '<span lang="fr">Bonjour</span>')
    translated = translated.replace("world", "monde")

    restored = restore_html(translated, preservation)

    assert restored == (
        '<p class="lede">&lt;span lang="fr"&gt;Bonjour&lt;/span&gt; '
        "<em>monde</em></p>"
    )


def test_trailing_container_marker_may_be_omitted():
    prepared, preservation, _ = prepare_html("<p>Hello <em>world</em></p>")
    translated = prepared.replace("Hello", "Bonjour").replace("world", "monde")

    restored = restore_html(translated.removesuffix("[[/E0]]"), preservation)

    assert restored == "<p>Bonjour <em>monde</em></p>"


def test_single_bracket_marker_variant_is_normalized():
    _, preservation, _ = prepare_html("<p>Hello <em>world</em></p>")

    restored = restore_html("[[E0]Bonjour [[E1]]monde[[/E1]][/E0]", preservation)

    assert restored == "<p>Bonjour <em>monde</em></p>"


@pytest.mark.parametrize(
    "translated_html",
    [
        "<p>Hello <strong>world</strong></p>",
        "<div><p>Hello <em>world</em></p></div>",
    ],
)
def test_html_structure_changes_are_rejected(translated_html):
    _, preservation, _ = prepare_html("<p>Hello <em>world</em></p>")

    with pytest.raises(DocumentTranslationValidationError):
        restore_html(translated_html, preservation)


@pytest.mark.parametrize(
    "returned_refs, message",
    [
        (["field:title"], "Missing fragment references"),
        (
            ["field:title", "field:intro", "field:intro"],
            "Duplicate fragment references",
        ),
        (
            ["field:title", "field:intro", "field:unknown"],
            "Unknown fragment references",
        ),
    ],
)
def test_fragment_reference_validation(returned_refs, message):
    run = TranslationRun(
        fragments=[
            DocumentFragment(ref="field:title", kind="text", text="Title"),
            DocumentFragment(ref="field:intro", kind="text", text="Intro"),
        ],
        html_preservations={},
    )
    response = TranslationResponse(
        fragments=[
            TranslatedFragment(ref=ref, text="Translated") for ref in returned_refs
        ]
    )

    with pytest.raises(DocumentTranslationValidationError, match=message):
        run.validate(response)


def test_validation_failure_does_not_mutate_target(settings):
    source = BlogPostPage(title="Hello", intro="<p>Introduction</p>", body=[])
    target = copy.copy(source)
    target.title = "Existing title"
    target.intro = "<p>Existing introduction</p>"
    translator = make_translator(settings)
    response = {
        "fragments": [{"ref": "field:title", "text": "Bonjour"}],
    }

    with translator.agent.override(model=TestModel(custom_output_args=response)):
        with pytest.raises(DocumentTranslationValidationError):
            translator.translate_obj(source, target)

    assert target.title == "Existing title"
    assert target.intro == "<p>Existing introduction</p>"


def test_request_failure_does_not_mutate_target(settings):
    source = BlogPostPage(title="Hello", intro="", body=[])
    target = copy.copy(source)
    target.title = "Existing title"
    translator = make_translator(settings)

    def fail_request(messages, info):
        raise RuntimeError("Provider unavailable")

    with translator.agent.override(model=FunctionModel(fail_request)):
        with pytest.raises(
            DocumentTranslationRequestError, match="Provider unavailable"
        ):
            translator.translate_obj(source, target)

    assert target.title == "Existing title"


def test_empty_document_skips_model_request(settings):
    source = BlogPostPage(title="", intro="", body=[])
    target = copy.copy(source)
    translator = make_translator(settings)
    calls = 0

    def count_request(messages, info):
        nonlocal calls
        calls += 1
        raise AssertionError("The model must not be called for an empty document")

    with translator.agent.override(model=FunctionModel(count_request)):
        translator.translate_obj(source, target)

    assert calls == 0


def test_model_setting_is_required(settings):
    del settings.WAGTAIL_TRANSLATE_LLM_MODEL

    with pytest.raises(ImproperlyConfigured, match="WAGTAIL_TRANSLATE_LLM_MODEL"):
        PydanticAIDocumentTranslator("en", "fr")


def test_invalid_first_response_gets_one_repair_attempt(settings):
    source = BlogPostPage(title="Hello", intro="", body=[])
    target = copy.copy(source)
    translator = make_translator(settings)
    calls = 0

    def respond(messages, info):
        nonlocal calls
        calls += 1
        if calls == 1:
            arguments = {"fragments": []}
        else:
            arguments = {"fragments": [{"ref": "field:title", "text": "Bonjour"}]}
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, arguments)])

    with translator.agent.override(model=FunctionModel(respond)):
        translator.translate_obj(source, target)

    assert calls == 2
    assert target.title == "Bonjour"


def test_custom_instructions_are_added(settings):
    settings.WAGTAIL_TRANSLATE_LLM_MODEL = "test:test"
    settings.WAGTAIL_TRANSLATE_LLM_INSTRUCTIONS = "Use formal French."

    translator = PydanticAIDocumentTranslator("en", "fr")

    assert "Use formal French." in translator.instructions


def test_translation_prompt_keeps_instructions_with_document(settings):
    translator = make_translator(settings)
    run = translator._extract_document(BlogPostPage(title="Hello", intro="", body=[]))
    document = TranslationDocument(
        source_language="en",
        target_language="fr",
        model_label="testapp.BlogPostPage",
        fragments=run.fragments,
    )
    prompt = translator._translation_prompt(document)

    assert "professional English (en) to\nFrench (fr) translator" in prompt
    assert '"text": "Hello"' in prompt


def test_ollama_uses_native_structured_output(settings):
    settings.WAGTAIL_TRANSLATE_LLM_MODEL = "ollama:qwen3:4b"

    translator = PydanticAIDocumentTranslator("en", "fr")

    assert isinstance(translator.agent._output_type, NativeOutput)


def test_translategemma_uses_plain_marker_output(settings):
    settings.WAGTAIL_TRANSLATE_LLM_MODEL = "ollama:translategemma:4b"
    translator = PydanticAIDocumentTranslator("en", "fr")
    run = translator._extract_document(
        BlogPostPage(title="Hello", intro="<p>Hello <em>world</em></p>", body=[])
    )

    response = translator._parse_plain_marker_response(
        "[[F0]]Bonjour[[/F0]]\n" "[[F1]][[E0]]Bonjour [[E1]]monde[[/E1]][[/E0]][[/F1]]",
        run,
    )

    assert translator.agent._output_type is str
    assert [fragment.text for fragment in response.fragments] == [
        "Bonjour",
        "[[E0]]Bonjour [[E1]]monde[[/E1]][[/E0]]",
    ]
