# -*- coding: utf-8 -*-
"""German/English lemma and transfer-word helpers."""

from __future__ import annotations

import re


def normalize_lookup(text: str) -> str:
    """Normalize lookup keys while preserving Goa'uld glottal stops."""
    normalized = str(text).strip().lower()
    normalized = normalized.replace("’", "'").replace("´", "'").replace("`", "'")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


# ─────────────────────────────────────────────────────────────────────────────
# FUNCTION WORDS / TRANSFER CLASSES
# ─────────────────────────────────────────────────────────────────────────────

# Only true transfer/function words are skipped. Semantic markers such as
# negation (nicht/kein/not/no), modals (muss/kann/must/can), yes/no and
# conjunctions stay translatable through YAML/overlay maps.
GERMAN_ARTICLES: frozenset[str] = frozenset({
    "der", "die", "das", "dem", "den", "des",
    "ein", "eine", "einen", "einem", "einer", "eines",
})
GERMAN_PREPOSITIONS: frozenset[str] = frozenset({
    "in", "im", "an", "am", "auf", "bei", "mit", "nach", "seit", "von",
    "vor", "zu", "zum", "zur", "durch", "für", "gegen", "ohne", "um",
    "über", "unter", "zwischen", "aus", "bis", "hinter", "neben",
})
GERMAN_AUXILIARIES: frozenset[str] = frozenset({
    "bin", "bist", "ist", "sind", "seid", "sein", "sei", "war", "waren",
    "wart", "gewesen", "habe", "hast", "hat", "haben", "habt", "hatte",
    "hatten", "werde", "wirst", "wird", "werden", "werdet", "würde",
    "würden",
})
GERMAN_MODAL_SEMANTIC: frozenset[str] = frozenset({
    "kann", "kannst", "können", "könnt", "muss", "musst", "müssen",
    "soll", "sollen", "sollst",
})
GERMAN_LIGHT_PARTICLES: frozenset[str] = frozenset({
    "auch", "nur", "schon", "noch", "doch", "sondern", "denn", "als",
    "sehr", "gar", "mal", "nun", "so",
})
GERMAN_STOP_WORDS: frozenset[str] = (
    GERMAN_ARTICLES | GERMAN_PREPOSITIONS | GERMAN_AUXILIARIES | GERMAN_LIGHT_PARTICLES
)

ENGLISH_ARTICLES: frozenset[str] = frozenset({"a", "an", "the"})
ENGLISH_PREPOSITIONS: frozenset[str] = frozenset({
    "in", "on", "at", "by", "with", "from", "for", "to", "of", "into",
    "onto", "over", "under", "between", "through", "before", "after",
    "within", "without", "as",
})
ENGLISH_AUXILIARIES: frozenset[str] = frozenset({
    "am", "are", "is", "be", "being", "been", "was", "were", "do", "does",
    "did", "have", "has", "had", "will", "would",
})
ENGLISH_MODAL_SEMANTIC: frozenset[str] = frozenset({
    "shall", "should", "can", "could", "may", "might", "must",
})
ENGLISH_LIGHT_PARTICLES: frozenset[str] = frozenset({"just", "very", "already", "still"})
ENGLISH_STOP_WORDS: frozenset[str] = (
    ENGLISH_ARTICLES | ENGLISH_PREPOSITIONS | ENGLISH_AUXILIARIES | ENGLISH_LIGHT_PARTICLES
)

STOP_WORDS_BY_LANG: dict[str, frozenset[str]] = {
    "de": GERMAN_STOP_WORDS,
    "en": ENGLISH_STOP_WORDS,
}


def de_lemma_candidates(word: str) -> list[str]:
    """
    Return possible German base forms for a word.

    Covers common verb conjugations, noun/adjective inflection, umlaut variants
    and a few contraction/compound bridges.
    """
    w = normalize_lookup(word)
    candidates = [w]

    _is_noun_plural = (
        w.endswith("e") and len(w) > 6
        and not w.endswith("che")
        and not w.endswith("sse")
        and not w.endswith("phe")
        and not w.endswith("nte")
        and not w.endswith("ste")
    )
    if not _is_noun_plural:
        if not w.endswith("e"):
            candidates.append(w + "e")
        if not w.endswith("en"):
            candidates.append(w + "en")
    else:
        candidates.append(w[:-1])

    if not _is_noun_plural:
        if w.endswith("st"):
            stem = w[:-2]
            candidates += [stem, stem + "en", stem + "e"]
        if w.endswith("t") and len(w) > 3:
            stem = w[:-1]
            candidates += [stem, stem + "en", stem + "e"]
        if w.endswith("est"):
            stem = w[:-3]
            candidates += [stem, stem + "en", stem + "e"]
        if w.endswith("e") and len(w) > 3:
            stem = w[:-1]
            if stem:
                candidates += [stem + "en", stem + "st", stem + "t"]
        if len(w) > 4 and not w.endswith("e") and not w.endswith("en"):
            candidates += [w + "st", w + "t"]

    if w.endswith("e") and len(w) > 3:
        candidates.append(w[:-1])
    if w.endswith("er") and len(w) > 4:
        candidates.append(w[:-2])
    if w.endswith("en") and len(w) > 4:
        candidates.append(w[:-2])
    if w.endswith("nen") and len(w) > 5:
        candidates.append(w[:-3])

    if w.endswith("es") and len(w) > 3:
        candidates.append(w[:-2])
    if w.endswith("s") and len(w) > 2:
        candidates.append(w[:-1])

    for suffix in ("em", "en", "er", "es", "sten", "test"):
        if w.endswith(suffix) and len(w) > len(suffix) + 2:
            candidates.append(w[: -len(suffix)])

    if w.endswith("sten") and len(w) > 5:
        candidates.append(w[:-4])
    if w.endswith("test") and len(w) > 5:
        candidates.append(w[:-4])

    umlaut_map = str.maketrans("äöü", "aou")
    plain = w.translate(umlaut_map).replace("ß", "ss")
    if plain != w:
        candidates.append(plain)
        if not plain.endswith("e"):
            candidates.append(plain + "e")
        if not plain.endswith("en"):
            candidates.append(plain + "en")

    reverse_chars = {"a": "ä", "o": "ö", "u": "ü"}
    umlauted = "".join(reverse_chars.get(c, c) for c in w)
    if "ss" in w:
        candidates.append(umlauted.replace("ss", "ß"))
    if umlauted != w and len(umlauted) == len(w):
        candidates.append(umlauted)

    kontraktionen: dict[str, str] = {
        "im": "in dem", "zum": "zu dem", "ans": "an das",
        "ams": "an dem", "ins": "in das", "beim": "bei dem", "vom": "von dem",
    }
    if w in kontraktionen:
        candidates.extend(kontraktionen[w].split())

    for suffix in ("heit", "keit", "ung", "bar", "sam", "lich", "isch", "haft", "los", "voll"):
        if w.endswith(suffix):
            stem = w[:-len(suffix)]
            if stem:
                candidates.append(stem)

    if w.endswith("e") and len(w) > 3:
        verb_inf = w[:-1] + "en"
        if verb_inf not in candidates:
            candidates.append(verb_inf)

    komposita_repl: dict[str, str] = {
        "ör": "örer",
        "ung": "ung",
        "bar": "er",
        "lich": "keit",
        "isch": "keit",
    }
    for suffix, replacement in komposita_repl.items():
        if w.endswith(suffix):
            stem = w[:-len(suffix)]
            if stem:
                candidates.append(stem + replacement)
    if w.endswith("ung"):
        candidates.extend([w + "en", w + "e", w + "er"])
    elif w.endswith("er") and len(w) > 4:
        candidates.extend([w + "e", w + "en"])

    seen: set[str] = set()
    result: list[str] = []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            result.append(c)
    return result


def en_lemma_candidates(word: str) -> list[str]:
    """Small English lemmatizer for low-resource direct lookup."""
    w = normalize_lookup(word)
    candidates = [w]

    irregular: dict[str, list[str]] = {
        "am": ["be"], "are": ["be"], "is": ["be"], "was": ["be"], "were": ["be"],
        "i'm": ["i"], "you're": ["you"], "we're": ["we"], "they're": ["they"],
        "don't": ["do not", "not"], "dont": ["do not", "not"],
        "doesn't": ["does not", "not"], "doesnt": ["does not", "not"],
        "didn't": ["did not", "not"], "didnt": ["did not", "not"],
    }
    candidates.extend(irregular.get(w, []))

    if w.endswith("ies") and len(w) > 4:
        candidates.append(w[:-3] + "y")
    if w.endswith("es") and len(w) > 3:
        candidates.append(w[:-2])
    if w.endswith("s") and len(w) > 3 and not w.endswith("ss"):
        candidates.append(w[:-1])
    if w.endswith("ing") and len(w) > 5:
        stem = w[:-3]
        candidates.extend([stem, stem + "e"])
    if w.endswith("ed") and len(w) > 4:
        stem = w[:-2]
        candidates.extend([stem, stem + "e"])

    seen: set[str] = set()
    result: list[str] = []
    for candidate in candidates:
        if candidate and candidate not in seen:
            seen.add(candidate)
            result.append(candidate)
    return result
