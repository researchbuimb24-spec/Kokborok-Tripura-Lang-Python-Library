"""Integration tests for the public API of tripura_translate."""

import pytest

import tripura_translate
from tripura_translate import (
    KokborokDictionary,
    TranslationResult,
    Translator,
    clean_text,
    detect_script,
    process_text,
    search_dictionary,
    tokenize_kokborok,
    translate,
)
from tripura_translate.exceptions import (
    EmptyInputError,
    InvalidLanguageError,
    TripuraTranslateError,
)


def test_package_metadata():
    assert tripura_translate.__version__ == "0.1.0"
    assert "process_text" in tripura_translate.__all__
    assert "search_dictionary" in tripura_translate.__all__
    assert "translate" in tripura_translate.__all__


def test_end_to_end_workflow():
    # 1. Text processing
    raw_kokborok = "  khulumkha ,  nwng bahai tong ? "
    processed = process_text(raw_kokborok)
    assert processed["script"] == "latin"
    assert processed["word_count"] == 4
    assert processed["tokens"] == ["khulumkha", "nwng", "bahai", "tong"]

    # 2. Dictionary search
    dict_results = search_dictionary("water", exact=True)
    assert len(dict_results) > 0
    assert dict_results[0]["kokborok_latin"] == "twi"

    # 3. Verified translation
    trans_result = translate("Good morning", "en", "trp")
    assert isinstance(trans_result, TranslationResult)
    assert trans_result.translated_text == "Phung kaham"

    # 4. Reverse translation
    reverse_result = translate("Phung kaham", "trp", "en")
    assert reverse_result.translated_text == "Good morning"


def test_exception_hierarchy():
    # Confirm that all library exceptions derive from TripuraTranslateError
    assert issubclass(EmptyInputError, TripuraTranslateError)
    assert issubclass(InvalidLanguageError, TripuraTranslateError)
