from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .document import HTMLDocumentTranslator
from .exceptions import DocumentTranslationRequestError

try:
    import deepl
except ImportError as exc:  # pragma: no cover - tested without the optional extra
    raise ImportError(
        "DeepLHTMLDocumentTranslator requires the DeepL dependency. "
        'Install it with `pip install "wagtail-translate[deepl]"`.'
    ) from exc


class DeepLHTMLDocumentTranslator(HTMLDocumentTranslator):
    """DeepLHTMLDocumentTranslator

    Guarantees the HTML structure, but does not translate attributes (title, alt, aria-label)"""

    def __init__(self, source_language_code: str, target_language_code: str) -> None:
        self.auth_key = getattr(settings, "WAGTAIL_TRANSLATE_DEEPL_KEY", "")
        if not self.auth_key:
            raise ImproperlyConfigured(
                "Please set WAGTAIL_TRANSLATE_DEEPL_KEY in your settings file."
            )
        super().__init__(source_language_code, target_language_code)

    def translate_document_html(self, html: str) -> str:
        try:
            translation = deepl.Translator(self.auth_key).translate_text(
                html,
                source_lang=self.source_language_code,
                target_lang=self.target_language_code,
                tag_handling="html",
                tag_handling_version="v2",
            )
        except Exception as exc:
            raise DocumentTranslationRequestError(
                f"The DeepL document translation request failed: {exc}"
            ) from exc
        return translation.text
