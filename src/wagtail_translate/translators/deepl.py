import os
import deepl

from .base import Translator

class DeepLTranslator(Translator):

    def __init__(self, source_language_code: str, target_language_code: str) -> None:
        self.auth_key = os.getenv("DEEPL_AUTH_KEY")
        super().__init__(source_language_code, target_language_code)

    def translate(self, source_string: str) -> str:
        """
        Translate, a function that does the actual translation.
        The translation service is provided by the DeepL service.
        """
        translator = deepl.Translator(self.auth_key)
        if source_string == "":
            return ""
        translation = translator.translate_text(source_string, source_lang = self.source_language_code, target_lang = self.target_language_code)
        return translation.text