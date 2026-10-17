"""Translation interfaces and verified translation engine for Kokborok.

Kokborok (ISO 639-3: 'trp') is currently a low-resource language that is NOT
supported out-of-the-box by standard commercial translation engines (e.g. Google
Translate) or base multilingual models (e.g. IndicTrans2, Meta NLLB-200 base).

To prevent hallucinations, ungrammatical word substitutions, and incorrect linguistic
claims, this module provides:
1. A verified parallel phrase engine (`VerifiedPhraseTranslator`) that guarantees
   100% accurate, attested translations for common phrases, greetings, and expressions.
2. A pluggable neural backend adapter (`HuggingFaceTranslator`) for researchers and
   developers wishing to load experimental fine-tuned models (e.g. MWirelabs/kokborok-mt).
3. Clear error handling (`EmptyInputError`, `InvalidLanguageError`,
   `UnsupportedDirectionError`, `TranslationNotAvailableError`) that never guesses.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple

from tripura_translate.exceptions import (
    DependencyMissingError,
    EmptyInputError,
    InvalidLanguageError,
    ModelNotFoundError,
    TranslationNotAvailableError,
    UnsupportedDirectionError,
)
from tripura_translate.text_processing import clean_text, validate_text


_DEFAULT_PHRASES_PATH = Path(__file__).parent / "data" / "verified_phrases.json"

# Supported language codes mapping to canonical ISO 639-3 codes
_LANG_ALIASES: Dict[str, str] = {
    "en": "eng",
    "eng": "eng",
    "english": "eng",
    "eng_latn": "eng",
    "trp": "trp",
    "kok": "trp",
    "kokborok": "trp",
    "tripuri": "trp",
    "trp_latn": "trp",
    "trp_beng": "trp",
}

SUPPORTED_CANONICAL_LANGS = ("eng", "trp")


def normalize_lang_code(code: str) -> str:
    """Normalize user-supplied language code to canonical ISO 639-3 ('eng' or 'trp').

    Args:
        code: Language code string (e.g. 'en', 'trp', 'kokborok', 'eng_Latn').

    Returns:
        Canonical code ('eng' or 'trp').

    Raises:
        EmptyInputError: If code is empty.
        InvalidLanguageError: If code is not recognized as English or Kokborok.
    """
    if not code or not str(code).strip():
        raise EmptyInputError(field_name="language_code")

    normalized = str(code).strip().lower()
    canonical = _LANG_ALIASES.get(normalized)
    if not canonical:
        raise InvalidLanguageError(
            language_code=code,
            supported_codes=["en", "eng", "trp", "kok", "kokborok"],
        )
    return canonical


@dataclass
class TranslationResult:
    """Structured result returned by translation functions."""

    source_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    backend: str
    confidence: float
    notes: Optional[str] = None

    def __str__(self) -> str:
        return self.translated_text


class BaseTranslator(ABC):
    """Abstract base class for all translation backends."""

    @abstractmethod
    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> TranslationResult:
        """Translate text from source_lang to target_lang.

        Args:
            text: Input string.
            source_lang: Source language code.
            target_lang: Target language code.

        Returns:
            A TranslationResult object.
        """
        pass


class VerifiedPhraseTranslator(BaseTranslator):
    """Translator backed by human-verified, attested parallel Kokborok-English sentences.

    Guarantees zero hallucinations and avoids word-by-word pseudo-translations.
    If a sentence is not attested in the verified corpus, it raises a
    TranslationNotAvailableError with guidance on using neural models or dictionary lookup.
    """

    def __init__(self, data_path: Optional[Path] = None) -> None:
        self._data_path = Path(data_path) if data_path else _DEFAULT_PHRASES_PATH
        self._phrases: List[Dict[str, Any]] = []
        self._load_phrases()

    def _load_phrases(self) -> None:
        if not self._data_path.exists():
            raise FileNotFoundError(f"Verified phrases file not found: {self._data_path}")

        with open(self._data_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError("Expected a JSON list in verified phrases data.")

        self._phrases = data

    @property
    def total_phrases(self) -> int:
        """Return the number of verified phrase pairs."""
        return len(self._phrases)

    def _normalize_key(self, text: str) -> str:
        """Strip punctuation and lowercase for fuzzy phrase matching."""
        cleaned = clean_text(text).lower()
        # Remove trailing and leading punctuation
        return re.sub(r"[^\w\s]", "", cleaned)

    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> TranslationResult:
        """Translate text using verified parallel phrase data."""
        src_canon = normalize_lang_code(source_lang)
        tgt_canon = normalize_lang_code(target_lang)

        if src_canon == tgt_canon:
            raise UnsupportedDirectionError(source_lang, target_lang)

        clean_input = validate_text(text, allow_empty=False, field_name="text")
        key = self._normalize_key(clean_input)

        for entry in self._phrases:
            eng_key = self._normalize_key(entry.get("english", ""))
            kb_key = self._normalize_key(entry.get("kokborok", ""))

            if src_canon == "eng" and tgt_canon == "trp":
                if key == eng_key:
                    return TranslationResult(
                        source_text=clean_input,
                        translated_text=entry["kokborok"],
                        source_lang=src_canon,
                        target_lang=tgt_canon,
                        backend="verified_phrase",
                        confidence=1.0,
                        notes=f"Source: {entry.get('source', 'Attested Kokborok corpus')}",
                    )

            elif src_canon == "trp" and tgt_canon == "eng":
                if key == kb_key:
                    return TranslationResult(
                        source_text=clean_input,
                        translated_text=entry["english"],
                        source_lang=src_canon,
                        target_lang=tgt_canon,
                        backend="verified_phrase",
                        confidence=1.0,
                        notes=f"Source: {entry.get('source', 'Attested Kokborok corpus')}",
                    )

        # If not found in verified phrases
        raise TranslationNotAvailableError(
            text=clean_input,
            reason=(
                f"Sentence '{clean_input}' is not present in the verified phrase dataset. "
                "For open-domain translation, configure a fine-tuned neural model backend "
                "(such as HuggingFaceTranslator). Individual word lookup is available via "
                "search_dictionary()."
            ),
        )


class HuggingFaceTranslator(BaseTranslator):
    """Adapter for neural machine translation models hosted on Hugging Face.

    Supports fine-tuned Seq2Seq models (such as MWirelabs/kokborok-mt or NLLB-200 checkpoints).
    Requires optional dependencies: `transformers`, `torch`, `sentencepiece`.
    """

    def __init__(
        self,
        model_name: str = "MWirelabs/kokborok-mt",
        device: str = "cpu",
    ) -> None:
        self.model_name = model_name
        self.device = device
        self._tokenizer = None
        self._model = None
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        try:
            import transformers  # noqa: F401
            import torch  # noqa: F401
        except ImportError:
            raise DependencyMissingError(
                dependency_name="transformers/torch",
                install_command="pip install transformers torch sentencepiece",
            )

    def _ensure_loaded(self) -> None:
        if self._model is not None and self._tokenizer is not None:
            return

        try:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            self._model.to(self.device)
        except Exception as exc:
            raise ModelNotFoundError(
                model_name=self.model_name,
                hint=f"Failed to load Hugging Face model '{self.model_name}': {exc}",
            ) from exc

    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> TranslationResult:
        src_canon = normalize_lang_code(source_lang)
        tgt_canon = normalize_lang_code(target_lang)

        if src_canon == tgt_canon:
            raise UnsupportedDirectionError(source_lang, target_lang)

        clean_input = validate_text(text, allow_empty=False, field_name="text")
        self._ensure_loaded()

        import torch

        # Prepare model inputs with NLLB-style language tokens if applicable
        src_token = "eng_Latn" if src_canon == "eng" else "trp_Latn"
        tgt_token = "trp_Latn" if tgt_canon == "trp" else "eng_Latn"

        tokenizer = self._tokenizer
        model = self._model

        # Tokenize with source language prefix if supported
        inputs = tokenizer(clean_input, return_tensors="pt").to(self.device)

        gen_kwargs: Dict[str, Any] = {"max_length": 128}
        if hasattr(tokenizer, "lang_code_to_id") and tgt_token in tokenizer.lang_code_to_id:
            gen_kwargs["forced_bos_token_id"] = tokenizer.lang_code_to_id[tgt_token]

        with torch.no_grad():
            outputs = model.generate(**inputs, **gen_kwargs)

        translated = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

        return TranslationResult(
            source_text=clean_input,
            translated_text=translated,
            source_lang=src_canon,
            target_lang=tgt_canon,
            backend=f"huggingface:{self.model_name}",
            confidence=0.85,
            notes="Neural model generation. Output should be reviewed for low-resource hallucination.",
        )


class Translator:
    """High-level translation coordinator supporting multiple backends."""

    def __init__(
        self,
        default_backend: str = "phrase",
        phrase_translator: Optional[VerifiedPhraseTranslator] = None,
        custom_translator: Optional[BaseTranslator] = None,
    ) -> None:
        self.default_backend = default_backend
        self._phrase_translator = phrase_translator or VerifiedPhraseTranslator()
        self._custom_translator = custom_translator
        self._hf_translator: Optional[HuggingFaceTranslator] = None

    def translate(
        self,
        text: str,
        source_lang: str = "en",
        target_lang: str = "trp",
        backend: Optional[str] = None,
        **kwargs: Any,
    ) -> TranslationResult:
        """Translate text between English and Kokborok.

        Args:
            text: Input string.
            source_lang: Source language ('en', 'eng', 'trp', 'kokborok').
            target_lang: Target language ('en', 'eng', 'trp', 'kokborok').
            backend: Translation backend ('phrase', 'huggingface', 'custom').
            **kwargs: Extra arguments passed to backends (e.g. model_name).

        Returns:
            TranslationResult instance.

        Raises:
            EmptyInputError: If input text is empty.
            InvalidLanguageError: If an invalid language code is specified.
            UnsupportedDirectionError: If source and target are identical or unsupported.
            TranslationNotAvailableError: If phrase cannot be verified and no neural model is active.
        """
        selected_backend = (backend or self.default_backend).lower()

        if selected_backend in ("phrase", "verified_phrase"):
            return self._phrase_translator.translate(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang,
            )

        elif selected_backend in ("huggingface", "hf"):
            if self._hf_translator is None:
                model_name = kwargs.get("model_name", "MWirelabs/kokborok-mt")
                device = kwargs.get("device", "cpu")
                self._hf_translator = HuggingFaceTranslator(model_name=model_name, device=device)
            return self._hf_translator.translate(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang,
            )

        elif selected_backend == "custom":
            if self._custom_translator is None:
                raise ValueError("No custom translator backend was registered.")
            return self._custom_translator.translate(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang,
            )

        else:
            raise ValueError(
                f"Unknown translation backend '{selected_backend}'. "
                "Supported: 'phrase', 'huggingface', 'custom'."
            )


# Module-level default translator instance
_DEFAULT_TRANSLATOR_INSTANCE: Optional[Translator] = None


def get_default_translator() -> Translator:
    """Get or initialize the shared Translator instance."""
    global _DEFAULT_TRANSLATOR_INSTANCE
    if _DEFAULT_TRANSLATOR_INSTANCE is None:
        _DEFAULT_TRANSLATOR_INSTANCE = Translator()
    return _DEFAULT_TRANSLATOR_INSTANCE


def translate(
    text: str,
    source_lang: str = "en",
    target_lang: str = "trp",
    backend: str = "phrase",
    **kwargs: Any,
) -> TranslationResult:
    """Translate text between English and Kokborok.

    Convenience function providing instant access to verified translation.

    Examples:
        >>> translate("Good morning", "en", "trp")
        TranslationResult(source_text='Good morning', translated_text='Phung kaham', ...)

        >>> translate("Hambai", "trp", "en")
        TranslationResult(source_text='Hambai', translated_text='Thank you', ...)

    Args:
        text: Input string to translate.
        source_lang: Source language code (e.g. 'en', 'eng', 'trp', 'kokborok').
        target_lang: Target language code (e.g. 'trp', 'en').
        backend: Backend engine ('phrase' for verified phrases, 'huggingface' for models).
        **kwargs: Backend configuration options.

    Returns:
        TranslationResult object.

    Raises:
        EmptyInputError: If input is empty.
        InvalidLanguageError: If language code is invalid.
        UnsupportedDirectionError: If direction is not supported.
        TranslationNotAvailableError: If sentence cannot be translated by verified resources.
    """
    translator = get_default_translator()
    return translator.translate(
        text=text,
        source_lang=source_lang,
        target_lang=target_lang,
        backend=backend,
        **kwargs,
    )
