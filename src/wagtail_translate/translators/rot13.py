import codecs

from bs4 import BeautifulSoup, NavigableString

from .document import HTMLDocumentTranslator


class ROT13HTMLDocumentTranslator(HTMLDocumentTranslator):
    """Deterministic whole-document translator for tests and demonstrations."""

    def translate_document_html(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for text_node in list(soup.find_all(string=True)):
            if isinstance(text_node, NavigableString):
                text_node.replace_with(codecs.encode(str(text_node), "rot13"))

        for tag in soup.find_all(True):
            for attribute in self.translatable_html_attributes:
                if tag.get(attribute):
                    tag[attribute] = codecs.encode(str(tag[attribute]), "rot13")
        return str(soup)
