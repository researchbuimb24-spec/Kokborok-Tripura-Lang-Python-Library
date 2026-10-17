import pytest

import tripura_translate
from tripura_translate import (
    KokborokDictionary,
    KokborokLiterature,
    LiteratureItem,
    TranslationResult,
    Translator,
    clean_text,
    detect_script,
    get_literature,
    list_literature,
    process_text,
    search_dictionary,
    search_literature,
    tokenize_kokborok,
    translate,
)
from tripura_translate.exceptions import (
    EmptyInputError,
    InvalidLanguageError,
    LiteratureNotFoundError,
    TripuraTranslateError,
)


def test_package_metadata():
    assert tripura_translate.__version__ == "0.1.0"
    assert "process_text" in tripura_translate.__all__
    assert "search_dictionary" in tripura_translate.__all__
    assert "translate" in tripura_translate.__all__
    assert "search_literature" in tripura_translate.__all__
    assert "list_literature" in tripura_translate.__all__
    assert "get_literature" in tripura_translate.__all__
    assert "KokborokLiterature" in tripura_translate.__all__
    assert "LiteratureItem" in tripura_translate.__all__


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

    # 5. Literature search and retrieval
    lit_results = search_literature("Chethuang")
    assert len(lit_results) > 0
    chethuang = lit_results[0]
    assert isinstance(chethuang, LiteratureItem)
    assert chethuang.category == "folklore"
    assert chethuang.has_full_text is True

    retrieved = get_literature("chethuang-kothoma")
    assert retrieved.id == chethuang.id


def test_exception_hierarchy():
    # Confirm that all library exceptions derive from TripuraTranslateError
    assert issubclass(EmptyInputError, TripuraTranslateError)
    assert issubclass(InvalidLanguageError, TripuraTranslateError)
    assert issubclass(LiteratureNotFoundError, TripuraTranslateError)

