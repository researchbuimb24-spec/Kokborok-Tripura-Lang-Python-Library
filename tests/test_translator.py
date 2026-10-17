"""Tests for the translation module of tripura-translate."""

import pytest

from tripura_translate.exceptions import (
    DependencyMissingError,
    EmptyInputError,
    InvalidLanguageError,
    TranslationNotAvailableError,
    UnsupportedDirectionError,
)
from tripura_translate.translator import (
    BaseTranslator,
    HuggingFaceTranslator,
    TranslationResult,
    Translator,
    VerifiedPhraseTranslator,
    normalize_lang_code,
    translate,
)


class TestLanguageCodeNormalization:
    def test_valid_english_codes(self):
        for code in ("en", "eng", "english", "eng_Latn", "ENG"):
            assert normalize_lang_code(code) == "eng"

    def test_valid_kokborok_codes(self):
        for code in ("trp", "kok", "kokborok", "tripuri", "trp_Latn", "TRP"):
            assert normalize_lang_code(code) == "trp"

    def test_empty_code_raises_empty_input_error(self):
        with pytest.raises(EmptyInputError):
            normalize_lang_code("")

    def test_invalid_code_raises_invalid_language_error(self):
        with pytest.raises(InvalidLanguageError, match="Unsupported or unrecognized"):
            normalize_lang_code("french")
        with pytest.raises(InvalidLanguageError):
            normalize_lang_code("hi")


class TestVerifiedPhraseTranslator:
    @pytest.fixture
    def phrase_translator(self) -> VerifiedPhraseTranslator:
        return VerifiedPhraseTranslator()

    def test_english_to_kokborok(self, phrase_translator: VerifiedPhraseTranslator):
        result = phrase_translator.translate("Good morning", "en", "trp")
        assert isinstance(result, TranslationResult)
        assert result.translated_text == "Phung kaham"
        assert result.confidence == 1.0
        assert result.backend == "verified_phrase"
        assert result.source_lang == "eng"
        assert result.target_lang == "trp"

    def test_kokborok_to_english(self, phrase_translator: VerifiedPhraseTranslator):
        result = phrase_translator.translate("Hambai", "trp", "en")
        assert result.translated_text == "Thank you"
        assert result.confidence == 1.0
        assert result.source_lang == "trp"
        assert result.target_lang == "eng"

    def test_case_and_punctuation_tolerance(self, phrase_translator: VerifiedPhraseTranslator):
        result1 = phrase_translator.translate("good morning!", "en", "trp")
        assert result1.translated_text == "Phung kaham"

        result2 = phrase_translator.translate("nwng bahai tong", "trp", "en")
        assert result2.translated_text == "How are you?"

    def test_unsupported_same_direction(self, phrase_translator: VerifiedPhraseTranslator):
        with pytest.raises(UnsupportedDirectionError):
            phrase_translator.translate("Hello", "en", "en")

    def test_unverified_sentence_raises_translation_not_available(
        self, phrase_translator: VerifiedPhraseTranslator
    ):
        with pytest.raises(TranslationNotAvailableError, match="Translation not available"):
            phrase_translator.translate(
                "Artificial intelligence transforms modern medicine across borders.",
                "en",
                "trp",
            )


class TestTranslatorComposite:
    def test_default_phrase_backend(self):
        t = Translator()
        result = t.translate("Thank you", "en", "trp")
        assert result.translated_text == "Hambai"

    def test_unknown_backend_raises_value_error(self):
        t = Translator()
        with pytest.raises(ValueError, match="Unknown translation backend"):
            t.translate("Hello", "en", "trp", backend="nonexistent_backend")

    def test_custom_backend(self):
        class DummyTranslator(BaseTranslator):
            def translate(self, text, source_lang, target_lang):
                return TranslationResult(
                    source_text=text,
                    translated_text=f"CUSTOM_{text}",
                    source_lang=source_lang,
                    target_lang=target_lang,
                    backend="custom_test",
                    confidence=0.99,
                )

        t = Translator(custom_translator=DummyTranslator())
        res = t.translate("test", "en", "trp", backend="custom")
        assert res.translated_text == "CUSTOM_test"
        assert res.backend == "custom_test"

    def test_huggingface_backend_missing_dependency(self, monkeypatch):
        # Ensure that if transformers is not installed or import fails, DependencyMissingError is raised
        import sys

        monkeypatch.setitem(sys.modules, "transformers", None)
        with pytest.raises(DependencyMissingError, match="Optional dependency"):
            HuggingFaceTranslator()


class TestTranslateHelperFunction:
    def test_translate_convenience_function(self):
        result = translate("What is your name?", source_lang="en", target_lang="trp")
        assert result.translated_text == "Nini mung tamo?"
        # Test __str__ on TranslationResult
        assert str(result) == "Nini mung tamo?"

    def test_translate_reverse(self):
        result = translate("Nini mung tamo?", source_lang="trp", target_lang="en")
        assert result.translated_text == "What is your name?"

    def test_translate_empty_text_raises_empty_input_error(self):
        with pytest.raises(EmptyInputError):
            translate("", "en", "trp")
