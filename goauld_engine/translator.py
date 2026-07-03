# -*- coding: utf-8 -*-
"""High-level translation helpers and runtime lookup maps."""

from __future__ import annotations

import logging
import re

log = logging.getLogger(__name__)

# Mutable module-level dicts populated by lexicon.py.
# DE_GOAULD_MAP remains the legacy alias used by existing UI code paths.
DE_GOAULD_MAP: dict[str, str] = {}
EN_GOAULD_MAP: dict[str, str] = {}
PRIMARY_GOAULD_MAPS: dict[str, dict[str, str]] = {"de": DE_GOAULD_MAP, "en": EN_GOAULD_MAP}
SECONDARY_GOAULD_MAPS: dict[str, dict[str, list[str]]] = {"de": {}, "en": {}}

_SOURCE_PRIORITY: dict[str, int] = {
    "Egyptian-Substrate": 1,
    "Goa_uld-Neologikum.md": 1,
    "Goa_uld-Fictionary.md": 2,
    "Fanon": 3,
    "Fanon/RPG": 4,
    "Gap-Fill": 5,
    "RPG-Lexikon": 6,
    "Kanon-ext": 7,
    "Goa_uld-Wörterbuch.md": 8,
    "Goa_uld-Dictionary.md": 8,
    "Kanon": 9,
    "SG1-Kanon": 10,
}


def normalize_lookup(text: str) -> str:
    """Normalize lookup keys while preserving Goa'uld glottal stops."""
    normalized = str(text).strip().lower()
    normalized = normalized.replace("’", "'").replace("´", "'").replace("`", "'")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def preserve_case(original: str, translated: str) -> str:
    if not translated:
        return translated
    if original.isupper():
        return translated.upper()
    if original and original[0].isupper():
        return translated[0].upper() + translated[1:]
    return translated


def _entry_sort_key(entry: dict, direction: str) -> tuple[int, int, int]:
    """Stable low→high sort key; later entries win in build_mapping."""
    source_score = _SOURCE_PRIORITY.get(str(entry.get("source", "")), 0)
    yaml_priority = int(entry.get("priority", 0) or 0)
    # In the German mobile UI, prefer DE meanings when source/priority tie.
    lang_bonus = 1 if direction == "goa2de" and entry.get("lang") == "de" else 0
    return source_score, yaml_priority, lang_bonus


def build_mapping(entries: list[dict], direction: str) -> dict[str, str]:
    """
    Build a flat {lowercase_source: target} mapping for fallback word translation.

    Runtime primary maps populated from YAML/overlay are preferred by
    translate_text and SentenceAnalyzer. This fallback mapping is still useful
    for old code paths and simple Goa'uld→DE lookups.
    """
    sorted_entries = sorted(entries, key=lambda e: _entry_sort_key(e, direction))

    mapping: dict[str, str] = {}
    if direction == "goa2de":
        for e in sorted_entries:
            mapping[normalize_lookup(e["goauld"])] = e["meaning"]
    else:
        for e in sorted_entries:
            mapping[normalize_lookup(e["meaning"])] = e["goauld"]
    return mapping


def _direct_goauld_lookup(key: str) -> str | None:
    """Try DE first, then EN for source-language→Goa'uld lookup."""
    return DE_GOAULD_MAP.get(key) or EN_GOAULD_MAP.get(key)


def _lemma_goauld_lookup(low: str, mapping: dict[str, str]) -> str | None:
    """
    Fallback: try German (then English) lemma candidates of an unknown token
    against the primary maps and the flat fallback mapping.

    Fixes the gap where inflected forms ("opfert", "findet", "schwöre") failed
    even though the base form ("opfern", "finden", "schwören") is in the lexicon.
    """
    from .lemma import (
        GERMAN_STOP_WORDS, ENGLISH_STOP_WORDS,
        de_lemma_candidates, en_lemma_candidates,
    )

    # Funktionswörter (haben/ist/der …) nie über Lemma-Raten übersetzen
    if low in GERMAN_STOP_WORDS or low in ENGLISH_STOP_WORDS:
        return None

    for cand in de_lemma_candidates(low)[1:]:
        hit = _direct_goauld_lookup(cand) or mapping.get(cand)
        if hit:
            return hit
    for cand in en_lemma_candidates(low)[1:]:
        hit = _direct_goauld_lookup(cand) or mapping.get(cand)
        if hit:
            return hit
    return None


def translate_text(text: str, mapping: dict[str, str],
                   direction: str = "goa2de") -> str:
    """Translate free text word-by-word using primary maps plus fallback mapping."""
    text_stripped = text.strip()
    text_lower = normalize_lookup(text_stripped)

    # DE/EN→Goa'uld: exact phrase first in curated YAML primary maps.
    if direction == "de2goa":
        direct = _direct_goauld_lookup(text_lower)
        if direct:
            return direct

    if text_lower in mapping:
        return preserve_case(text_stripped, mapping[text_lower])

    tokens = re.split(r"([A-Za-zÄÖÜäöüßÀ-ÿ']+)", text)
    result: list[str] = []
    for tok in tokens:
        if not tok:
            continue
        if re.match(r"^[A-Za-zÄÖÜäöüßÀ-ÿ']+$", tok):
            low = normalize_lookup(tok)
            if direction == "de2goa":
                direct = _direct_goauld_lookup(low)
                if direct:
                    result.append(direct)
                    continue
            if low in mapping:
                result.append(preserve_case(tok, mapping[low]))
            elif direction != "goa2de" and (hit := _lemma_goauld_lookup(low, mapping)):
                result.append(preserve_case(tok, hit))
            else:
                result.append(tok)
        else:
            result.append(tok)
    return "".join(result)
