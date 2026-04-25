# -*- coding: utf-8 -*-
"""
Goa'uld lexicon loader — YAML-first with Markdown fallback.

This module replicates the ``_load_lexicon()`` function from the original
``goa'uld_translator.py`` (lines 1250–1283) and adds the embedded
gap-filling vocabulary (lines 1341–1403).

Returns a ``LexiconResult`` dataclass that the rest of the engine consumes.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .parser import parse_de_map_from_entries, parse_markdown_dictionary
from .resources import find_md_files, get_app_dir
from .translator import DE_GOAULD_MAP

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional YAML loader import (like the original)
# ---------------------------------------------------------------------------
try:
    from . import yaml_loader
    YAML_LOADER_AVAILABLE = True
    find_lexicon_yaml = yaml_loader.find_lexicon_yaml
    load_lexicon_yaml = yaml_loader.load_lexicon_yaml
except (ImportError, AttributeError):
    YAML_LOADER_AVAILABLE = False

# ---------------------------------------------------------------------------
# Gap-fill vocabulary (verbatim from original lines 1341–1403)
# ---------------------------------------------------------------------------
_GAP_FILL: list[dict] = [
    # FIX 2 (translation-bugs-findings.md): "mensch" → "tau'ri" (kanonisch SG1)
    # Diese Einträge haben höchste Priorität (SG1-Kanon) und überschreiben
    # sekundäre Quellen wie Fictionary/Neologikum (tap'tar).
    {"goauld": "tau'ri",   "meaning": "mensch",           "section": "Gap-Fill", "source": "SG1-Kanon", "lang": "de", "de_map": True},
    {"goauld": "tau'ri",   "meaning": "menschen",         "section": "Gap-Fill", "source": "SG1-Kanon", "lang": "de", "de_map": True},
    {"goauld": "tau'ri",   "meaning": "human",            "section": "Gap-Fill", "source": "SG1-Kanon", "lang": "en", "de_map": False},
    {"goauld": "tau'ri",   "meaning": "humans",           "section": "Gap-Fill", "source": "SG1-Kanon", "lang": "en", "de_map": False},
    # Verwandtschaft / Family
    {"goauld": "shel'c",   "meaning": "Bruder",          "section": "Gap-Fill", "source": "Fanon/RPG", "lang": "de", "de_map": True},
    {"goauld": "shel'ca",  "meaning": "Schwester",        "section": "Gap-Fill", "source": "Fanon/RPG", "lang": "de", "de_map": True},
    {"goauld": "tel'mak",  "meaning": "Vater",            "section": "Gap-Fill", "source": "Fanon/RPG", "lang": "de", "de_map": True},
    {"goauld": "tel'ma",   "meaning": "Mutter",           "section": "Gap-Fill", "source": "Fanon/RPG", "lang": "de", "de_map": True},
    {"goauld": "shol'va",  "meaning": "Sohn",             "section": "Gap-Fill", "source": "Fanon",     "lang": "de", "de_map": True},
    {"goauld": "kresh'ta", "meaning": "Tochter",          "section": "Gap-Fill", "source": "Fanon",     "lang": "de", "de_map": True},
    # Gefühle / Emotions
    {"goauld": "pal",      "meaning": "Liebe",            "section": "Gap-Fill", "source": "Kanon-ext", "lang": "de", "de_map": True},
    {"goauld": "pal",      "meaning": "Herz",             "section": "Gap-Fill", "source": "Kanon-ext", "lang": "de", "de_map": True},
    {"goauld": "shal tek", "meaning": "Stolz",            "section": "Gap-Fill", "source": "Kanon-ext", "lang": "de", "de_map": True},
    {"goauld": "nel nem ron","meaning": "Frieden",        "section": "Gap-Fill", "source": "Kanon-ext", "lang": "de", "de_map": True},
    {"goauld": "mak shel", "meaning": "Treue",            "section": "Gap-Fill", "source": "Kanon-ext", "lang": "de", "de_map": True},
    # Handlungen / Verben
    {"goauld": "kree",     "meaning": "gehen",            "section": "Gap-Fill", "source": "Kanon-ext", "lang": "de", "de_map": True},
    {"goauld": "kel",      "meaning": "kommen",           "section": "Gap-Fill", "source": "Fanon",     "lang": "de", "de_map": True},
    {"goauld": "hol",      "meaning": "halten",           "section": "Gap-Fill", "source": "Kanon-ext", "lang": "de", "de_map": True},
    {"goauld": "tel",      "meaning": "sehen",            "section": "Gap-Fill", "source": "Fanon",     "lang": "de", "de_map": True},
    {"goauld": "nok",      "meaning": "wissen",           "section": "Gap-Fill", "source": "Kanon-ext", "lang": "de", "de_map": True},
    {"goauld": "shree",    "meaning": "eindringen",       "section": "Gap-Fill", "source": "Kanon-ext", "lang": "de", "de_map": True},
    {"goauld": "tak",      "meaning": "täuschen",         "section": "Gap-Fill", "source": "Kanon-ext", "lang": "de", "de_map": True},
    # FIX Problem 2 (translation-bugs-findings.md): "stirb" → "mel", "vernichten" → "mol kek"
    {"goauld": "mel",      "meaning": "sterbe",           "section": "Gap-Fill", "source": "SG1-Kanon", "lang": "de", "de_map": True},
    {"goauld": "mel",      "meaning": "stirb",            "section": "Gap-Fill", "source": "SG1-Kanon", "lang": "de", "de_map": True},
    {"goauld": "mel",      "meaning": "sterben",          "section": "Gap-Fill", "source": "SG1-Kanon", "lang": "de", "de_map": True},
    {"goauld": "mol kek",  "meaning": "vernichten",       "section": "Gap-Fill", "source": "SG1-Kanon", "lang": "de", "de_map": True},
    {"goauld": "mol kek",  "meaning": "vernichtet",       "section": "Gap-Fill", "source": "SG1-Kanon", "lang": "de", "de_map": True},
    {"goauld": "kek",      "meaning": "sterben",          "section": "Gap-Fill", "source": "Kanon-ext", "lang": "de", "de_map": True},
    {"goauld": "tac",      "meaning": "kämpfen",          "section": "Gap-Fill", "source": "Fanon",     "lang": "de", "de_map": True},
    {"goauld": "kalach",   "meaning": "schützen",         "section": "Gap-Fill", "source": "Kanon-ext", "lang": "de", "de_map": True},
    {"goauld": "mol kek",  "meaning": "zerstören",        "section": "Gap-Fill", "source": "Kanon-ext", "lang": "de", "de_map": True},
    # Adjektive / Eigenschaften
    {"goauld": "tal",      "meaning": "groß",             "section": "Gap-Fill", "source": "Fanon",     "lang": "de", "de_map": True},
    {"goauld": "teal'c",   "meaning": "stark",            "section": "Gap-Fill", "source": "Kanon",     "lang": "de", "de_map": True},
    {"goauld": "teal'c",   "meaning": "Stärke",           "section": "Gap-Fill", "source": "Kanon",     "lang": "de", "de_map": True},
    {"goauld": "nokia",    "meaning": "neu",              "section": "Gap-Fill", "source": "Kanon-ext", "lang": "de", "de_map": True},
    {"goauld": "shel",     "meaning": "frei",             "section": "Gap-Fill", "source": "Fanon",     "lang": "de", "de_map": True},
    {"goauld": "kek",      "meaning": "schwach",          "section": "Gap-Fill", "source": "Kanon-ext", "lang": "de", "de_map": True},
    {"goauld": "onak",     "meaning": "alle",             "section": "Gap-Fill", "source": "Kanon-ext", "lang": "de", "de_map": True},
    # Technologie / Schiffe
    {"goauld": "ha'tak",   "meaning": "Raumschiff",       "section": "Gap-Fill", "source": "Kanon-ext", "lang": "de", "de_map": True},
    {"goauld": "ha'tak",   "meaning": "Schiff",           "section": "Gap-Fill", "source": "Kanon-ext", "lang": "de", "de_map": True},
    {"goauld": "ha'tak",   "meaning": "Kriegsschiff",     "section": "Gap-Fill", "source": "Kanon-ext", "lang": "de", "de_map": True},
    {"goauld": "tel'tak",  "meaning": "Frachtschiff",     "section": "Gap-Fill", "source": "Kanon",     "lang": "de", "de_map": True},
    {"goauld": "udajeet",  "meaning": "Jäger",            "section": "Gap-Fill", "source": "Kanon",     "lang": "de", "de_map": True},
    # Orte / Substantive
    {"goauld": "a'roush",  "meaning": "Heimat",           "section": "Gap-Fill", "source": "Kanon-ext", "lang": "de", "de_map": True},
    {"goauld": "nel",      "meaning": "Weg",              "section": "Gap-Fill", "source": "Fanon",     "lang": "de", "de_map": True},
    {"goauld": "ring",     "meaning": "Tor",              "section": "Gap-Fill", "source": "Fanon",     "lang": "de", "de_map": True},
    {"goauld": "kel'sha",  "meaning": "Welt",             "section": "Gap-Fill", "source": "Fanon",     "lang": "de", "de_map": True},
    {"goauld": "onak",     "meaning": "Macht",            "section": "Gap-Fill", "source": "Kanon-ext", "lang": "de", "de_map": True},
    {"goauld": "shal tek", "meaning": "Ehre",             "section": "Gap-Fill", "source": "Kanon",     "lang": "de", "de_map": True},
    {"goauld": "kel mar",  "meaning": "Rache",            "section": "Gap-Fill", "source": "Kanon",     "lang": "de", "de_map": True},
    {"goauld": "kalach",   "meaning": "heilig",           "section": "Gap-Fill", "source": "Kanon-ext", "lang": "de", "de_map": True},
]


# ---------------------------------------------------------------------------
# LexiconResult dataclass
# ---------------------------------------------------------------------------
@dataclass
class LexiconResult:
    """Result of loading the full lexicon."""
    entries: list[dict]
    found_paths: list[str]
    de_map: dict[str, str]
    en_map: dict[str, str]
    secondary_de: dict[str, list[str]]
    secondary_en: dict[str, list[str]]
    source: str  # "yaml" or "markdown"


# ---------------------------------------------------------------------------
# Main loader
# ---------------------------------------------------------------------------
def load_full_lexicon(
    hint_en: Optional[str] = None,
    hint_de: Optional[str] = None,
) -> LexiconResult:
    """
    Bevorzugter Loader: versucht zuerst goauld_lexicon.yaml, fällt bei
    Fehlen auf die vier MD-Dateien zurück.

    Returns a ``LexiconResult`` with:
      - entries: flat list of dicts (goauld, meaning, section, source, lang, …)
      - found_paths: list of file paths that were loaded
      - de_map: German → Goa'uld primary lookup
      - en_map: English → Goa'uld primary lookup
      - secondary_de: German alternatives for polysemous words
      - secondary_en: English alternatives for polysemous words
      - source: "yaml" or "markdown"
    """
    # Reset DE_GOAULD_MAP before loading (FIX P4a from original)
    DE_GOAULD_MAP.clear()

    # YAML-first approach
    if YAML_LOADER_AVAILABLE:
        # Search directories: app dir, then _MEIPASS if frozen
        search_dirs: list = [get_app_dir()]
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            search_dirs.append(Path(meipass))

        yaml_path = find_lexicon_yaml(search_dirs=search_dirs)
        if yaml_path:
            entries, de_map, en_map, sec_de, sec_en = load_lexicon_yaml(yaml_path)
            # Populate DE_GOAULD_MAP from YAML primary map
            DE_GOAULD_MAP.update({k: v.lower() for k, v in de_map.items()})
            log.info("Lexicon loaded from YAML: %s (%d entries)",
                     yaml_path, len(entries))
            return LexiconResult(
                entries=entries,
                found_paths=[yaml_path],
                de_map=de_map,
                en_map=en_map,
                secondary_de=sec_de,
                secondary_en=sec_en,
                source="yaml",
            )

    # Markdown fallback
    entries, paths = _load_mds(hint_en, hint_de)
    return LexiconResult(
        entries=entries,
        found_paths=paths,
        de_map=dict(DE_GOAULD_MAP),
        en_map={},
        secondary_de={},
        secondary_en={},
        source="markdown",
    )


def _load_mds(
    hint_en: Optional[str] = None,
    hint_de: Optional[str] = None,
) -> tuple[list[dict], list[str]]:
    """
    Lädt EN- und DE-Wörterbuchdateien, gibt (alle_eintraege, gefundene_pfade) zurück.
    Befüllt außerdem das globale DE_GOAULD_MAP aus der DE-Datei.
    """
    all_entries: list[dict] = []
    found_paths: list[str] = []

    en_paths, de_paths = find_md_files(hint_en, hint_de)

    # EN-Dateien (Dictionary + Fictionary + ...)
    if en_paths:
        for en_path in en_paths:
            entries = parse_markdown_dictionary(en_path)
            if entries:
                all_entries += [{**e, "lang": "en"} for e in entries]
                found_paths.append(en_path)
                log.info("EN-Wörterbuch geladen: %s  (%d Einträge)",
                         Path(en_path).name, len(entries))
            else:
                log.warning("Keine Einträge in EN-Datei: %s", en_path)
    else:
        log.info("Kein EN-Wörterbuch gefunden.")

    # DE-Dateien (Wörterbuch + Neologikum + ...)
    if de_paths:
        for de_path in de_paths:
            entries = parse_markdown_dictionary(de_path)
            if entries:
                all_entries += [{**e, "lang": "de"} for e in entries]
                found_paths.append(de_path)
                new_map = parse_de_map_from_entries([{**e, "lang": "de"} for e in entries])
                for k, v in new_map.items():
                    if k not in DE_GOAULD_MAP:
                        DE_GOAULD_MAP[k] = v
                regular = sum(1 for e in entries if not e.get("de_map"))
                map_cnt = len(new_map)
                log.info("DE-Wörterbuch geladen: %s  (%d Einträge, %d DE→Goa'uld-Mappings)",
                         Path(de_path).name, regular, map_cnt)
            else:
                log.warning("Keine Einträge in DE-Datei: %s", de_path)
    else:
        log.info("Kein DE-Wörterbuch gefunden.")

    # ── Embedded gap-filling vocabulary ──────────────────────────────────────
    gap_map = parse_de_map_from_entries(_GAP_FILL)
    for k, v in gap_map.items():
        if k not in DE_GOAULD_MAP:
            DE_GOAULD_MAP[k] = v

    # Add gap entries to the main pool so they appear in search results too
    all_entries = _GAP_FILL + all_entries  # low priority (prepended, MD wins via dedup)

    if not all_entries:
        log.error("Kein Vokabular geladen — bitte Wörterbuch-Dateien prüfen.")

    return all_entries, found_paths
