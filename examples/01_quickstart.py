"""Quickstart example for the tripura-translate library.

This example demonstrates the 3 core functions:
1. process_text()
2. search_dictionary()
3. translate()
"""

from tripura_translate import (
    process_text,
    search_dictionary,
    translate,
)


def main():
    print("=" * 60)
    print("tripura-translate: Quickstart Demo (Kokborok / Tripuri)")
    print("=" * 60)

    # 1. Text Processing
    sample_text = "  Khulumkha ,  nwng bahai tong ? "
    print("\n1. Text Processing:")
    print(f"Raw Input: '{sample_text}'")
    processed = process_text(sample_text)
    print(f"Cleaned Text : '{processed['cleaned_text']}'")
    print(f"Script       : {processed['script']}")
    print(f"Word Count   : {processed['word_count']}")
    print(f"Tokens       : {processed['tokens']}")

    # 2. Dictionary Search
    print("\n2. Dictionary Search:")
    query = "water"
    print(f"Searching dictionary for English word: '{query}'")
    results = search_dictionary(query, exact=True)
    for entry in results:
        print(f"  -> Kokborok (Latin)   : {entry['kokborok_latin']}")
        print(f"  -> Kokborok (Bengali) : {entry.get('kokborok_bengali')}")
        print(f"  -> Meaning            : {entry['english']}")
        print(f"  -> Category           : {entry['category']}")
        print(f"  -> Example            : {entry['example_kokborok']} ({entry['example_english']})")

    # 3. Verified Translation (Bidirectional)
    print("\n3. Verified Translation:")
    # English -> Kokborok
    eng_text = "Good morning"
    res1 = translate(eng_text, source_lang="en", target_lang="trp")
    print(f"English: '{eng_text}' -> Kokborok: '{res1.translated_text}' (Backend: {res1.backend})")

    # Kokborok -> English
    kb_text = "Hambai"
    res2 = translate(kb_text, source_lang="trp", target_lang="en")
    print(f"Kokborok: '{kb_text}' -> English: '{res2.translated_text}' (Backend: {res2.backend})")

    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
