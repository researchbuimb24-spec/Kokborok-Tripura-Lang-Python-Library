"""Unit and integration tests for the Kokborok Language Basics module."""

import json
from pathlib import Path
import pytest

from tripura_translate import (
    EmptyInputError,
    GrammarTopicNotFoundError,
    KokborokLanguageBasics,
    LanguageBasicsError,
    TripuraTranslateError,
    get_alphabet,
    get_basic_phrases,
    get_default_language_basics,
    get_grammar_topic,
    get_language_sources,
    list_grammar_topics,
    list_vocabulary_categories,
    search_vocabulary,
)


class TestAlphabetAndPronunciation:
    def test_get_alphabet_structure(self):
        alphabet = get_alphabet()
        assert isinstance(alphabet, dict)
        assert "language" in alphabet
        assert "scripts" in alphabet
        assert "vowels" in alphabet
        assert "diphthongs" in alphabet
        assert "consonants" in alphabet
        assert "tone_system" in alphabet

        # Verify scripts
        script_names = [s["name"] for s in alphabet["scripts"]]
        assert any("Latin" in name for name in script_names)
        assert any("Bengali" in name or "Eastern Nagari" in name for name in script_names)

    def test_vowels_include_w_phoneme(self):
        alphabet = get_alphabet()
        vowels = alphabet["vowels"]
        assert len(vowels) >= 6

        # Check for characteristic Kokborok vowel 'w' (/ɨ/)
        w_vowel = next((v for v in vowels if v["letter"] == "w"), None)
        assert w_vowel is not None
        assert "/ɨ/" in w_vowel["ipa"] or "/ɯ/" in w_vowel["ipa"]
        assert "central" in w_vowel["articulatory_description"].lower()
        assert len(w_vowel["examples"]) >= 3

        example_words = [ex["kokborok"] for ex in w_vowel["examples"]]
        assert "twi" in example_words
        assert "nwng" in example_words
        assert "swi" in example_words

    def test_diphthongs(self):
        alphabet = get_alphabet()
        diphthongs = alphabet["diphthongs"]
        combinations = [d["combination"] for d in diphthongs]
        assert any("ai" in c for c in combinations)
        assert any("ui" in c for c in combinations)
        assert any("wi" in c for c in combinations)
        assert any("ya" in c for c in combinations)

    def test_tone_system(self):
        alphabet = get_alphabet()
        tone_sys = alphabet["tone_system"]
        assert tone_sys["tonal_language"] is True
        assert tone_sys["number_of_tones"] == 2
        tones = tone_sys["tones"]
        assert len(tones) == 2
        tone_names = [t["name"] for t in tones]
        assert any("Level" in n or "Low" in n for n in tone_names)
        assert any("High" in n or "Falling" in n for n in tone_names)

    def test_consonants(self):
        alphabet = get_alphabet()
        consonants = alphabet["consonants"]
        letters = [c["letter"] for c in consonants]
        # Check standard Kokborok phonemic stops and affricates
        for char in ("p", "ph", "b", "t", "th", "d", "k", "kh", "g", "ch", "j", "s", "h", "m", "n", "ng", "r", "l", "y"):
            assert char in letters, f"Consonant '{char}' missing from inventory"


class TestVocabularySearch:
    def test_search_exact_match(self):
        results = search_vocabulary("water")
        assert len(results) >= 1
        assert results[0]["kokborok_latin"] == "twi"
        assert results[0]["english"] == "water"
        assert results[0]["verified"] is True

        kb_results = search_vocabulary("twi")
        assert len(kb_results) >= 1
        assert kb_results[0]["english"] == "water"

    def test_search_case_insensitive(self):
        res_lower = search_vocabulary("hello")
        res_upper = search_vocabulary("HELLO")
        res_mixed = search_vocabulary("Hello")
        assert len(res_lower) == len(res_upper) == len(res_mixed)
        assert res_lower[0]["kokborok_latin"] == "khulumkha"

    def test_search_substring(self):
        results = search_vocabulary("thank")
        assert len(results) >= 2
        meanings = [r["english"].lower() for r in results]
        assert any("thank you" in m for m in meanings)
        assert any("thank you very much" in m for m in meanings)

    def test_search_with_category_filter(self):
        greetings = search_vocabulary("kha", category="greetings")
        assert len(greetings) >= 1
        assert all(entry["category"] == "greetings" for entry in greetings)

        # Non-matching category
        food_match = search_vocabulary("khulumkha", category="food_and_daily_life")
        assert len(food_match) == 0

    def test_search_no_match(self):
        results = search_vocabulary("non_existent_xyz_word")
        assert results == []

    def test_search_empty_input_raises_error(self):
        with pytest.raises(EmptyInputError):
            search_vocabulary("")
        with pytest.raises(EmptyInputError):
            search_vocabulary("   \t\n  ")

    def test_list_vocabulary_categories(self):
        categories = list_vocabulary_categories()
        assert len(categories) >= 7
        expected = [
            "greetings",
            "numbers",
            "family",
            "colors",
            "food_and_daily_life",
            "people_and_places",
            "verbs",
            "adjectives",
        ]
        for exp in expected:
            assert exp in categories, f"Category '{exp}' missing from list_vocabulary_categories"

    def test_all_vocabulary_entries_have_required_metadata(self):
        basics = get_default_language_basics()
        for entry in basics._vocabulary:
            assert entry.get("kokborok_latin"), "Missing kokborok_latin"
            assert entry.get("english"), "Missing english"
            assert entry.get("category"), "Missing category"
            assert entry.get("source"), "Missing source citation"
            assert entry.get("verified") is True, "Entry must be marked verified"
            assert entry.get("example_kokborok"), "Missing Kokborok example"
            assert entry.get("example_english"), "Missing English example translation"


class TestGrammarTopics:
    def test_list_grammar_topics(self):
        topics = list_grammar_topics()
        assert len(topics) == 9
        expected_topics = [
            "pronouns",
            "nouns_and_plurals",
            "verbs_and_patterns",
            "tense_and_aspect",
            "negation",
            "questions",
            "sentence_structure",
            "postpositions",
            "sentence_construction",
        ]
        for t in expected_topics:
            assert t in topics, f"Grammar topic '{t}' missing from list_grammar_topics"

    @pytest.mark.parametrize(
        "topic_id",
        [
            "pronouns",
            "nouns_and_plurals",
            "verbs_and_patterns",
            "tense_and_aspect",
            "negation",
            "questions",
            "sentence_structure",
            "postpositions",
            "sentence_construction",
        ],
    )
    def test_get_grammar_topic_success(self, topic_id: str):
        topic = get_grammar_topic(topic_id)
        assert isinstance(topic, dict)
        assert topic["topic_id"] == topic_id
        assert topic["title"], "Topic title must not be empty"
        assert topic["kokborok_term"], "Kokborok term must not be empty"
        assert topic["summary"], "Topic summary must not be empty"
        assert len(topic["rules"]) >= 2, "Topic must contain at least 2 structured rules"
        assert len(topic["authentic_examples"]) >= 2, "Topic must contain at least 2 authentic examples"
        assert len(topic["source_references"]) >= 1, "Topic must cite at least one reference"

        # Check authentic examples have breakdowns and sources
        for ex in topic["authentic_examples"]:
            assert ex.get("kokborok"), "Example must have Kokborok text"
            assert ex.get("english"), "Example must have English translation"
            assert ex.get("breakdown"), "Example must have grammatical breakdown"
            assert ex.get("source"), "Example must have authentic source citation"

    def test_topic_aliases(self):
        # Alias 'pronoun' -> 'pronouns'
        p1 = get_grammar_topic("pronoun")
        p2 = get_grammar_topic("pronouns")
        assert p1["topic_id"] == p2["topic_id"] == "pronouns"

        # Alias 'verbs' -> 'verbs_and_patterns'
        v = get_grammar_topic("verbs")
        assert v["topic_id"] == "verbs_and_patterns"

        # Alias 'tense' -> 'tense_and_aspect'
        t = get_grammar_topic("tense")
        assert t["topic_id"] == "tense_and_aspect"

        # Alias 'word_order' -> 'sentence_structure'
        s = get_grammar_topic("word_order")
        assert s["topic_id"] == "sentence_structure"

    def test_get_grammar_topic_missing_raises_error(self):
        with pytest.raises(GrammarTopicNotFoundError) as exc_info:
            get_grammar_topic("quantum_linguistics")
        assert "quantum_linguistics" in str(exc_info.value)
        assert issubclass(GrammarTopicNotFoundError, LanguageBasicsError)
        assert issubclass(LanguageBasicsError, TripuraTranslateError)
        assert exc_info.value.available_topics

    def test_get_grammar_topic_empty_raises_error(self):
        with pytest.raises(EmptyInputError):
            get_grammar_topic("")
        with pytest.raises(EmptyInputError):
            get_grammar_topic("   \t  ")


class TestBasicPhrases:
    def test_get_all_phrases(self):
        phrases = get_basic_phrases()
        assert isinstance(phrases, list)
        assert len(phrases) >= 12
        for phrase in phrases:
            assert phrase.get("kokborok"), "Phrase must have Kokborok text"
            assert phrase.get("english"), "Phrase must have English translation"
            assert phrase.get("category"), "Phrase must have category"
            assert phrase.get("source"), "Phrase must have source"
            assert phrase.get("literal_breakdown"), "Phrase must have literal breakdown"

    def test_get_phrases_by_category(self):
        greetings = get_basic_phrases(category="greetings")
        assert len(greetings) >= 3
        assert all(p["category"] == "greetings" for p in greetings)

        polite = get_basic_phrases(category="polite_expressions")
        assert len(polite) >= 3
        assert all(p["category"] == "polite_expressions" for p in polite)

        questions = get_basic_phrases(category="questions")
        assert len(questions) >= 3
        assert all(p["category"] == "questions" for p in questions)

        empty_category = get_basic_phrases(category="non_existent_category")
        assert empty_category == []


class TestLanguageSourcesMetadata:
    def test_get_language_sources(self):
        sources = get_language_sources()
        assert isinstance(sources, list)
        assert len(sources) >= 5

        source_ids = [s["id"] for s in sources]
        assert "karapurkar_1976_grammar" in source_ids
        assert "karapurkar_1972_phonetic_reader" in source_ids
        assert "pandey_2018_learners_dict" in source_ids
        assert "tripura_school_primers_adivaani" in source_ids
        assert "cbse_kokborok_syllabus_2024_25" in source_ids

    def test_sources_accessibility_status_documented(self):
        sources = get_language_sources()
        for source in sources:
            assert "accessibility_status" in source, f"Source {source['id']} lacks accessibility_status"
            assert "accessible_content_notes" in source, f"Source {source['id']} lacks accessible_content_notes"
            assert "reference_url" in source, f"Source {source['id']} lacks reference_url"
            assert len(source.get("verified_topics", [])) > 0, f"Source {source['id']} has no verified_topics"

            # Check that Google Books catalog snippet status is explicitly marked
            if source["id"] == "karapurkar_1976_grammar":
                assert source["accessibility_status"] == "partially_accessible_metadata_and_citations"
                assert "snippet" in source["accessible_content_notes"].lower()

            # Check that Adivaani primers are marked accessible
            if source["id"] == "tripura_school_primers_adivaani":
                assert "accessible" in source["accessibility_status"].lower()
                assert "adivaani" in source["reference_url"].lower()


class TestUnicodeAndScriptIntegrity:
    def test_vocabulary_unicode_characters(self):
        results = search_vocabulary("hello")
        entry = results[0]
        # Bengali script presence
        assert entry["kokborok_bengali"] == "খুলুমখা"
        assert entry["kokborok_latin"] == "khulumkha"

        # Water entry
        twi_results = search_vocabulary("water")
        twi_entry = twi_results[0]
        assert twi_entry["kokborok_bengali"] == "তুই"
        assert twi_entry["kokborok_latin"] == "twi"

    def test_phrases_unicode_characters(self):
        phrases = get_basic_phrases(category="greetings")
        hello = next(p for p in phrases if p["id"] == "phrase_hello")
        assert hello["kokborok_bengali"] == "খুলুমখা"
        assert hello["kokborok"] == "Khulumkha"


class TestCustomPathAndErrors:
    def test_custom_dir_missing(self, tmp_path: Path):
        missing_dir = tmp_path / "non_existent_dir"
        with pytest.raises(FileNotFoundError):
            KokborokLanguageBasics(missing_dir)

    def test_custom_dir_corrupt_json(self, tmp_path: Path):
        bad_dir = tmp_path / "bad_data"
        bad_dir.mkdir()
        bad_file = bad_dir / "alphabet.json"
        bad_file.write_text("{\"invalid\": \"not complete\"}", encoding="utf-8")
        # Missing other files
        with pytest.raises(FileNotFoundError):
            KokborokLanguageBasics(bad_dir)

    def test_custom_dir_invalid_type(self, tmp_path: Path):
        custom_dir = tmp_path / "custom"
        custom_dir.mkdir()
        # Write alphabet as list instead of dict
        (custom_dir / "alphabet.json").write_text("[]", encoding="utf-8")
        with pytest.raises(ValueError, match="expected JSON object"):
            KokborokLanguageBasics(custom_dir)


class TestTopLevelApiIntegration:
    def test_singleton_consistency(self):
        inst1 = get_default_language_basics()
        inst2 = get_default_language_basics()
        assert inst1 is inst2
        assert inst1.total_vocabulary > 0
        assert inst1.total_grammar_topics == 9
        assert inst1.total_phrases > 0
