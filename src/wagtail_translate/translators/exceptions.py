class DocumentTranslationError(Exception):
    """Base error for whole-document translations."""


class DocumentTranslationRequestError(DocumentTranslationError):
    """The translation model request could not be completed."""


class DocumentTranslationValidationError(DocumentTranslationError):
    """The translation response could not be validated or rehydrated."""
