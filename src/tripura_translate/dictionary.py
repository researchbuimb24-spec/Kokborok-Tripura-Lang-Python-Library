"""Searchable Kokborok-English dictionary module.

Provides the `KokborokDictionary` class and the top-level `search_dictionary()`
function. Supports exact and partial matching, bidirectional lookup (Kokborok
to English and English to Kokborok), category browsing, and morphological
stem-fallback lookup for inflected Kokborok words.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from tripura_translate.exceptions import (
    DictionaryEntryNotFoundError,
    EmptyInputError,
)
from tripura_translate.text_processing import (
    analyze_word_structure,
    clean_text,
    detect_script,
    remove_tone_markers,
    validate_text,
)


_DEFAULT_DATA_PATH = Path(__file__).parent / "data" / "kokborok_dictionary.json"


class KokborokDictionary:
    """A searchable, verified Kokborok-English dictionary.

    Features:
    - Bidirectional search (Kokborok <-> English).
    - Exact matching and partial / substring matching.
    - Script-aware search (Roman Latin script and Eastern Nagari Bengali script).
    - Tone-tolerant searching (matching words with or without tonal 'h').
    - Morphological stem fallback for inflected Kokborok words (e.g. 'phaidi' -> 'phai').
    - Category filtering (e.g., 'greetings', 'numbers', 'nature', 'family', 'colors').
    """

    def __init__(self, data_path: Optional[Path] = None) -> None:
        """Initialize the dictionary with a path to JSON data.

        Args:
            data_path: Optional custom path to a dictionary JSON file.
        """
        self._data_path = Path(data_path) if data_path else _DEFAULT_DATA_PATH
        self._entries: List[Dict[str, Any]] = []
        self._loaded: bool = False
        self._categories: Set[str] = set()
        self._load_data()

    def _load_data(self) -> None:
        """Load dictionary entries from the JSON dataset."""
        if not self._data_path.exists():
            raise FileNotFoundError(
                f"Dictionary data file not found at: {self._data_path}"
            )

        with open(self._data_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError(
                f"Invalid dictionary file format at {self._data_path}: expected JSON list."
            )

        self._entries = data
        self._categories = {
            entry.get("category", "general")
            for entry in self._entries
            if "category" in entry
        }
        self._loaded = True

    @property
    def total_entries(self) -> int:
        """Return the number of entries in the dictionary."""
        return len(self._entries)

    def count(self) -> int:
        """Return the total number of dictionary entries."""
        return len(self._entries)

    def get_categories(self) -> List[str]:
        """Return a sorted list of all available semantic categories."""
        return sorted(self._categories)

    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Retrieve all entries belonging to a specific category.

        Args:
            category: The category name (e.g., 'numbers', 'greetings', 'family').

        Returns:
            A list of dictionary entries matching the category.
        """
        cat_lower = category.strip().lower()
        return [
            entry
            for entry in self._entries
            if entry.get("category", "").lower() == cat_lower
        ]

    def add_entry(self, entry: Dict[str, Any]) -> None:
        """Add a new verified dictionary entry in-memory.

        Args:
            entry: A dictionary containing at least 'kokborok_latin' and 'english'.

        Raises:
            ValueError: If required fields are missing.
        """
        if not isinstance(entry, dict):
            raise TypeError("Entry must be a dictionary.")
        if "kokborok_latin" not in entry or "english" not in entry:
            raise ValueError(
                "Dictionary entry must contain at least 'kokborok_latin' and 'english'."
            )

        self._entries.append(entry)
        if "category" in entry:
            self._categories.add(entry["category"].lower())

    def search(
        self,
        query: str,
        search_in: str = "both",
        exact: bool = False,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search the dictionary for words or phrases.

        Args:
            query: The search term (Kokborok or English).
            search_in: Target to search in: 'kokborok', 'english', or 'both'.
            exact: Whether to require exact matches (case-insensitive) or allow partial matches.
            limit: Maximum number of results to return.

        Returns:
            A list of matching dictionary entries.

        Raises:
            EmptyInputError: If query is empty or only whitespace.
            ValueError: If search_in is not one of ('kokborok', 'english', 'both').
        """
        cleaned_query = validate_text(query, allow_empty=False, field_name="query")
        target_mode = search_in.strip().lower()
        if target_mode not in ("kokborok", "english", "both"):
            raise ValueError(
                f"Invalid search_in option '{search_in}'. Must be 'kokborok', 'english', or 'both'."
            )

        q_lower = cleaned_query.lower()
        q_tone_free = remove_tone_markers(q_lower)
        script = detect_script(cleaned_query)

        results: List[Dict[str, Any]] = []
        seen_keys: Set[str] = set()

        def add_result(entry: Dict[str, Any]) -> None:
            key = f"{entry.get('kokborok_latin', '')}_{entry.get('english', '')}"
            if key not in seen_keys:
                seen_keys.add(key)
                results.append(entry)

        for entry in self._entries:
            if len(results) >= limit:
                break

            kb_latin = entry.get("kokborok_latin", "").lower()
            kb_bengali = entry.get("kokborok_bengali", "")
            eng = entry.get("english", "").lower()
            synonyms = [s.lower() for s in entry.get("english_synonyms", [])]

            match = False

            # Check Kokborok side
            if target_mode in ("kokborok", "both"):
                if script == "bengali":
                    # Exact or partial match in Bengali script
                    if exact:
                        match = cleaned_query == kb_bengali
                    else:
                        match = cleaned_query in kb_bengali
                else:
                    # Match in Latin script
                    if exact:
                        match = (
                            q_lower == kb_latin
                            or q_tone_free == remove_tone_markers(kb_latin)
                        )
                    else:
                        match = (
                            q_lower in kb_latin
                            or q_tone_free in remove_tone_markers(kb_latin)
                        )

            # Check English side
            if not match and target_mode in ("english", "both"):
                if exact:
                    match = (q_lower == eng) or (q_lower in synonyms)
                else:
                    match = (
                        (q_lower in eng)
                        or any(q_lower in syn for syn in synonyms)
                    )

            if match:
                add_result(entry)

        return results

    def lookup_word(
        self,
        word: str,
        lang: str = "auto",
        raise_on_not_found: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Look up a single word with morphological stem fallback for Kokborok.

        If an exact match is not found for a Kokborok word, this method analyzes
        its prefixes/suffixes (e.g. turning 'phaidi' into 'phai' + '-di') and
        searches for the root stem, annotating the result with a morphology note.

        Args:
            word: The word to look up.
            lang: 'kokborok', 'english', or 'auto'.
            raise_on_not_found: Whether to raise DictionaryEntryNotFoundError if not found.

        Returns:
            Dictionary entry (possibly with 'morphology_note' and 'analyzed_stem')
            or None if not found.

        Raises:
            EmptyInputError: If word is empty.
            DictionaryEntryNotFoundError: If not found and raise_on_not_found is True.
        """
        cleaned = validate_text(word, allow_empty=False, field_name="word")
        lang_mode = lang.strip().lower()

        # Step 1: Attempt exact search first
        target_mode = "both" if lang_mode == "auto" else lang_mode
        exact_results = self.search(cleaned, search_in=target_mode, exact=True, limit=1)
        if exact_results:
            return exact_results[0]

        # Step 2: If language is auto or kokborok, try morphological decomposition
        if lang_mode in ("auto", "kokborok"):
            analysis = analyze_word_structure(cleaned)
            stem = analysis["stem_candidate"]
            if stem != cleaned.lower():
                stem_results = self.search(stem, search_in="kokborok", exact=True, limit=1)
                if stem_results:
                    entry_copy = dict(stem_results[0])
                    note_parts = [f"Base root: '{stem}'"]
                    if analysis["detected_prefix"]:
                        note_parts.append(f"prefix: '{analysis['detected_prefix']}'")
                    if analysis["detected_suffix"]:
                        suffix_info = analysis['detected_suffix']
                        if analysis['suffix_function']:
                            suffix_info += f" ({analysis['suffix_function']})"
                        note_parts.append(f"suffix: '-{suffix_info}'")
                    entry_copy["morphology_note"] = "; ".join(note_parts)
                    entry_copy["analyzed_input"] = cleaned
                    return entry_copy

        # Step 3: Partial fallback search
        partial_results = self.search(cleaned, search_in=target_mode, exact=False, limit=3)
        if partial_results:
            entry_copy = dict(partial_results[0])
            entry_copy["partial_match"] = True
            return entry_copy

        if raise_on_not_found:
            raise DictionaryEntryNotFoundError(query=cleaned)
        return None


# Module-level default dictionary instance (lazy singleton)
_DEFAULT_DICT_INSTANCE: Optional[KokborokDictionary] = None


def get_default_dictionary() -> KokborokDictionary:
    """Get or initialize the shared KokborokDictionary instance."""
    global _DEFAULT_DICT_INSTANCE
    if _DEFAULT_DICT_INSTANCE is None:
        _DEFAULT_DICT_INSTANCE = KokborokDictionary()
    return _DEFAULT_DICT_INSTANCE


def search_dictionary(
    query: str,
    search_in: str = "both",
    exact: bool = False,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Convenience function to search the Kokborok-English dictionary.

    Examples:
        >>> search_dictionary("water")
        [{'kokborok_latin': 'twi', 'english': 'water', ...}]

        >>> search_dictionary("khulumkha", exact=True)
        [{'kokborok_latin': 'khulumkha', 'english': 'hello', ...}]

    Args:
        query: The word or term to search.
        search_in: 'kokborok', 'english', or 'both' (default).
        exact: Whether to enforce exact matching.
        limit: Maximum number of results to return.

    Returns:
        List of matching dictionary entries.
    """
    dictionary = get_default_dictionary()
    return dictionary.search(query=query, search_in=search_in, exact=exact, limit=limit)
