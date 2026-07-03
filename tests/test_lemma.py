# -*- coding: utf-8 -*-
"""Regressionstests für den ausgebauten deutschen Lemmatizer."""
import pytest
from goauld_engine.lemma import de_lemma_candidates


@pytest.mark.parametrize("form,lemma", [
    # regelmäßig: -et, -ern/-eln, Präteritum, Partizip II, Imperativ
    ("findet", "finden"), ("wartet", "warten"), ("arbeitet", "arbeiten"),
    ("opfert", "opfern"), ("lauert", "lauern"), ("sammelt", "sammeln"),
    ("opferte", "opfern"), ("geopfert", "opfern"), ("gearbeitet", "arbeiten"),
    ("kämpfe", "kämpfen"), ("kämpften", "kämpfen"),
    # stark: 3sg / Präteritum / Partizip / Plural-Präteritum / du-Form
    ("gibt", "geben"), ("gibst", "geben"), ("gab", "geben"),
    ("gaben", "geben"), ("gegeben", "geben"),
    ("stirbt", "sterben"), ("starb", "sterben"), ("gestorben", "sterben"),
    ("trägt", "tragen"), ("trug", "tragen"), ("schwor", "schwören"),
    ("geschworen", "schwören"), ("flohen", "fliehen"), ("fand", "finden"),
    # Präfixverben
    ("verrät", "verraten"), ("verlor", "verlieren"), ("verloren", "verlieren"),
    ("erobert", "erobern"), ("zerbrach", "zerbrechen"),
    ("aufgebaut", "aufbauen"), ("angegriffen", "angreifen"),
    # Digraph-Varianten für Alt-Glossen
    ("schwöre", "schwoeren"), ("schlüssel", "schluessel"), ("schön", "schoen"),
    # Nomen/Adjektiv
    ("feinden", "feind"), ("waffen", "waffe"), ("königinnen", "königin"),
    ("stärkste", "stark"),
])
def test_de_lemma(form, lemma):
    assert lemma in de_lemma_candidates(form)


def test_erste_position_ist_originalform():
    assert de_lemma_candidates("Opfert")[0] == "opfert"
