# -*- coding: utf-8 -*-
"""Deutsches Lemma- und Stemming-System."""

import re

# ─────────────────────────────────────────────────────────────────────────────
# STOP WORDS  (Deutsche Funktionswörter ohne Goa'uld-Äquivalent)
# ─────────────────────────────────────────────────────────────────────────────

# Goa'uld hat keine Artikel, keine Hilfsverben im deutschen Sinne und kaum
# Präpositionen — diese Wörter werden bei DE→Goa'uld stumm übersprungen.
GERMAN_STOP_WORDS: frozenset[str] = frozenset({
    # Artikel
    "der", "die", "das", "dem", "den", "des",
    "ein", "eine", "einen", "einem", "einer", "eines",
    # Präpositionen
    "in", "im", "an", "am", "auf", "bei", "mit", "nach", "seit", "von",
    "vor", "zu", "zum", "zur", "durch", "für", "gegen", "ohne", "um",
    "über", "unter", "zwischen", "aus", "bis", "hinter", "neben",
    # Konjunktionen (koordinierend)
    "und", "oder", "aber", "doch", "sondern", "denn", "als", "wie",
    # Partikel / sonstige Funktionswörter
    "auch", "nur", "schon", "noch", "ja", "nicht", "kein", "keine",
    "sehr", "gar", "mal", "nun", "so",
})


def de_lemma_candidates(word: str) -> list[str]:
    """
    Gibt mögliche Grundformen für ein deutsches Wort zurück.
    Deckt häufige Verb-Konjugation und Nominalflexion ab, damit
    DE_MAP-Lookups für Imperativ/Plural/Genitiv-Formen funktionieren.

    Beispiele:
      zerstör  → [zerstör, zerstöre, zerstören]
      liebst   → [liebst, lieben, liebe, lieb]
      raumschiffe → [raumschiffe, raumschiff]

    Erweiterungen:
      - Umlaut-Varianten: ä→a, ö→o, ü→u
      - Kompositvorschläge: "frei" → auch "Freiheit" prüfen
      - Reduplikation: "sterbe" → "sterben", "sterbt"
      - Genitiv: "dem" → "der"
      - Kompositvorschläge: "zerstör" → "Zerstörung"
      - Kontraktionen: "im" → "in dem", "zum" → "zu dem"
    """
    w = word.lower().strip()
    candidates = [w]

    # ── Verb: Imperativ-Ergänzungen ──────────────────────────────────────────
    # "zerstör" → "zerstöre", "zerstören"
    # Nur für kurze Wörter und keine offensichtlichen Nomen-Plurale
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
        # Für Nomen-Plurale: nur Singular-Form hinzufügen
        candidates.append(w[:-1])

    # ── Verb: Präsens → Infinitiv ─────────────────────────────────────────────
    # "zerstörst" → "zerstör" → "zerstören"
    # Nur für Verben, nicht für Nomen-Plurale
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
        # 1. Person Singular → Infinitiv
        if w.endswith("e") and len(w) > 3:
            stem = w[:-1]
            if stem:
                candidates += [stem + "en", stem + "st", stem + "t"]
        # Imperativ Singular → Infinitiv
        if len(w) > 4 and not w.endswith("e") and not w.endswith("en"):
            candidates += [w + "st", w + "t"]

    # ── Nomen: Plural-Formen → Singular ──────────────────────────────────────
    # "raumschiffe" → "raumschiff"
    if w.endswith("e") and len(w) > 3:
        candidates.append(w[:-1])
    # "götter" → "gott"  (not perfect but helps)
    if w.endswith("er") and len(w) > 4:
        candidates.append(w[:-2])
    if w.endswith("en") and len(w) > 4:
        candidates.append(w[:-2])
    if w.endswith("nen") and len(w) > 5:
        candidates.append(w[:-3])

    # ── Nomen: Genitiv → Nominativ ────────────────────────────────────────────
    # "hauses" → "haus"
    if w.endswith("es") and len(w) > 3:
        candidates.append(w[:-2])
    if w.endswith("s") and len(w) > 2:
        candidates.append(w[:-1])

    # ── Adjektiv-Endungen → Stamm ─────────────────────────────────────────────
    for suffix in ("em", "en", "er", "es", "sten", "test"):
        if w.endswith(suffix) and len(w) > len(suffix) + 2:
            candidates.append(w[: -len(suffix)])

    # ── Superlativ/Comparativ → Positiv ───────────────────────────────────────
    if w.endswith("sten") and len(w) > 5:
        candidates.append(w[:-4])  # "meisten" → "meist"
    if w.endswith("test") and len(w) > 5:
        candidates.append(w[:-4])  # "am besten" → "best"

    # ── Umlaut-Varianten ──────────────────────────────────────────────────────
    # ä→a, ö→o, ü→u, ß→ss (für DE_MAP-Lookup)
    umlaut_map = str.maketrans("äöü", "aou")
    plain = w.translate(umlaut_map).replace("ß", "ss")
    if plain != w:
        candidates.append(plain)
        # Auch Plural/Verb-Formen des Stamms
        if not plain.endswith("e"):
            candidates.append(plain + "e")
        if not plain.endswith("en"):
            candidates.append(plain + "en")

    # ── Rückwärts-Umlaut: a→ä, o→ö, u→ü, ss→ß ────────────────────────────────
    # Hilfreich wenn DE_MAP Umlaute hat, aber Eingabe nicht
    # Nur einfache 1:1 Mapping, ss→ß ist komplexer
    reverse_chars = {"a": "ä", "o": "ö", "u": "ü"}
    umlauted = "".join(reverse_chars.get(c, c) for c in w)
    if "ss" in w:
        umlauted_ss = umlauted.replace("ss", "ß")
        candidates.append(umlauted_ss)
    if umlauted != w and len(umlauted) == len(w):
        candidates.append(umlauted)

    # ── Kontraktionen auflösen ────────────────────────────────────────────────
    _kontraktionen: dict[str, str] = {
        "im": "in dem", "zum": "zu dem", "ans": "an das",
        "ams": "an dem", "ins": "in das", "ins": "in dem",
        "beim": "bei dem", "vom": "von dem", "ins": "in das",
        "ins": "in das", "ins": "in das",
    }
    if w in _kontraktionen:
        candidates.extend(_kontraktionen[w].split())

    # ── Kompositvorschläge (häufige Suffixe) ─────────────────────────────────
    # "frei" → "Freiheit", "Stärke" → "stark"
    for suffix in ("heit", "keit", "ung", "bar", "sam", "lich", "isch", "haft", "los", "voll"):
        if w.endswith(suffix):
            stem = w[:-len(suffix)]
            if stem:
                candidates.append(stem)
    # "sterbe" → "sterben" (bereits oben), aber auch "tot" prüfen
    if w.endswith("e") and len(w) > 3:
        verb_inf = w[:-1] + "en"
        if verb_inf not in candidates:
            candidates.append(verb_inf)

    # ── Häufige Komposita-Brücken ────────────────────────────────────────────
    # "zerstör" → auch "Zerstörer", "Zerstörung" prüfen
    # Ersetzt das Suffix statt anzuhängen
    _komposita_repl: dict[str, str] = {
        "ör": "örer",       # zerstör → Zerstörer
        "ung": "ung",      # zerstör → Zerstörung (nur anhängen)
        "bar": "er",       # zerstörbar → Zerstörer
        "lich": "keit",    # freilich → Freiheit
        "isch": "keit",    # herrlich → Herrlichkeit
    }
    for suffix, replacement in _komposita_repl.items():
        if w.endswith(suffix):
            stem = w[:-len(suffix)]
            if stem:
                candidates.append(stem + replacement)
    # Suffix-Anhängen für -ung Varianten
    if w.endswith("ung"):
        candidates.extend([w + "en", w + "e", w + "er"])
    elif w.endswith("er") and len(w) > 4:
        candidates.extend([w + "e", w + "en"])

    # Deduplizieren, Reihenfolge erhalten (ursprüngliches Wort zuerst)
    seen: set[str] = set()
    result: list[str] = []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            result.append(c)
    return result
