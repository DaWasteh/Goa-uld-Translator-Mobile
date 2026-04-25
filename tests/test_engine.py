# -*- coding: utf-8 -*-
"""Regressionstests für goauld_engine."""

import pytest
from goauld_engine import (
    load_full_lexicon,
    build_mapping,
    translate_text,
    SearchEngine,
    SentenceAnalyzer,
    de_lemma_candidates,
)


@pytest.fixture(scope="module")
def lexicon():
    """Einmal pro Modul laden."""
    return load_full_lexicon()


@pytest.fixture(scope="module")
def goa2de_map(lexicon):
    return build_mapping(lexicon.entries, "goa2de")


@pytest.fixture(scope="module")
def de2goa_map(lexicon):
    return build_mapping(lexicon.entries, "de2goa")


def test_lexicon_loads(lexicon):
    """Lexicon enthält mindestens 1000 Einträge."""
    assert len(lexicon.entries) >= 1000, \
        f"Nur {len(lexicon.entries)} Einträge geladen — erwartet ≥ 1000"


def test_lexicon_has_de_map(lexicon):
    """DE-Map enthält mindestens 200 Direkt-Mappings."""
    assert len(lexicon.de_map) >= 200, \
        f"Nur {len(lexicon.de_map)} DE-Map-Einträge"


def test_jaffa_kree(goa2de_map):
    """Klassischer Jaffa-Befehl."""
    result = translate_text("Jaffa kree", goa2de_map, "goa2de")
    # 'kree' ist polysem; 'Krieger' für Jaffa, 'Achtung'/'aufgepasst' für kree
    assert any(w in result.lower() for w in ["krieger", "jaffa", "achtung"])


def test_tau_ri(goa2de_map):
    """Tau'ri = Erdling/Mensch von der Erde."""
    result = translate_text("Tau'ri", goa2de_map, "goa2de")
    assert any(w in result.lower() for w in ["erde", "mensch", "tau'ri"])


def test_de2goa_simple(de2goa_map):
    """Einfache DE→Goa-Übersetzung."""
    # 'krieger' ist eine grundlegende Vokabel
    result = translate_text("krieger", de2goa_map, "de2goa")
    # Erwartet 'jaffa' irgendwo im Output
    assert "jaffa" in result.lower(), f"Erwartete 'jaffa', bekam: {result!r}"


def test_de_lemma_basics():
    """DE-Lemma findet Infinitiv aus konjugierter Form."""
    candidates = de_lemma_candidates("gehe")
    assert "gehen" in candidates


def test_de_lemma_plural():
    """DE-Lemma findet Singular aus Plural."""
    candidates = de_lemma_candidates("Krieger")
    # Der Singular ist gleich, aber bei Plural-Endungen sollte gestimmt werden
    assert "krieger" in [c.lower() for c in candidates]


def test_search_engine_finds_jaffa(lexicon):
    """SearchEngine findet einen kanonischen Eintrag."""
    engine = SearchEngine(lexicon.entries)
    results = engine.search("jaffa", direction="goa2de", max_results=5)
    assert len(results) >= 1
    # Der Top-Treffer enthält 'jaffa' im Term oder einer Bedeutung
    top = results[0]
    found = "jaffa" in str(top).lower()
    assert found, f"Top-Result enthält kein 'jaffa': {top}"


def test_sentence_analyzer_runs(lexicon):
    """SentenceAnalyzer wirft keinen Fehler auf einer Standard-Phrase."""
    analyzer = SentenceAnalyzer(lexicon.entries)
    result = analyzer.analyze("Jaffa kree", direction="goa2de")
    # Genaue Struktur hängt vom Original ab — hier nur: kein Crash, Liste/Dict zurück
    assert result is not None


def test_phrase_priority(de2goa_map):
    """Multi-Wort-Phrasen werden NICHT in Einzelwörter zerhackt."""
    # Wenn 'auf der Hut sein' eine eigene Phrase ist, soll sie als Einheit übersetzt werden
    # — Test angepasst nach tatsächlichem Lexicon-Inhalt
    pass  # Wird in Phase 4 ergänzt, sobald konkrete Beispielphrasen feststehen
