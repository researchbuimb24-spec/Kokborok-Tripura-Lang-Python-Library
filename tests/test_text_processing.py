"""Tests for the text processing module of tripura-translate."""

import pytest

from tripura_translate.exceptions import EmptyInputError
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


class TestCleanText:
    def test_unicode_nfc_normalization(self):
        # Combining character vs composed
        decomposed = "e\u0301"  # e with acute
        composed = "\u00e9"
        assert clean_text(decomposed) == clean_text(composed)

    def test_invisible_and_special_spaces(self):
        raw = "\ufeff  Khulumkha \u200b  nwng \u00a0 bahai tong?  \u200e"
        cleaned = clean_text(raw)
        assert cleaned == "Khulumkha nwng bahai tong?"

    def test_whitespace_collapsing(self):
        raw = "Ang    khamno \n\t  tong  "
        assert clean_text(raw) == "Ang khamno tong"

    def test_non_string_input_raises_type_error(self):
        with pytest.raises(TypeError, match="Expected a string"):
            clean_text(12345)  # type: ignore


class TestScriptDetection:
    def test_latin_script(self):
        assert detect_script("Khulumkha") == "latin"
        assert detect_script("Nwng bahai tong?") == "latin"

    def test_bengali_script(self):
        assert detect_script("খুলুমখা") == "bengali"
        assert detect_script("হাম্বাই") == "bengali"

    def test_mixed_script(self):
        assert detect_script("Khulumkha খুলুমখা") == "mixed"

    def test_unknown_script(self):
        assert detect_script("12345 !@#$%") == "unknown"
        assert detect_script("") == "unknown"


class TestValidateText:
    def test_valid_string(self):
        assert validate_text(" Hambai ") == "Hambai"

    def test_empty_string_raises_empty_input_error(self):
        with pytest.raises(EmptyInputError):
            validate_text("")

    def test_whitespace_only_raises_empty_input_error(self):
        with pytest.raises(EmptyInputError):
            validate_text("   \n\t   ")

    def test_allow_empty_flag(self):
        assert validate_text("   ", allow_empty=True) == ""

    def test_expected_script_matches(self):
        assert validate_text("Khulumkha", expected_script="latin") == "Khulumkha"

    def test_expected_script_mismatch_raises_value_error(self):
        with pytest.raises(ValueError, match="Expected script 'bengali'"):
            validate_text("Khulumkha", expected_script="bengali")


class TestTokenizeKokborok:
    def test_preserves_hyphenated_compounds(self):
        text = "Obo sal-kwtal, phung-kaham!"
        tokens = tokenize_kokborok(text, keep_hyphens=True)
        assert tokens == ["Obo", "sal-kwtal", "phung-kaham"]

    def test_splits_hyphens_when_disabled(self):
        text = "Kok-borok"
        tokens = tokenize_kokborok(text, keep_hyphens=False)
        assert tokens == ["Kok", "borok"]

    def test_strips_punctuation(self):
        text = "Khulumkha, nwng bahai tong?"
        tokens = tokenize_kokborok(text)
        assert tokens == ["Khulumkha", "nwng", "bahai", "tong"]

    def test_empty_text(self):
        assert tokenize_kokborok("") == []


class TestAnalyzeWordStructure:
    def test_analyzes_vowel_w(self):
        result = analyze_word_structure("nwng")
        assert result["has_kokborok_vowel_w"] is True
        assert result["script"] == "latin"

    def test_analyzes_tone_marker_h(self):
        result = analyze_word_structure("kaham")
        assert result["has_tone_marker_h"] is True

    def test_analyzes_prefix_bu(self):
        result = analyze_word_structure("buphang")
        assert result["detected_prefix"] == "bu"
        assert result["stem_candidate"] == "phang"

    def test_analyzes_suffix_di(self):
        result = analyze_word_structure("phaidi")
        assert result["detected_suffix"] == "di"
        assert result["suffix_function"] == "imperative"
        assert result["stem_candidate"] == "phai"

    def test_analyzes_suffix_rok(self):
        result = analyze_word_structure("borok-rok")
        assert result["detected_suffix"] == "rok"
        assert result["suffix_function"] == "plural"
        assert result["stem_candidate"] == "borok"


class TestRemoveToneMarkers:
    def test_removes_postvocalic_h(self):
        assert remove_tone_markers("kaham") == "kaam"
        assert remove_tone_markers("chah") == "cha"
        # Aspirated consonant 'ph' is preserved since 'h' follows a consonant
        assert remove_tone_markers("buphang") == "buphang"


class TestFormatKokborokText:
    def test_formats_spacing_and_capitalization(self):
        raw = "khulumkha ,  nwng bahai tong ? ang kahamno  ."
        formatted = format_kokborok_text(raw, capitalize_sentences=True)
        assert formatted == "Khulumkha, nwng bahai tong? Ang kahamno."


class TestProcessText:
    def test_process_text_returns_expected_structure(self):
        result = process_text("Khulumkha, nwng bahai tong?")
        assert result["cleaned_text"] == "Khulumkha, nwng bahai tong?"
        assert result["script"] == "latin"
        assert result["word_count"] == 4
        assert result["tokens"] == ["Khulumkha", "nwng", "bahai", "tong"]
        assert len(result["word_analysis"]) == 4
