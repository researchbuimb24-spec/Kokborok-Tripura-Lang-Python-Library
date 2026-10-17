"""Tests for the Kokborok literature catalog and module."""

import json
from pathlib import Path
import pytest

from tripura_translate import (
    KokborokLiterature,
    LiteratureItem,
    get_default_literature,
    get_literature,
    list_literature,
    search_literature,
)
from tripura_translate.exceptions import (
    EmptyInputError,
    LiteratureNotFoundError,
    TripuraTranslateError,
)


def test_literature_initialization_default():
    catalog = KokborokLiterature()
    assert catalog.total_items > 0
    assert catalog.count() == catalog.total_items
    categories = catalog.get_categories()
    assert "folklore" in categories
    assert "poem" in categories
    assert "proverb" in categories
    assert "book" in categories or "grammar" in categories
    authors = catalog.get_authors()
    assert any("Radhamohan" in a for a in authors)


def test_literature_custom_path(tmp_path: Path):
    custom_data = [
        {
            "id": "custom-story-1",
            "title": "Custom Kokborok Story",
            "author_or_source": "Traditional Elder",
            "category": "story",
            "language": "trp",
            "script": "latin",
            "source_institution": "Tripura Research",
            "source_links": ["https://example.org"],
            "copyright_status": "traditional_cultural_expression",
            "has_full_text": True,
            "summary": "A test custom story.",
            "tags": ["test"],
            "content": "Kham thung, sumui swr.",
        }
    ]
    file_path = tmp_path / "custom_lit.json"
    file_path.write_text(json.dumps(custom_data), encoding="utf-8")

    catalog = KokborokLiterature(file_path)
    assert catalog.total_items == 1
    item = catalog.get_by_id("custom-story-1")
    assert item.title == "Custom Kokborok Story"
    assert item.content == "Kham thung, sumui swr."


def test_literature_missing_file(tmp_path: Path):
    missing_file = tmp_path / "non_existent.json"
    with pytest.raises(FileNotFoundError):
        KokborokLiterature(missing_file)


def test_literature_invalid_format(tmp_path: Path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text(json.dumps({"error": "not a list"}), encoding="utf-8")
    with pytest.raises(ValueError):
        KokborokLiterature(bad_file)


def test_list_items_and_filtering():
    catalog = get_default_literature()

    # Filter by category
    folklores = catalog.list_items(category="folklore")
    assert len(folklores) > 0
    assert all(item.category == "folklore" for item in folklores)

    # Filter by has_full_text
    full_text_items = catalog.list_items(has_full_text=True)
    assert len(full_text_items) > 0
    assert all(item.has_full_text is True for item in full_text_items)
    assert all(item.content is not None for item in full_text_items)

    metadata_only_items = catalog.list_items(has_full_text=False)
    assert len(metadata_only_items) > 0
    assert all(item.has_full_text is False for item in metadata_only_items)

    # Filter by language
    trp_items = catalog.list_items(language="trp")
    assert len(trp_items) > 0


def test_get_by_id_success():
    catalog = get_default_literature()
    chethuang = catalog.get_by_id("chethuang-kothoma")
    assert isinstance(chethuang, LiteratureItem)
    assert "Chethuang" in chethuang.title
    assert chethuang.category == "folklore"
    assert chethuang.has_full_text is True
    assert chethuang.content is not None
    assert "Alstonia scholaris" in chethuang.content or "Alstonia scholaris" in str(chethuang.metadata)

    # Historical book
    grammar_1900 = catalog.get_by_id("kok-borokma-1900")
    assert grammar_1900.year == 1900
    assert "Radhamohan" in grammar_1900.author_or_source


def test_get_by_id_errors():
    catalog = get_default_literature()

    with pytest.raises(EmptyInputError):
        catalog.get_by_id("")

    with pytest.raises(EmptyInputError):
        catalog.get_by_id("   ")

    with pytest.raises(LiteratureNotFoundError) as exc_info:
        catalog.get_by_id("non-existent-folktale-xyz")
    assert "non-existent-folktale-xyz" in str(exc_info.value)


def test_search_literature():
    catalog = get_default_literature()

    # Search folklore by name
    results = catalog.search("Chethuang")
    assert len(results) >= 1
    assert any(r.id == "chethuang-kothoma" for r in results)

    # Search by author
    author_results = catalog.search("Murasingh")
    assert len(author_results) >= 1
    assert any("Murasingh" in r.author_or_source for r in author_results)

    # Search by tag or theme
    proverb_results = catalog.search("proverb")
    assert len(proverb_results) >= 1

    # Search with category filter
    folklore_results = catalog.search("Garia", category="folklore")
    assert len(folklore_results) >= 1
    assert all(r.category == "folklore" for r in folklore_results)

    # Exact search
    exact_res = catalog.search("Chethuangni Kothoma", exact=True)
    assert len(exact_res) == 1
    assert exact_res[0].id == "chethuang-kothoma"


def test_search_empty_input():
    catalog = get_default_literature()
    with pytest.raises(EmptyInputError):
        catalog.search("")


def test_category_helper_methods():
    catalog = get_default_literature()

    folklores = catalog.get_folklores()
    assert len(folklores) >= 3
    assert all(f.category == "folklore" for f in folklores)

    books = catalog.get_books()
    assert len(books) >= 3
    assert all(b.category in ("book", "grammar", "epic_chronicle") for b in books)

    poems = catalog.get_poems()
    assert len(poems) >= 2
    assert all(p.category == "poem" for p in poems)

    proverbs = catalog.get_proverbs()
    assert len(proverbs) >= 1
    assert all(pr.category == "proverb" for pr in proverbs)

    full_texts = catalog.get_full_text_items()
    assert len(full_texts) >= 4
    for ft in full_texts:
        assert ft.has_full_text is True
        assert ft.content is not None
        assert len(ft.content) > 20


def test_literature_item_helpers():
    catalog = get_default_literature()
    item = catalog.get_by_id("chethuang-kothoma")

    # to_dict
    d = item.to_dict()
    assert isinstance(d, dict)
    assert d["id"] == "chethuang-kothoma"
    assert d["title"] == item.title

    # format_citation
    citation = item.format_citation()
    assert item.author_or_source in citation
    assert item.title in citation

    # preview
    prev = item.preview(max_length=50)
    assert len(prev) <= 53  # 50 + "..."
    assert prev.endswith("...")

    # public domain
    assert item.is_public_domain() is True

    # dict-like subscript and get
    assert item["id"] == "chethuang-kothoma"
    assert item.get("category") == "folklore"
    assert item.get("non_existent_key", "default_val") == "default_val"


def test_legal_and_copyright_safeguards():
    catalog = get_default_literature()
    all_items = catalog.get_all()

    for item in all_items:
        # Every entry must have non-empty ID, title, author/source, source links or institution
        assert item.id, "ID must not be empty"
        assert item.title, "Title must not be empty"
        assert item.author_or_source, "Author or source must be documented"
        assert item.source_institution, "Source institution must be documented"
        assert len(item.source_links) > 0, "At least one legitimate source link must be present"

        # Modern copyrighted works must NEVER include unauthorized full text
        if item.copyright_status == "copyrighted_metadata_only":
            assert item.has_full_text is False, f"Copyrighted item {item.id} must not have full text set to True"
            assert item.content is None, f"Copyrighted item {item.id} must not have full content stored"

        # If has_full_text is True, it must have verified content and public domain / traditional status
        if item.has_full_text:
            assert item.content is not None, f"Item {item.id} has_full_text=True but content is None"
            assert item.copyright_status in ("public_domain", "traditional_cultural_expression")


def test_top_level_functions():
    # search_literature
    results = search_literature("Khumpui")
    assert len(results) >= 1
    assert any("Khumpui" in r.title for r in results)

    # list_literature
    folks = list_literature(category="folklore")
    assert len(folks) > 0

    # get_literature
    item = get_literature("khumpui-legend")
    assert item.id == "khumpui-legend"

    # get_default_literature singleton
    lit = get_default_literature()
    assert isinstance(lit, KokborokLiterature)
