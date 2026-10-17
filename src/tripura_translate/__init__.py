"""tripura-translate: A Python library for Kokborok (Tripuri) language processing,
dictionary search, and translation interfaces.
"""

from tripura_translate.dictionary import (
    KokborokDictionary,
    get_default_dictionary,
    search_dictionary,
)
from tripura_translate.exceptions import (
    DependencyMissingError,
    DictionaryEntryNotFoundError,
    EmptyInputError,
    InvalidLanguageError,
    ModelNotFoundError,
    TranslationModelError,
    TranslationNotAvailableError,
    TripuraTranslateError,
    UnsupportedDirectionError,
)
from tripura_translate.text_processing import (
    analyze_word_structure,
    clean_text,
    detect_script,
    format_kokborok_text,
    process_text,
    remove_tone_markers,
    tokenize_kokborok,
    validate_text,
)
from tripura_translate.translator import (
    BaseTranslator,
    HuggingFaceTranslator,
    TranslationResult,
    Translator,
    VerifiedPhraseTranslator,
    get_default_translator,
    normalize_lang_code,
    translate,
)

__version__ = "0.1.0"
__author__ = "Tripura Translate Contributors"
__license__ = "MIT"

__all__ = [
    # Top-level functions
    "process_text",
    "clean_text",
    "detect_script",
    "validate_text",
    "tokenize_kokborok",
    "analyze_word_structure",
    "remove_tone_markers",
    "format_kokborok_text",
    "search_dictionary",
    "translate",
    "normalize_lang_code",
    # Classes
    "KokborokDictionary",
    "Translator",
    "VerifiedPhraseTranslator",
    "HuggingFaceTranslator",
    "BaseTranslator",
    "TranslationResult",
    "get_default_dictionary",
    "get_default_translator",
    # Exceptions
    "TripuraTranslateError",
    "EmptyInputError",
    "InvalidLanguageError",
    "UnsupportedDirectionError",
    "DictionaryEntryNotFoundError",
    "TranslationModelError",
    "ModelNotFoundError",
    "DependencyMissingError",
    "TranslationNotAvailableError",
    # Metadata
    "__version__",
]
