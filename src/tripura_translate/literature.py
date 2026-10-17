"""Kokborok (Tripuri) literature, folklore, poetry, and catalog module.

This module provides the `KokborokLiterature` class and top-level helper
functions (`search_literature`, `list_literature`, `get_literature`) for
cataloging, querying, and retrieving authentic Kokborok folklores, stories,
books, poems, and proverbs.

Ethical & Legal Safeguards:
- Authentic public domain folktales, proverbs, and traditional cradle verses include
  their verified text and cultural notes.
- Copyrighted 20th- and 21st-century literary publications (novels, modern poetry,
  and modern grammars) are cataloged strictly with metadata, summaries, citations,
  and legitimate institutional source links (Sahitya Akademi, TTAADC, TRCI, Govt. of Tripura).
- No folklores, words, or translations are fabricated.
"""

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from tripura_translate.exceptions import (
    EmptyInputError,
    LiteratureNotFoundError,
)
from tripura_translate.text_processing import clean_text


_DEFAULT_LITERATURE_PATH = (
    Path(__file__).parent / "data" / "kokborok_literature.json"
)


@dataclass
class LiteratureItem:
    """Represents a single literary work, folklore story, book, poem, or proverb.

    Attributes:
        id: Unique identifier string for the item.
        title: Primary display title.
        title_kokborok: Title in Kokborok language (Latin or Bengali script).
        title_english: Translated or Anglicized title.
        author_or_source: Author, compiler, or traditional cultural source.
        category: Literary genre ('folklore', 'story', 'book', 'poem', 'proverb', 'grammar', 'epic_chronicle').
        language: Language code ('trp', 'trp-en', 'trp-bn-en', etc.).
        script: Script used ('latin', 'bengali', 'multilingual').
        year: Year of publication or historical documentation (or None for oral lore).
        source_institution: Reputable publisher, archive, or cultural body.
        source_links: Legitimate reference URLs or archive catalog links.
        copyright_status: 'public_domain', 'traditional_cultural_expression', or 'copyrighted_metadata_only'.
        has_full_text: True if full text is legally included; False for metadata-only entries.
        summary: Verified description of themes, plot, or linguistic significance.
        tags: Keywords for searching and taxonomy.
        content: Full text when legally permitted, or None.
        metadata: Additional metadata (e.g., botanical references, related festivals).
    """

    id: str
    title: str
    title_kokborok: Optional[str] = None
    title_english: Optional[str] = None
    author_or_source: str = "Traditional Tripuri Oral Folklore"
    category: str = "folklore"
    language: str = "trp-en"
    script: str = "latin"
    year: Optional[int] = None
    source_institution: str = "Directorate of Kokborok & Other Minority Languages, Government of Tripura"
    source_links: List[str] = field(default_factory=list)
    copyright_status: str = "traditional_cultural_expression"
    has_full_text: bool = False
    summary: str = ""
    tags: List[str] = field(default_factory=list)
    content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the item into a serializable dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "title_kokborok": self.title_kokborok,
            "title_english": self.title_english,
            "author_or_source": self.author_or_source,
            "category": self.category,
            "language": self.language,
            "script": self.script,
            "year": self.year,
            "source_institution": self.source_institution,
            "source_links": list(self.source_links),
            "copyright_status": self.copyright_status,
            "has_full_text": self.has_full_text,
            "summary": self.summary,
            "tags": list(self.tags),
            "content": self.content,
            "metadata": dict(self.metadata),
        }

    def format_citation(self) -> str:
        """Format an academic or bibliographic citation string for this entry."""
        year_str = f" ({self.year})" if self.year else ""
        return (
            f"{self.author_or_source}{year_str}. '{self.title}'. "
            f"Published/Archived by {self.source_institution}. [{self.category.capitalize()}]"
        )

    def preview(self, max_length: int = 150) -> str:
        """Return a brief text preview of the content or summary."""
        text = self.content or self.summary
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[:max_length].rstrip() + "..."

    def is_public_domain(self) -> bool:
        """Return True if the work is in the public domain or traditional heritage."""
        return self.copyright_status in ("public_domain", "traditional_cultural_expression")

    def __getitem__(self, key: str) -> Any:
        """Provide dictionary-like subscript access for backwards compatibility."""
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        """Dictionary-like get method."""
        return getattr(self, key, default)


class KokborokLiterature:
    """Manages an authentic catalog of Kokborok folklores, stories, books, and poems.

    Provides search, filtering, and retrieval mechanisms adhering to copyright
    and cultural accuracy standards.
    """

    def __init__(self, data_path: Optional[Path] = None) -> None:
        """Initialize the literature catalog from a JSON file.

        Args:
            data_path: Optional custom path to a literature JSON file.
        """
        self._data_path = Path(data_path) if data_path else _DEFAULT_LITERATURE_PATH
        self._items: List[LiteratureItem] = []
        self._id_map: Dict[str, LiteratureItem] = {}
        self._categories: Set[str] = set()
        self._authors: Set[str] = set()
        self._load_data()

    def _load_data(self) -> None:
        """Load and parse the literature dataset."""
        if not self._data_path.exists():
            raise FileNotFoundError(
                f"Kokborok literature data file not found at: {self._data_path}"
            )

        with open(self._data_path, "r", encoding="utf-8") as file:
            raw_entries = json.load(file)

        if not isinstance(raw_entries, list):
            raise ValueError(
                f"Invalid literature file format at {self._data_path}: expected JSON list."
            )

        self._items.clear()
        self._id_map.clear()
        self._categories.clear()
        self._authors.clear()

        for entry in raw_entries:
            item = LiteratureItem(
                id=entry["id"],
                title=entry.get("title", ""),
                title_kokborok=entry.get("title_kokborok"),
                title_english=entry.get("title_english"),
                author_or_source=entry.get("author_or_source", "Traditional Tripuri Oral Folklore"),
                category=entry.get("category", "folklore").lower().strip(),
                language=entry.get("language", "trp-en"),
                script=entry.get("script", "latin"),
                year=entry.get("year"),
                source_institution=entry.get("source_institution", ""),
                source_links=entry.get("source_links", []),
                copyright_status=entry.get("copyright_status", "traditional_cultural_expression"),
                has_full_text=entry.get("has_full_text", False),
                summary=entry.get("summary", ""),
                tags=entry.get("tags", []),
                content=entry.get("content"),
                metadata=entry.get("metadata", {}),
            )
            self._items.append(item)
            self._id_map[item.id.lower()] = item
            self._categories.add(item.category)
            if item.author_or_source:
                self._authors.add(item.author_or_source)

    @property
    def total_items(self) -> int:
        """Return the total number of literary items in the catalog."""
        return len(self._items)

    def count(self) -> int:
        """Return the total count of cataloged items."""
        return len(self._items)

    def get_categories(self) -> List[str]:
        """Return a sorted list of all available categories."""
        return sorted(self._categories)

    def get_authors(self) -> List[str]:
        """Return a sorted list of all unique authors or traditional sources."""
        return sorted(self._authors)

    def get_all(self) -> List[LiteratureItem]:
        """Return all catalog items."""
        return list(self._items)

    def get_by_id(self, item_id: str) -> LiteratureItem:
        """Retrieve a specific literature item by its unique ID.

        Args:
            item_id: The unique slug identifier (e.g., 'chethuang-kothoma').

        Returns:
            The matched LiteratureItem.

        Raises:
            EmptyInputError: If item_id is empty or whitespace.
            LiteratureNotFoundError: If no item matches the ID.
        """
        if not item_id or not item_id.strip():
            raise EmptyInputError("item_id")

        key = clean_text(item_id).lower()
        if key in self._id_map:
            return self._id_map[key]

        suggestions = [
            i.id for i in self._items if key in i.id or key in i.title.lower()
        ][:5]
        raise LiteratureNotFoundError(identifier=item_id, suggestions=suggestions)

    def list_items(
        self,
        category: Optional[str] = None,
        language: Optional[str] = None,
        has_full_text: Optional[bool] = None,
        script: Optional[str] = None,
    ) -> List[LiteratureItem]:
        """List literature items with optional filtering.

        Args:
            category: Filter by category (e.g., 'folklore', 'story', 'book', 'poem', 'proverb').
            language: Filter by language code (e.g., 'trp', 'trp-en').
            has_full_text: Filter by whether complete full text is legally included.
            script: Filter by script ('latin', 'bengali', 'multilingual').

        Returns:
            A list of matching LiteratureItem objects.
        """
        results = list(self._items)

        if category:
            cat_norm = category.strip().lower()
            results = [item for item in results if item.category == cat_norm]

        if language:
            lang_norm = language.strip().lower()
            results = [item for item in results if lang_norm in item.language.lower()]

        if has_full_text is not None:
            results = [item for item in results if item.has_full_text is has_full_text]

        if script:
            script_norm = script.strip().lower()
            results = [item for item in results if item.script.lower() == script_norm]

        return results

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        exact: bool = False,
        full_text_only: bool = False,
    ) -> List[LiteratureItem]:
        """Search the literature catalog by keywords, titles, authors, or themes.

        Args:
            query: The search text (e.g., 'chethuang', 'Murasingh', 'proverbs').
            category: Optional category filter.
            exact: If True, matches titles or authors exactly. If False, does partial matching.
            full_text_only: If True, only returns items that have full text included.

        Returns:
            List of matching LiteratureItem objects.

        Raises:
            EmptyInputError: If query is empty or whitespace.
        """
        cleaned_query = clean_text(query).strip()
        if not cleaned_query:
            raise EmptyInputError("query")

        q_lower = cleaned_query.lower()
        results: List[LiteratureItem] = []

        pool = self.list_items(category=category, has_full_text=True if full_text_only else None)

        for item in pool:
            if exact:
                match = (
                    q_lower == item.id.lower()
                    or q_lower == item.title.lower()
                    or (item.title_kokborok and q_lower == item.title_kokborok.lower())
                    or (item.title_english and q_lower == item.title_english.lower())
                    or q_lower == item.author_or_source.lower()
                )
            else:
                # Partial search across title, Kokborok title, English title, author, summary, tags, and content
                title_match = q_lower in item.title.lower()
                kb_title_match = bool(item.title_kokborok and q_lower in item.title_kokborok.lower())
                en_title_match = bool(item.title_english and q_lower in item.title_english.lower())
                author_match = q_lower in item.author_or_source.lower()
                tag_match = any(q_lower in tag.lower() for tag in item.tags)
                summary_match = q_lower in item.summary.lower()
                content_match = bool(item.content and q_lower in item.content.lower())
                institution_match = q_lower in item.source_institution.lower()

                match = (
                    title_match
                    or kb_title_match
                    or en_title_match
                    or author_match
                    or tag_match
                    or summary_match
                    or content_match
                    or institution_match
                )

            if match:
                results.append(item)

        return results

    def get_folklores(self) -> List[LiteratureItem]:
        """Retrieve all folklore and mythological narrative items."""
        return self.list_items(category="folklore")

    def get_books(self) -> List[LiteratureItem]:
        """Retrieve all cataloged books, grammars, and novels."""
        return [
            item
            for item in self._items
            if item.category in ("book", "grammar", "epic_chronicle")
        ]

    def get_poems(self) -> List[LiteratureItem]:
        """Retrieve all poetry collections, folk songs, and verses."""
        return self.list_items(category="poem")

    def get_proverbs(self) -> List[LiteratureItem]:
        """Retrieve all proverbs and maxims (Kokbwkrai)."""
        return self.list_items(category="proverb")

    def get_full_text_items(self) -> List[LiteratureItem]:
        """Retrieve all items that contain legal full text."""
        return self.list_items(has_full_text=True)


# Module-level singleton
_DEFAULT_LITERATURE_CATALOG: Optional[KokborokLiterature] = None


def get_default_literature() -> KokborokLiterature:
    """Return or initialize the singleton KokborokLiterature catalog."""
    global _DEFAULT_LITERATURE_CATALOG
    if _DEFAULT_LITERATURE_CATALOG is None:
        _DEFAULT_LITERATURE_CATALOG = KokborokLiterature()
    return _DEFAULT_LITERATURE_CATALOG


def search_literature(
    query: str,
    category: Optional[str] = None,
    exact: bool = False,
) -> List[LiteratureItem]:
    """Top-level convenience function to search Kokborok literature.

    Args:
        query: Search term (e.g. 'Chethuang', 'Murasingh', 'Garia').
        category: Optional category filter ('folklore', 'poem', 'book', 'proverb').
        exact: Whether to match exact string values.

    Returns:
        List of matching LiteratureItem objects.
    """
    catalog = get_default_literature()
    return catalog.search(query=query, category=category, exact=exact)


def list_literature(
    category: Optional[str] = None,
    has_full_text: Optional[bool] = None,
) -> List[LiteratureItem]:
    """Top-level convenience function to list cataloged Kokborok literature.

    Args:
        category: Optional category filter.
        has_full_text: Optional boolean filter.

    Returns:
        List of LiteratureItem objects.
    """
    catalog = get_default_literature()
    return catalog.list_items(category=category, has_full_text=has_full_text)


def get_literature(item_id: str) -> LiteratureItem:
    """Top-level convenience function to retrieve a literature item by ID.

    Args:
        item_id: The unique identifier slug.

    Returns:
        LiteratureItem.

    Raises:
        LiteratureNotFoundError: If the item is not found.
    """
    catalog = get_default_literature()
    return catalog.get_by_id(item_id=item_id)
