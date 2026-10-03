from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import get_language_info

from .document import HTMLDocumentTranslator
from .exceptions import DocumentTranslationRequestError

try:
    from openai import OpenAI
except ImportError as exc:  # pragma: no cover - tested without the optional extra
    raise ImportError(
        "LLMHTMLDocumentTranslator requires the OpenAI dependency. "
        'Install it with `pip install "wagtail-translate[llm]"`.'
    ) from exc


class LLMHTMLDocumentTranslator(HTMLDocumentTranslator):
    """Translate HTML through an OpenAI-compatible Chat Completions endpoint."""

    def __init__(self, source_language_code: str, target_language_code: str) -> None:
        super().__init__(source_language_code, target_language_code)
        self.model = getattr(settings, "WAGTAIL_TRANSLATE_LLM_MODEL", "")
        if not self.model:
            raise ImproperlyConfigured(
                "Please set WAGTAIL_TRANSLATE_LLM_MODEL in your settings file."
            )

        self.base_url = getattr(
            settings,
            "WAGTAIL_TRANSLATE_LLM_BASE_URL",
            "http://localhost:11434/v1/",
        )
        self.api_key = getattr(settings, "WAGTAIL_TRANSLATE_LLM_API_KEY", "ollama")
        self.custom_instructions = getattr(
            settings, "WAGTAIL_TRANSLATE_LLM_INSTRUCTIONS", ""
        )
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    def _language_name(self, language_code: str) -> str:
        try:
            return get_language_info(language_code)["name"]
        except KeyError:
            return language_code

    def _prompt(self, html: str) -> str:
        source_name = self._language_name(self.source_language_code)
        target_name = self._language_name(self.target_language_code)
        custom = ""
        if self.custom_instructions:
            custom = f"\nProject translation guidance:\n{self.custom_instructions}\n"
        return f"""Translate this HTML document from {source_name} to {target_name}.

Translate all human-readable text and the values of alt, title, and aria-label attributes.
Preserve every HTML element, its nesting, attribute names, and id values.
Leave empty placeholder elements intact.

Consider the complete document when resolving meaning and ambiguity.
{custom}
Return only the translated HTML without Markdown fences or commentary.

{html}"""

    def translate_document_html(self, html: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": self._prompt(html)}],
            )
            translated_html = response.choices[0].message.content
        except Exception as exc:
            raise DocumentTranslationRequestError(
                f"The LLM document translation request failed: {exc}"
            ) from exc
        if not translated_html:
            raise DocumentTranslationRequestError(
                "The LLM document translation request returned no HTML."
            )
        return translated_html
