import copy
import importlib
import sys
import uuid
from types import SimpleNamespace

import pytest

from tests.testproject.demoapp.models import BlogPostPage
from wagtail_translate.translators.document import HTMLDocumentCodec
from wagtail_translate.translators.exceptions import (
    DocumentTranslationValidationError,
)
from wagtail_translate.translators.rot13 import ROT13HTMLDocumentTranslator

OPAQUE_TAGS = frozenset({"code", "math", "pre", "script", "style", "svg", "template"})
TEXT_ATTRIBUTES = frozenset({"alt", "title", "aria-label"})
pytestmark = pytest.mark.django_db


def make_codec():
    return HTMLDocumentCodec(
        opaque_html_tags=OPAQUE_TAGS,
        translatable_html_attributes=TEXT_ATTRIBUTES,
    )


def test_decompose_uses_semantic_field_and_nested_block_elements():
    source = BlogPostPage(
        title="The match",
        intro="<p>Light the candle.</p>",
        body=[
            ("heading", "Instructions"),
            ("list_nested", [["Strike the match", "Wait"]]),
        ],
    )

    document = make_codec().decompose(source)

    assert '<h1 id="f0">The match</h1>' in document.html
    assert '<div id="f1"><p>Light the candle.</p></div>' in document.html
    assert next(iter(document.fields.values())).field_name == "title"
    assert [binding.kind for binding in document.blocks.values()] == [
        "text",
        "text",
        "text",
        "container",
        "container",
    ]


def test_attributes_and_opaque_nodes_round_trip():
    source = BlogPostPage(
        title="Hello",
        intro=(
            '<p class="lede">Hello <a linktype="page" id="123" '
            'title="The link" aria-label="Open the page">world</a>'
            '<!--editor note--><code data-language="python">print("hello")</code>'
            '<embed embedtype="image" id="10" alt="" format="left"/></p>'
        ),
        body=[],
    )
    target = copy.copy(source)
    codec = make_codec()
    document = codec.decompose(source)

    assert 'class="lede"' not in document.html
    assert 'linktype="page"' not in document.html
    assert 'title="The link"' in document.html
    assert 'aria-label="Open the page"' in document.html
    assert "editor note" not in document.html
    assert 'print("hello")' not in document.html

    translated = (
        document.html.replace("Hello", "Bonjour")
        .replace("The link", "Le lien")
        .replace("Open the page", "Ouvrir la page")
        .replace("world", "monde")
    )
    codec.rehydrate(document, translated, source, target, lambda value: value)

    assert '<p class="lede">' in target.intro
    assert 'linktype="page"' in target.intro
    assert 'id="123"' in target.intro
    assert 'title="Le lien"' in target.intro
    assert 'aria-label="Ouvrir la page"' in target.intro
    assert "<!--editor note-->" in target.intro
    assert '<code data-language="python">print("hello")</code>' in target.intro
    assert '<embed alt="" embedtype="image" format="left" id="10"/>' in target.intro


def test_rot13_translates_one_document_without_mutating_source():
    source = BlogPostPage(
        title="Hello",
        intro='<p title="Greeting">Hello <em>world</em></p>',
        body=[("heading", "Introduction")],
    )
    target = copy.copy(source)

    result = ROT13HTMLDocumentTranslator("en", "fr").translate_obj(source, target)

    assert result is target
    assert target.title == "Uryyb"
    assert target.intro == '<p title="Terrgvat">Uryyb <em>jbeyq</em></p>'
    assert target.body[0].value == "Vagebqhpgvba"
    assert source.title == "Hello"
    assert source.intro == '<p title="Greeting">Hello <em>world</em></p>'


@pytest.mark.parametrize(
    "change, message",
    [
        (lambda html: html.replace('id="f0"', 'id="other"'), "Missing"),
        (lambda html: html.replace("<h1", "<h2").replace("</h1>", "</h2>"), "tag"),
        (lambda html: html.replace("</h1>", "<strong>new</strong></h1>"), "structure"),
    ],
)
def test_validation_rejects_reference_and_structure_changes(change, message):
    document = make_codec().decompose(BlogPostPage(title="Hello", intro="", body=[]))

    with pytest.raises(DocumentTranslationValidationError, match=message):
        make_codec().validate(document, change(document.html))


@pytest.mark.parametrize(
    "wrap",
    [
        pytest.param(lambda html: f"```html\n{html}\n```", id="markdown-fence"),
        pytest.param(
            lambda html: f"<html><body>{html}</body></html>", id="document-wrapper"
        ),
        pytest.param(
            lambda html: f"Translation:\n{html}\n<script>ignored()</script>",
            id="surrounding-content",
        ),
    ],
)
def test_validation_tolerates_content_around_single_main(wrap):
    source = BlogPostPage(title="Hello", intro="", body=[])
    target = copy.copy(source)
    codec = make_codec()
    document = codec.decompose(source)
    translated = wrap(document.html.replace("Hello", "Bonjour"))

    codec.rehydrate(document, translated, source, target, lambda value: value)

    assert target.title == "Bonjour"


@pytest.mark.parametrize(
    "translate",
    [
        pytest.param(lambda html: "No translated HTML", id="missing"),
        pytest.param(lambda html: html + html, id="multiple"),
    ],
)
def test_validation_requires_exactly_one_main(translate):
    codec = make_codec()
    document = codec.decompose(BlogPostPage(title="Hello", intro="", body=[]))

    with pytest.raises(
        DocumentTranslationValidationError,
        match="must contain exactly one main element",
    ):
        codec.validate(document, translate(document.html))


def test_nested_streamfield_paths_rehydrate_independently():
    source = BlogPostPage(
        title="Hello",
        intro="",
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
                        ],
                        "id": str(uuid.uuid4()),
                    }
                ],
                "id": str(uuid.uuid4()),
            }
        ],
    )
    target = copy.copy(source)
    translator = ROT13HTMLDocumentTranslator("en", "fr")

    translator.translate_obj(source, target)

    nested = target.body[0].value[0].value
    assert [child.value for child in nested] == ["Bar", "Gjb"]


def test_empty_document_skips_provider_call():
    class FailingTranslator(ROT13HTMLDocumentTranslator):
        def translate_document_html(self, html):
            raise AssertionError("provider should not be called")

    source = BlogPostPage(title="", intro="", body=[])
    target = copy.copy(source)

    FailingTranslator("en", "fr").translate_obj(source, target)


def test_validation_failure_does_not_mutate_target():
    class InvalidTranslator(ROT13HTMLDocumentTranslator):
        def translate_document_html(self, html):
            return html.replace('id="f0"', 'id="changed"')

    source = BlogPostPage(title="Hello", intro="<p>Introduction</p>", body=[])
    target = copy.copy(source)
    target.title = "Existing title"
    target.intro = "<p>Existing introduction</p>"

    with pytest.raises(DocumentTranslationValidationError):
        InvalidTranslator("en", "fr").translate_obj(source, target)

    assert target.title == "Existing title"
    assert target.intro == "<p>Existing introduction</p>"


def test_deepl_translator_sends_one_html_request(settings, monkeypatch):
    calls = []

    class FakeClient:
        def __init__(self, auth_key):
            assert auth_key == "secret"

        def translate_text(self, html, **kwargs):
            calls.append((html, kwargs))
            return SimpleNamespace(text=html.replace("Hello", "Bonjour"))

    fake_deepl = SimpleNamespace(Translator=FakeClient)
    monkeypatch.setitem(sys.modules, "deepl", fake_deepl)
    sys.modules.pop("wagtail_translate.translators.deepl", None)
    deepl_module = importlib.import_module("wagtail_translate.translators.deepl")
    settings.WAGTAIL_TRANSLATE_DEEPL_KEY = "secret"
    translator = deepl_module.DeepLHTMLDocumentTranslator("en", "fr")

    translated = translator.translate_document_html("<main><p>Hello</p></main>")

    assert translated == "<main><p>Bonjour</p></main>"
    assert calls == [
        (
            "<main><p>Hello</p></main>",
            {
                "source_lang": "en",
                "target_lang": "fr",
                "tag_handling": "html",
                "tag_handling_version": "v2",
            },
        )
    ]


def test_llm_translator_uses_openai_compatible_ollama_defaults(settings, monkeypatch):
    requests = []

    class FakeCompletions:
        def create(self, **kwargs):
            requests.append(kwargs)
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content='<main><h1 id="f0">Bonjour</h1></main>'
                        )
                    )
                ]
            )

    class FakeOpenAI:
        def __init__(self, **kwargs):
            assert kwargs == {
                "base_url": "http://localhost:11434/v1/",
                "api_key": "ollama",
            }
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FakeOpenAI))
    sys.modules.pop("wagtail_translate.translators.openai_compatible", None)
    llm_module = importlib.import_module(
        "wagtail_translate.translators.openai_compatible"
    )
    settings.WAGTAIL_TRANSLATE_LLM_MODEL = "translategemma:4b"
    translator = llm_module.LLMHTMLDocumentTranslator("en", "fr")

    translated = translator.translate_document_html(
        '<main><h1 id="f0">Hello</h1></main>'
    )

    assert translated == '<main><h1 id="f0">Bonjour</h1></main>'
    assert requests[0]["model"] == "translategemma:4b"
    assert (
        '<main><h1 id="f0">Hello</h1></main>' in requests[0]["messages"][0]["content"]
    )
    assert "alt, title, and aria-label" in requests[0]["messages"][0]["content"]
    assert "Preserve every HTML element" in requests[0]["messages"][0]["content"]
    assert (
        "Leave empty placeholder elements intact"
        in requests[0]["messages"][0]["content"]
    )
