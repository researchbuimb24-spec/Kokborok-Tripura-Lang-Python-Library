# Kokborok Tripura Language Python Library

A reusable Python library for working with Kokborok (Tripuri) language text. The project supports text processing, dictionary lookup, verified phrase translation, and a literature and folklore catalog of authentic stories, books, poems, and proverbs.

## Features

- **Text Processing:** Clean and normalize Kokborok text, detect script (Latin / Eastern Nagari Bengali), tokenize words, analyze prefixes/suffixes, and strip tone markers.
- **Dictionary Lookup:** Fast bidirectional search (Kokborok ↔ English) with exact and substring matching, tone tolerance, and morphological stem-fallback.
- **Literature & Folklore Catalog:** Store, list, search, and retrieve authentic Kokborok folklores, legends, books, poems, and proverbs (*Kokbwkrai*) with legal and copyright safeguards.
- **Verified Translation:** Strict, non-hallucinating translation backend based on verified phrase pairings and pluggable neural models.
- **Automated Tests:** Comprehensive unit and integration test suite with high test coverage.

## Project Structure

```text
language_project/
├── examples/
│   ├── 01_quickstart.py
│   └── 02_literature_catalog.py
├── src/
│   └── tripura_translate/
│       ├── data/
│       │   ├── kokborok_dictionary.json
│       │   ├── kokborok_literature.json
│       │   └── verified_phrases.json
│       ├── dictionary.py
│       ├── exceptions.py
│       ├── literature.py
│       ├── text_processing.py
│       ├── translator.py
│       └── __init__.py
├── tests/
│   ├── test_api_integration.py
│   ├── test_dictionary.py
│   ├── test_literature.py
│   ├── test_text_processing.py
│   └── test_translator.py
├── pyproject.toml
├── .gitignore
└── README.md
```

## Requirements

- Python 3.8 or later (tested on Python 3.10, 3.11, 3.12, 3.13).
- Optional neural translation dependencies: `transformers`, `torch`, `sentencepiece`.
- Development / testing dependencies: `pytest`.

## Installation

Clone the repository and open the project directory:

```bash
git clone https://github.com/researchbuimb24-spec/Kokborok-Tripura-Lang-Python-Library.git
cd Kokborok-Tripura-Lang-Python-Library
```

Install the package in editable mode:

```bash
python -m pip install -e .
```

## Quick Start

### 1. Text Processing & Translation

```python
from tripura_translate import process_text, search_dictionary, translate

# Clean and tokenize Kokborok text
processed = process_text("  khulumkha ,  nwng bahai tong ? ")
print(processed["cleaned_text"])  # "khulumkha , nwng bahai tong ?"
print(processed["script"])        # "latin"
print(processed["tokens"])        # ["khulumkha", "nwng", "bahai", "tong"]

# Search dictionary
results = search_dictionary("water", exact=True)
print(results[0]["kokborok_latin"])  # "twi"

# Verified phrase translation
res = translate("Good morning", source_lang="en", target_lang="trp")
print(res.translated_text)  # "Phung kaham"
```

### 2. Literature and Folklore Catalog

The library includes authentic, curated records of traditional Kokborok oral literature (folktales, legends, proverbs, cradle songs) and published works (grammars, novels, poetry collections).

```python
from tripura_translate import (
    get_literature,
    list_literature,
    search_literature,
)

# List all traditional folklores
folklores = list_literature(category="folklore")
for f in folklores:
    print(f"{f.title} ({f.title_english}) - Source: {f.author_or_source}")

# Search by topic, author, or keyword
matches = search_literature("Murasingh")
for m in matches:
    print(f"{m.title} ({m.year}) - Citation: {m.format_citation()}")

# Retrieve full text of a public domain folktale
chethuang = get_literature("chethuang-kothoma")
print(chethuang.title)
print(chethuang.content)  # Full traditional narrative

# Retrieve traditional Kokborok proverbs (Kokbwkrai)
proverbs = get_literature("kokborok-kokbwkrai")
print(proverbs.content)
```

Run the runnable example scripts:

```bash
python examples/01_quickstart.py
python examples/02_literature_catalog.py
```

## Literature Catalog & Copyright Policy

The literature catalog adheres to strict ethical, academic, and legal cultural heritage guidelines:
- **Public Domain & Traditional Expressions:** Traditional oral folklores (such as *Chethuangni Kothoma*, *Khumpui*, *Nuwai Tok*, *Kuchuk Kherengbar*, *Baba Garia*), traditional cradle songs (*Uayingkhilimung*), and proverbs (*Kokbwkrai*) include verified narrative transcripts and cultural notes (`has_full_text=True`).
- **Modern Copyrighted Works:** 20th- and 21st-century published literature (e.g., works by Chandrakanta Murasingh, Pushpa Pai / CIIL, Binoy Debbarma, Bimal Sinha, Shefali Debbarma) are recorded strictly with bibliographic metadata, abstract summaries, and links to official cultural and academic institutions (`has_full_text=False`).
- **Authenticity Guarantee:** No folklore, vocabulary, translations, or historical sources are fabricated. Citations originate from documented, verifiable academic and institutional sources, including:
  - Faijul Hoque (2014), *"Kokborok: A Major Tribal Language of Tripura"*, *IOSR Journal of Humanities and Social Science (IOSR-JHSS)*.
  - Dr. Jagadis Gan-Choudhury (1985), *Folk-Tales of Tripura*, Directorate of Higher Education, Govt. of Tripura.
  - Pushpa Pai (1976), *Kokborok Grammar*, Central Institute of Indian Languages (CIIL), Mysore.
  - Thakur Radhamohan Debbarma (1900), *Kok-Borok-Ma*, Royal State Press, Agartala.
  - Directorate of Kokborok & Other Minority Languages, Government of Tripura (`kokborokoml.tripura.gov.in`).
  - Tripura Tribal Areas Autonomous District Council (TTAADC, `ttaadc.gov.in`).
  - Sahitya Akademi (National Academy of Letters, India).


## Running Tests

Run the complete automated test suite using `pytest`:

```bash
python -m pytest
```

All 74 test cases (covering API integration, text processing, dictionary, literature catalog, and translation) will execute.

## Contributing

Contributions that expand verified literature references, improve grammar and translation coverage, or enrich Kokborok language documentation are welcome. Please ensure that all contributions respect copyright and include genuine institutional references.

## License

This project is licensed under the MIT License. Traditional cultural expressions remain the cultural heritage of the Borok (Tripuri) community.
