"""Custom exceptions for the tripura_translate library.

This module defines descriptive, structured exceptions used across the
tripura-translate package. Catching `TripuraTranslateError` allows client
code to catch all errors raised by this library.
"""

from typing import Optional, Sequence


class TripuraTranslateError(Exception):
    """Base exception for all errors raised by tripura-translate."""

    def __init__(self, message: str, details: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} ({self.details})"
        return self.message


class EmptyInputError(TripuraTranslateError):
    """Raised when text input is empty, None, or only whitespace."""

    def __init__(self, field_name: str = "text") -> None:
        super().__init__(
            message=f"Input '{field_name}' cannot be empty or contain only whitespace.",
            details="Please provide non-empty string input.",
        )
        self.field_name = field_name


class InvalidLanguageError(TripuraTranslateError):
    """Raised when an invalid or unsupported language code is provided."""

    def __init__(
        self,
        language_code: str,
        supported_codes: Optional[Sequence[str]] = None,
    ) -> None:
        msg = f"Unsupported or unrecognized language code: '{language_code}'."
        if supported_codes:
            details = f"Supported codes: {', '.join(supported_codes)}"
        else:
            details = "Supported codes are typically 'en' (English) and 'trp' (Kokborok)."
        super().__init__(message=msg, details=details)
        self.language_code = language_code
        self.supported_codes = supported_codes or []


class UnsupportedDirectionError(TripuraTranslateError):
    """Raised when a translation direction between two languages is not supported."""

    def __init__(self, source_lang: str, target_lang: str) -> None:
        super().__init__(
            message=f"Translation direction from '{source_lang}' to '{target_lang}' is not supported.",
            details="Supported directions are English -> Kokborok and Kokborok -> English.",
        )
        self.source_lang = source_lang
        self.target_lang = target_lang


class DictionaryEntryNotFoundError(TripuraTranslateError):
    """Raised when an exact dictionary lookup produces no results."""

    def __init__(self, query: str, suggestions: Optional[Sequence[str]] = None) -> None:
        msg = f"No dictionary entry found for '{query}'."
        details = None
        if suggestions:
            details = f"Did you mean: {', '.join(suggestions)}?"
        super().__init__(message=msg, details=details)
        self.query = query
        self.suggestions = suggestions or []


class TranslationModelError(TripuraTranslateError):
    """Base exception for translation model operations."""


class ModelNotFoundError(TranslationModelError):
    """Raised when a requested external translation model or checkpoint cannot be found."""

    def __init__(self, model_name: str, hint: Optional[str] = None) -> None:
        super().__init__(
            message=f"Translation model '{model_name}' could not be loaded or was not found.",
            details=hint or "Verify the model path or repository identifier.",
        )
        self.model_name = model_name


class DependencyMissingError(TripuraTranslateError):
    """Raised when an optional third-party dependency is required but not installed."""

    def __init__(self, dependency_name: str, install_command: str) -> None:
        super().__init__(
            message=f"Optional dependency '{dependency_name}' is required for this feature but not installed.",
            details=f"Install it with: {install_command}",
        )
        self.dependency_name = dependency_name
        self.install_command = install_command


class TranslationNotAvailableError(TranslationModelError):
    """Raised when an input sentence cannot be translated by verified resources.

    This error is intentionally raised to prevent hallucinating Kokborok translations
    or misrepresenting dictionary word lookups as grammatical sentence translation.
    """

    def __init__(self, text: str, reason: Optional[str] = None) -> None:
        super().__init__(
            message=f"Translation not available for sentence: '{text}'.",
            details=reason
            or (
                "No verified phrase match was found, and no verified neural translation "
                "model is loaded. The library refuses to invent unverified translations or "
                "stitch ungrammatical word-by-word dictionary lookups."
            ),
        )
        self.text = text


class LiteratureNotFoundError(TripuraTranslateError):
    """Raised when a requested literature item or search query is not found."""

    def __init__(self, identifier: str, suggestions: Optional[Sequence[str]] = None) -> None:
        msg = f"Literature item not found for '{identifier}'."
        details = None
        if suggestions:
            details = f"Available or suggested items: {', '.join(suggestions)}"
        super().__init__(message=msg, details=details)
        self.identifier = identifier
        self.suggestions = suggestions or []


class FolkSongNotFoundError(TripuraTranslateError):
    """Raised when a requested folk song entry is not found in the catalog."""

    def __init__(self, identifier: str, suggestions: Optional[Sequence[str]] = None) -> None:
        msg = f"Folk song not found for '{identifier}'."
        details = None
        if suggestions:
            details = f"Did you mean: {', '.join(suggestions)}?"
        super().__init__(message=msg, details=details)
        self.identifier = identifier
        self.suggestions = suggestions or []


class LanguageBasicsError(TripuraTranslateError):
    """Base exception for errors originating in the language basics module."""


class GrammarTopicNotFoundError(LanguageBasicsError):
    """Raised when a requested grammar topic is not found."""

    def __init__(self, topic: str, available_topics: Optional[Sequence[str]] = None) -> None:
        msg = f"Grammar topic '{topic}' was not found."
        details = None
        if available_topics:
            details = f"Available topics: {', '.join(available_topics)}"
        super().__init__(message=msg, details=details)
        self.topic = topic
        self.available_topics = list(available_topics) if available_topics else []


