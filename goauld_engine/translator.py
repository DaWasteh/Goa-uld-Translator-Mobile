# -*- coding: utf-8 -*-
"""Hochlevel-Übersetzungsfunktionen."""

import re
import logging
from typing import Optional

log = logging.getLogger(__name__)

# Globale DE→Goa'uld Map (wird von lexicon.py befüllt)
DE_GOAULD_MAP: dict[str, str] = {}


def preserve_case(original: str, translated: str) -> str:
    if not translated:
        return translated
    if original.isupper():
        return translated.upper()
    if original[0].isupper():
        return translated[0].upper() + translated[1:]
    return translated


def build_mapping(entries: list[dict], direction: str) -> dict[str, str]:
    """
    Baut ein flaches {lowercase_source: target} Mapping für Wort-Übersetzung.
    Sortiert die Einträge nach Priorität, damit qualitativ hochwertige
    Quellen (Kanon) bei Duplikaten gewinnen (last-one-wins).
    """
    # Sortier-Hierarchie für last-one-wins:
    # Höhere Priorität (Kanon) muss ans ENDE der Liste.
    _PRIO_MAP = {
        "SG1-Kanon": 10,
        "Kanon": 9,
        "Goa_uld-Wörterbuch.md": 8,
        "Goa_uld-Dictionary.md": 8,
        "Kanon-ext": 7,
        "RPG-Lexikon": 6,
        "Gap-Fill": 5,
        "Fanon/RPG": 4,
        "Fanon": 3,
        "Goa_uld-Fictionary.md": 2,
        "Goa_uld-Neologikum.md": 1,
    }

    # Stabiles Sortieren: Niedrige Prio zuerst, Hohe Prio zuletzt.
    # Bei gleicher Prio gewinnt DE über EN (da DE in yaml_loader/lexicon später kommt).
    sorted_entries = sorted(
        entries,
        key=lambda e: _PRIO_MAP.get(e.get("source", ""), 0)
    )

    mapping: dict[str, str] = {}
    if direction == "goa2de":
        for e in sorted_entries:
            mapping[e["goauld"].lower()] = e["meaning"]
    else:
        for e in sorted_entries:
            mapping[e["meaning"].lower()] = e["goauld"]
    return mapping


def translate_text(text: str, mapping: dict[str, str],
                   direction: str = "goa2de") -> str:
    """Übersetzt einen Freitext-Satz Wort für Wort."""
    text_stripped = text.strip()
    text_lower = text_stripped.lower()

    # DE→Goa'uld: kompletten Satz zuerst im expliziten Map prüfen
    if direction == "de2goa" and text_lower in DE_GOAULD_MAP:
        return DE_GOAULD_MAP[text_lower]

    if text_lower in mapping:
        return preserve_case(text_stripped, mapping[text_lower])

    tokens = re.split(r"([A-Za-zÄÖÜäöüßÀ-ÿ']+)", text)
    result = []
    for tok in tokens:
        if not tok:
            continue
        if re.match(r"^[A-Za-zÄÖÜäöüßÀ-ÿ']+$", tok):
            low = tok.lower()
            if direction == "de2goa" and low in DE_GOAULD_MAP:
                result.append(DE_GOAULD_MAP[low])
            elif low in mapping:
                result.append(preserve_case(tok, mapping[low]))
            else:
                result.append(tok)
        else:
            result.append(tok)
    return "".join(result)
