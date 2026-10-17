"""Tests for the Kokborok dictionary module."""

import pytest

from tripura_translate.dictionary import (
    KokborokDictionary,
    search_dictionary,
)
from tripura_translate.exceptions import (
    DictionaryEntryNotFoundError,
    EmptyInputError,
)


@pytest.fixture
def dictionary() -> KokborokDictionary:
    return KokborokDictionary()


class TestKokborokDictionary:
    def test_initialization_and_count(self, dictionary: KokborokDictionary):
        assert dictionary.total_entries > 30
        assert dictionary.count() == dictionary.total_entries

    def test_exact_search_kokborok(self, dictionary: KokborokDictionary):
        results = dictionary.search("twi", search_in="kokborok", exact=True)
        assert len(results) > 0
        assert results[0]["kokborok_latin"] == "twi"
        assert results[0]["english"] == "water"

    def test_exact_search_english(self, dictionary: KokborokDictionary):
        results = dictionary.search("water", search_in="english", exact=True)
        assert len(results) > 0
        assert results[0]["kokborok_latin"] == "twi"

    def test_partial_search(self, dictionary: KokborokDictionary):
        # "thank" should find "thank you"
        results = dictionary.search("thank", search_in="english", exact=False)
        assert len(results) > 0
        assert any(r["kokborok_latin"] == "hambai" for r in results)

    def test_bengali_script_search(self, dictionary: KokborokDictionary):
        results = dictionary.search("খুলুমখা", search_in="kokborok", exact=True)
        assert len(results) > 0
        assert results[0]["kokborok_latin"] == "khulumkha"
        assert results[0]["english"] == "hello"

    def test_get_categories(self, dictionary: KokborokDictionary):
        categories = dictionary.get_categories()
        assert "numbers" in categories
        assert "greetings" in categories
        assert "colors" in categories
        assert "nature" in categories

    def test_get_by_category_numbers(self, dictionary: KokborokDictionary):
        numbers = dictionary.get_by_category("numbers")
        assert len(numbers) >= 10
        # Verify 1 through 10 are present
        kb_words = [item["kokborok_latin"] for item in numbers]
        assert "sa" in kb_words  # 1
        assert "nwi" in kb_words  # 2
        assert "tham" in kb_words  # 3
        assert "chi" in kb_words  # 10

    def test_get_by_category_colors(self, dictionary: KokborokDictionary):
        colors = dictionary.get_by_category("colors")
        color_words = [item["kokborok_latin"] for item in colors]
        assert "kuphur" in color_words  # white
        assert "kosom" in color_words   # black
        assert "kwchak" in color_words  # red
        assert "kwkhrang" in color_words  # green

    def test_lookup_word_exact(self, dictionary: KokborokDictionary):
        entry = dictionary.lookup_word("hambai")
        assert entry is not None
        assert entry["english"] == "thank you"

    def test_lookup_word_morphological_fallback(self, dictionary: KokborokDictionary):
        # 'phaikha' (came) is an inflected form of 'phai' (come) with past suffix -kha
        entry = dictionary.lookup_word("phaikha")
        assert entry is not None
        assert entry["kokborok_latin"] == "phai"
        assert "morphology_note" in entry
        assert "kha" in entry["morphology_note"]

    def test_lookup_word_not_found(self, dictionary: KokborokDictionary):
        entry = dictionary.lookup_word("nonexistentword12345")
        assert entry is None

    def test_lookup_word_raise_on_not_found(self, dictionary: KokborokDictionary):
        with pytest.raises(DictionaryEntryNotFoundError):
            dictionary.lookup_word("nonexistentword12345", raise_on_not_found=True)

    def test_empty_query_raises_empty_input_error(self, dictionary: KokborokDictionary):
        with pytest.raises(EmptyInputError):
            dictionary.search("   ")

    def test_invalid_search_in_raises_value_error(self, dictionary: KokborokDictionary):
        with pytest.raises(ValueError, match="Invalid search_in option"):
            dictionary.search("water", search_in="invalid_target")

    def test_add_custom_entry(self, dictionary: KokborokDictionary):
        initial_count = dictionary.count()
        new_entry = {
            "kokborok_latin": "kormo_test",
            "english": "test word",
            "category": "test_category",
        }
        dictionary.add_entry(new_entry)
        assert dictionary.count() == initial_count + 1
        results = dictionary.search("kormo_test", exact=True)
        assert len(results) == 1
        assert "test_category" in dictionary.get_categories()


class TestSearchDictionaryHelper:
    def test_search_dictionary_function(self):
        results = search_dictionary("hello")
        assert len(results) > 0
        assert results[0]["kokborok_latin"] == "khulumkha"
