"""Example script demonstrating Kokborok literature and folklore cataloging.

This script illustrates:
1. Listing available categories and authors.
2. Searching for folklores, traditional tales, and books.
3. Reading verified full text for public domain / traditional oral lore.
4. Viewing metadata, citations, and official links for copyrighted modern books.
"""

import sys
from tripura_translate import (
    get_literature,
    list_literature,
    search_literature,
)

# Ensure proper Unicode output on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main():

    print("=" * 70)
    print("tripura-translate: Kokborok Literature & Folklore Catalog Demo")
    print("=" * 70)

    # 1. List folklores
    print("\n1. Traditional Folklores and Tales:")
    folklores = list_literature(category="folklore")
    for item in folklores:
        print(f"  [{item.id}] {item.title}")
        print(f"      Source: {item.author_or_source}")
        print(f"      Full Text Available: {item.has_full_text}")

    # 2. Search for a specific folklore and display content
    print("\n2. Retrieving Full Text for 'Chethuangni Kothoma':")
    chethuang = get_literature("chethuang-kothoma")
    print(f"Title     : {chethuang.title} ({chethuang.title_english})")
    print(f"Source    : {chethuang.author_or_source}")
    print(f"Institution: {chethuang.source_institution}")
    print(f"Summary   : {chethuang.summary[:120]}...")
    print("\n--- Story Excerpt ---")
    print(chethuang.content[:350] + "...\n---------------------")

    # 3. Traditional Proverbs (Kokbwkrai)
    print("\n3. Kokborok Proverbs (Kokbwkrai):")
    proverbs_item = get_literature("kokborok-kokbwkrai")
    print(proverbs_item.content)

    # 4. Search modern and historical books
    print("\n4. Searching Literature for 'Murasingh':")
    results = search_literature("Murasingh")
    for r in results:
        print(f"  -> {r.title} ({r.year or 'N/A'}) by {r.author_or_source}")
        print(f"     Category: {r.category} | Status: {r.copyright_status}")
        print(f"     Citation: {r.format_citation()}")
        print(f"     Source Link: {r.source_links[0] if r.source_links else 'N/A'}")

    print("\n" + "=" * 70)
    print("Literature demo completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
