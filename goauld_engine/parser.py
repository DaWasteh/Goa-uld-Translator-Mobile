# -*- coding: utf-8 -*-
"""Markdown-Parser für die Goa'uld-Dictionaries."""

import re
import logging
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

# Regex für rechteckige Tabellen-Trennzeichen
_SKIP_FIRST = {"goa'uld", "goa'uldsprache", "deutsch", "english", "wort", "bedeutung"}
_SKIP_SECOND = {"bedeutung", "english", "deutsch", "goa'uld", "goa'uldsprache", "wörterbuch"}

# Regex für Deutsch→Goa'uld-Sektionserkennung
_DE_GOA_SECTION_RE = re.compile(
    r"(deutsch\s*→\s*goa'uld|deutsch\s*=>\s*goa'uld|"
    r"deutsch\s*\(?\s*goa'uld|deutsch\s*to\s*goa'uld|"
    r"direct\s+lookup|direktzuordnung|neologikum.*direct)",
    re.IGNORECASE,
)


def _clean(text: str) -> str:
    """Strip **bold** markers, inline code, and whitespace."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = text.strip().strip('"').strip("'")
    return text.strip()


def parse_markdown_dictionary(filepath: str) -> list[dict]:
    """
    Parse a Goa'uld markdown dictionary and return a list of entries.

    Each entry is a dict:
        goauld   – the Goa'uld word / phrase
        meaning  – the translation (German or English)
        section  – which section of the dictionary
        source   – episode / source reference (optional)

    Also handles reversed sections (Deutsch → Goa'uld) where col0 is the
    German word and col1 is the Goa'uld target — these are returned with
    goauld/meaning swapped so the engine sees them correctly.
    """
    entries: list[dict] = []
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError as exc:
        log.warning("Markdown-Datei nicht lesbar: %s", exc)
        return entries

    current_section = "Allgemein"
    reversed_section = False   # True inside a Deutsch→Goa'uld table

    for raw in lines:
        line = raw.rstrip("\n")

        # Track section headings
        if line.startswith("## ") or line.startswith("# "):
            current_section = line.lstrip("#").strip()
            reversed_section = bool(_DE_GOA_SECTION_RE.match(current_section))
            continue

        # Only process table rows
        if not line.startswith("|"):
            continue

        # Skip separator rows (| --- | --- |)
        if re.search(r"\|\s*[-:]+\s*\|", line):
            continue

        parts = [_clean(p) for p in line.split("|")]
        parts = [p for p in parts if p]

        if len(parts) < 2:
            continue

        col0 = parts[0]
        col1 = parts[1]
        col2 = parts[2] if len(parts) > 2 else ""

        # Skip header rows
        if col0.lower() in _SKIP_FIRST:
            continue
        if col1.lower() in _SKIP_SECOND:
            continue
        if not col0 or not col1:
            continue

        if reversed_section:
            # col0 = Deutsch, col1 = Goa'uld  → swap so engine is consistent
            entries.append({
                "goauld":  col1,
                "meaning": col0,
                "section": current_section,
                "source":  col2,
                "de_map":  True,   # marker: used to rebuild DE_GOAULD_MAP
            })
        else:
            entries.append({
                "goauld":  col0,
                "meaning": col1,
                "section": current_section,
                "source":  col2,
            })

    return entries


def parse_de_map_from_entries(entries: list[dict]) -> dict[str, str]:
    """
    Baut das DE→Goa'uld-Direktwörterbuch aus den geladenen MD-Einträgen.

    Zwei Quellen:
    1. Explizite de_map-Einträge (Wörterbuch: Deutsch→Goa'uld-Direktzuordnung)
    2. Auto-Reverse: DE-Einträge (lang=="de") mit einwortigem deutsches Bedeutungsfeld
       → ermöglicht Satz-Übersetzung aus Neologikum/Fictionary ohne manuelle de_map-Tags.
    """
    result: dict[str, str] = {}

    # Quelle 1: Explizit markierte Direktzuordnungen (höchste Priorität)
    for e in entries:
        if e.get("de_map"):
            key = e["meaning"].lower().strip()
            result[key] = e["goauld"].strip()

    # Quelle 2: Auto-Reverse aus einfachen DE-Einträgen
    # Aus jeder Bedeutung den ersten deutschen Term extrahieren:
    #   "Kind (geschlechtsneutral)"  → "kind"
    #   "Fehler, Alarm, Warnsignal"  → "fehler" + "alarm" + "warnsignal"
    #   "Zukunft, das Kommende"       → "zukunft"
    _split_re = re.compile(r"[,;]")
    _paren_re = re.compile(r"\s*\(.*?\)")
    _word_ok = re.compile(r"^[\w\u00c4\u00d6\u00dc\u00e4\u00f6\u00fc\u00df\'\-]+$", re.UNICODE)
    for e in entries:
        if e.get("lang") != "de":
            continue
        if e.get("de_map"):
            continue  # bereits in Quelle 1 erfasst
        goauld = e["goauld"].strip()
        parts = _split_re.split(e["meaning"].strip())
        for part in parts:
            term = _paren_re.sub("", part).strip()
            key = term.lower()
            # Nur aufnehmen wenn einwortig und noch nicht belegt
            if " " not in term and _word_ok.match(term) and key not in result:
                result[key] = goauld

    return result
