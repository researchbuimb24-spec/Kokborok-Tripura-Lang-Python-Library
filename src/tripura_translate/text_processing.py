"""Text processing utilities for Kokborok (Tripuri) and multilingual text.

Kokborok is written in both the Roman (Latin) script and the Eastern Nagari (Bengali)
script. In Roman Kokborok, the letter 'w' represents the close central unrounded vowel
[ɨ], and post-vocalic 'h' often functions as a tone marker indicating a high tone.
Kokborok is also an agglutinative language with characteristic nominal/verbal prefixes
(such as 'bw-', 'bu-', 'bo-', 'kw-') and grammatical suffixes (such as '-kha', '-di',
'-rok', '-no', '-ni', '-bai', '-ya').

This module provides Unicode-safe text cleaning, script detection, Kokborok
tokenization, morphological structure inspection, and sentence formatting.
"""

import re
import unicodedata
from typing import Any, Dict, List, Optional

from tripura_translate.exceptions import EmptyInputError


# Known Kokborok prefixes and suffixes based on published linguistic grammars
KOKBOROK_PREFIXES = (
    "bw-", "bo-", "bu-", "kw-",
    "bw", "bo", "bu", "kw",
)

KOKBOROK_SUFFIXES = (
    ("song", "kinship_plural"),
    ("rok", "plural"),
    ("kha", "past_perfective"),
    ("di", "imperative"),
    ("nai", "future_agentive"),
    ("no", "accusative_dative"),
    ("ni", "genitive_possessive"),
    ("bai", "instrumental_associative"),
    ("ya", "negative"),
    ("o", "locative"),
)

# Regex patterns for script identification
_RE_LATIN = re.compile(r"[A-Za-z\u00C0-\u024F]")
_RE_BENGALI = re.compile(r"[\u0980-\u09FF]")
_RE_WHITESPACE = re.compile(r"\s+")
_RE_TOKEN = re.compile(r"[^\w\-]+", re.UNICODE)


def clean_text(text: str) -> str:
    """Normalize and clean input text safely across Unicode representations.

    Performs:
    1. Unicode normalization (NFC).
    2. Stripping invisible control characters, zero-width spaces, and byte-order marks.
    3. Replacing non-breaking spaces (\u00a0) and formatting spaces with standard ASCII space.
    4. Collapsing consecutive whitespace into a single space.
    5. Stripping leading and trailing whitespace.

    Args:
        text: The raw input string.

    Returns:
        Cleaned, normalized string.

    Raises:
        TypeError: If the input is not a string.
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected a string, but received {type(text).__name__}.")

    # Normalize Unicode composition
    normalized = unicodedata.normalize("NFC", text)

    # Remove invisible zero-width characters and BOM while preserving normal characters
    # \u200b: Zero-width space, \ufeff: Byte order mark, \u200e/\u200f: Directional marks
    cleaned_chars = []
    for char in normalized:
        if char in ("\ufeff", "\u200b", "\u200e", "\u200f"):
            continue
        # Replace non-breaking space with normal space
        if char == "\u00a0":
            cleaned_chars.append(" ")
        else:
            cleaned_chars.append(char)

    result = "".join(cleaned_chars)
    # Collapse multiple whitespaces and trim
    result = _RE_WHITESPACE.sub(" ", result).strip()
    return result


def validate_text(
    text: Any,
    allow_empty: bool = False,
    expected_script: Optional[str] = None,
    field_name: str = "text",
) -> str:
    """Validate and clean input text, handling errors gracefully.

    Args:
        text: The input to validate.
        allow_empty: If True, empty strings will not raise an EmptyInputError.
        expected_script: Optional script requirement ("latin" or "bengali").
        field_name: Name of the input field for descriptive error messages.

    Returns:
        The cleaned string.

    Raises:
        TypeError: If text is not a string.
        EmptyInputError: If text is empty or only whitespace (and allow_empty is False).
        ValueError: If expected_script does not match detected script.
    """
    if text is None:
        raise EmptyInputError(field_name=field_name)

    if not isinstance(text, str):
        raise TypeError(f"Expected a string for '{field_name}', got {type(text).__name__}.")

    cleaned = clean_text(text)
    if not cleaned and not allow_empty:
        raise EmptyInputError(field_name=field_name)

    if expected_script and cleaned:
        detected = detect_script(cleaned)
        if expected_script.lower() != detected.lower() and detected != "mixed":
            raise ValueError(
                f"Expected script '{expected_script}', but detected '{detected}' for '{cleaned}'."
            )

    return cleaned


def detect_script(text: str) -> str:
    """Detect whether text is written in Latin (Roman), Bengali (Eastern Nagari), or mixed.

    Kokborok is widely written in both Latin (Roman Kokborok) and Bengali script.

    Args:
        text: Input string.

    Returns:
        One of: 'latin', 'bengali', 'mixed', or 'unknown'.
    """
    if not isinstance(text, str) or not text.strip():
        return "unknown"

    has_latin = bool(_RE_LATIN.search(text))
    has_bengali = bool(_RE_BENGALI.search(text))

    if has_latin and has_bengali:
        return "mixed"
    if has_latin:
        return "latin"
    if has_bengali:
        return "bengali"
    return "unknown"


def tokenize_kokborok(text: str, keep_hyphens: bool = True) -> List[str]:
    """Tokenize Kokborok text into words, preserving hyphenated compounds.

    In Kokborok, compound words and affixes are often written with hyphens
    (e.g., 'phung-kaham', 'kok-borok', 'sal-kwtal').

    Args:
        text: Input string.
        keep_hyphens: Whether to treat hyphenated words as single tokens.

    Returns:
        A list of string word tokens with punctuation removed.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return []

    tokens: List[str] = []
    # Split by whitespace first
    raw_words = cleaned.split()

    for word in raw_words:
        if keep_hyphens:
            # Strip outer punctuation around hyphens: [",", ".", "!", "?", "\"", "'", etc.]
            stripped = word.strip(".,!?:;\"'()[]{}«»`~—–-")
            if stripped:
                tokens.append(stripped)
        else:
            # Replace hyphens with spaces and split
            sub_words = word.replace("-", " ").split()
            for sub in sub_words:
                stripped = sub.strip(".,!?:;\"'()[]{}«»`~—–")
                if stripped:
                    tokens.append(stripped)

    return tokens


def analyze_word_structure(word: str) -> Dict[str, Any]:
    """Analyze the morphological structure and phonetic markers of a Kokborok word.

    Kokborok words frequently exhibit:
    - The high central vowel 'w' [ɨ] (e.g., nwng, wngkha, swi, bwsla).
    - Tone indicator 'h' (e.g., kaham, buphang, hamjak).
    - Nominal/class prefixes: 'bw-', 'bu-', 'bo-', 'kw-'.
    - Grammatical suffixes: '-kha', '-rok', '-no', '-di', '-ya', '-ni', '-bai', '-o'.

    Args:
        word: A single Kokborok word.

    Returns:
        A dictionary with morphological details:
        - 'original': The original word.
        - 'script': Detected script.
        - 'has_kokborok_vowel_w': Boolean indicating presence of 'w' vowel.
        - 'has_tone_marker_h': Boolean indicating presence of tone-marking 'h'.
        - 'detected_prefix': Detected prefix or None.
        - 'detected_suffix': Detected suffix or None.
        - 'suffix_function': Grammatical function of suffix or None.
        - 'stem_candidate': Potential root stem after removing identified affixes.
    """
    clean_word = word.strip(".,!?:;\"'()[]{}").lower()
    script = detect_script(clean_word)

    has_w = "w" in clean_word if script == "latin" else False
    # In Kokborok Roman script, 'h' following a vowel often marks high tone
    has_tone_h = bool(re.search(r"[aeiouw]h", clean_word)) if script == "latin" else False

    detected_prefix: Optional[str] = None
    detected_suffix: Optional[str] = None
    suffix_function: Optional[str] = None
    stem_candidate = clean_word

    PROTECTED_ROOTS = {"borok", "bolong", "bokhorok", "bwsla", "bwroi"}

    if script == "latin" and len(clean_word) > 3:
        # Check suffixes first
        for suffix, func in KOKBOROK_SUFFIXES:
            if clean_word.endswith("-" + suffix):
                detected_suffix = suffix
                suffix_function = func
                stem_candidate = clean_word[: -len("-" + suffix)]
                break
            elif clean_word.endswith(suffix) and len(clean_word) > len(suffix) + 2:
                # Do not strip suffix if stem would be too short or if it's a known whole word
                potential_stem = clean_word[: -len(suffix)]
                if len(potential_stem) >= 2 and clean_word not in PROTECTED_ROOTS:
                    detected_suffix = suffix
                    suffix_function = func
                    stem_candidate = potential_stem
                    break

        # Check prefixes on the remaining stem candidate
        for prefix in ("bw-", "bo-", "bu-", "kw-"):
            if stem_candidate.startswith(prefix) and len(stem_candidate) > len(prefix) + 1:
                detected_prefix = prefix
                stem_candidate = stem_candidate[len(prefix):]
                break

        if not detected_prefix and stem_candidate not in PROTECTED_ROOTS:
            for prefix in ("bw", "bo", "bu", "kw"):
                if stem_candidate.startswith(prefix) and len(stem_candidate) >= len(prefix) + 3:
                    detected_prefix = prefix
                    stem_candidate = stem_candidate[len(prefix):]
                    break

    return {
        "original": word,
        "normalized": clean_word,
        "script": script,
        "has_kokborok_vowel_w": has_w,
        "has_tone_marker_h": has_tone_h,
        "detected_prefix": detected_prefix,
        "detected_suffix": detected_suffix,
        "suffix_function": suffix_function,
        "stem_candidate": stem_candidate if stem_candidate != clean_word else clean_word,
    }


def remove_tone_markers(word: str) -> str:
    """Normalize a Kokborok word by removing tone-marking 'h' for fuzzy searches.

    In Roman Kokborok orthography, tone is sometimes written with 'h' (e.g. kaham)
    and sometimes omitted in informal texts (e.g. kaam). This utility assists in
    tone-tolerant search matching.

    Args:
        word: A Kokborok word in Latin script.

    Returns:
        Word with post-vocalic 'h' removed.
    """
    clean = word.lower()
    # Replace post-vocalic 'h' (e.g. 'ah', 'eh', 'ih', 'oh', 'uh', 'wh') with the vowel alone
    return re.sub(r"([aeiouw])h", r"\1", clean)


def format_kokborok_text(text: str, capitalize_sentences: bool = True) -> str:
    """Format Kokborok sentences with standard punctuation spacing and capitalization.

    Args:
        text: Input string.
        capitalize_sentences: Whether to capitalize the first letter of each sentence.

    Returns:
        Nicely formatted Kokborok text string.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return ""

    # Ensure single space after punctuation: .,!?:;
    formatted = re.sub(r"\s*([.,!?:;])\s*", r"\1 ", cleaned)
    # Remove space before closing quotes or brackets
    formatted = re.sub(r"\s+([)\]}»])", r"\1", formatted)
    # Remove space after opening quotes or brackets
    formatted = re.sub(r"([(\[{«])\s+", r"\1", formatted)
    formatted = formatted.strip()

    if capitalize_sentences and formatted:
        # Split by sentence boundaries (.!?) and capitalize first non-space character
        parts = re.split(r"([.!?]+\s*)", formatted)
        reconstructed = []
        for i, part in enumerate(parts):
            if i % 2 == 0 and part:  # Sentence text
                reconstructed.append(part[:1].upper() + part[1:])
            else:  # Punctuation delimiter
                reconstructed.append(part)
        formatted = "".join(reconstructed)

    return formatted


def process_text(
    text: str,
    script_check: bool = True,
    normalize_unicode: bool = True,
) -> Dict[str, Any]:
    """Process, clean, analyze, and inspect Kokborok or multilingual text.

    This is the primary high-level text processing function exposed by the library.

    Args:
        text: The raw input text.
        script_check: Whether to detect and validate the script.
        normalize_unicode: Whether to perform Unicode normalization.

    Returns:
        A dictionary containing:
        - 'cleaned_text': Cleaned, standardized string.
        - 'script': Detected script ('latin', 'bengali', 'mixed', 'unknown').
        - 'tokens': List of individual word tokens.
        - 'word_count': Total number of words.
        - 'char_count': Total characters in cleaned text.
        - 'word_analysis': Morphological breakdown for each token.

    Raises:
        EmptyInputError: If text is empty or contains only whitespace.
        TypeError: If text is not a string.
    """
    cleaned = validate_text(text, allow_empty=False, field_name="text")
    script = detect_script(cleaned) if script_check else "unknown"
    tokens = tokenize_kokborok(cleaned)

    word_analysis = [analyze_word_structure(t) for t in tokens]

    return {
        "cleaned_text": cleaned,
        "script": script,
        "tokens": tokens,
        "word_count": len(tokens),
        "char_count": len(cleaned),
        "word_analysis": word_analysis,
    }
