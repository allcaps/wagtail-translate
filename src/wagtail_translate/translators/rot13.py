import codecs

from wagtail_translate.translators.base import BaseTranslator


class ROT13Translator(BaseTranslator):
    def translate(self, source_string: str) -> str:
        """
        ROT13 is its own inverse. Because there are 26 letters (2×13) in the
        Latin alphabet, applying ROT13 to a piece of text twice will give the
        original text.

        ROT13Translator.translate is deterministic and therefore used in tests.

        Rot13 does not need the language codes, but a real translation service would.
        - self.source_language_code
        - self.target_language_code
        """
        return codecs.encode(source_string, "rot13")
