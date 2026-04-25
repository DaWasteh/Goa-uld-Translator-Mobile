# -*- coding: utf-8 -*-
"""Fuzzy-Search-Engine über das Lexicon."""

import re
import difflib
import logging
from typing import Optional

from .lemma import de_lemma_candidates

log = logging.getLogger(__name__)


class SearchEngine:
    """
    Bidirektionale Suche mit exaktem Matching, Präfix-Matching und Fuzzy-Matching.
    """

    # Quellen-Priorität: Haupt-Wörterbuch > Fictionary > Neologikum
    _SOURCE_PRIORITY: dict[str, int] = {
        "Goa'uld-Wörterbuch.md": 3,
        "Goa_uld-Wörterbuch.md": 3,
        "Goa'uld-Dictionary.md": 3,
        "Goa_uld-Dictionary.md": 3,
        "Goa'uld-Fictionary.md": 2,
        "Goa_uld-Fictionary.md": 2,
        "Goa'uld-Neologikum.md": 1,
        "Goa_uld-Neologikum.md": 1,
        "Gap-Fill": 2,
        "Kanon": 3,
        "Kanon-ext": 2,
        "Fanon": 2,
        "Fanon/RPG": 2,
        "RPG-Lexikon": 2,
        "SG1-Kanon": 3,
    }

    def __init__(self, entries: list[dict]) -> None:
        self.entries = entries
        # FIX 1 (translation-bugs-findings.md): Deduplikation mit Quellen-Priorität
        # Bei gleichem (goauld_lower, meaning_lower) behalten wir den Eintrag
        # mit der höheren Quellen-Priorität.
        seen: dict[tuple, tuple[int, dict]] = {}
        for e in entries:
            key = (e["goauld"].lower(), e["meaning"].lower())
            src = e.get("source", "")
            priority = self._SOURCE_PRIORITY.get(src, 0)
            if key not in seen:
                seen[key] = (priority, e)
            else:
                old_priority = seen[key][0]
                if priority > old_priority:
                    seen[key] = (priority, e)
        self.entries = [e for _, e in seen.values()]

    # ─── public api ──────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        direction: str = "goa2de",
        max_results: int = 80,
        fuzzy_threshold: float = 0.45,
        lang_pref: str = "de",
        prefer_short_target: bool = False,
        min_score: int = 0,
    ) -> list[dict]:
        """
        direction:           'goa2de' → suche in goauld-Spalte
                             'de2goa' → suche in meaning-Spalte
        lang_pref:           'de' → deutsche Einträge zuerst
                             'en' → englische Einträge zuerst
        prefer_short_target: True → bevorzuge Einträge mit einwortigem Ziel
        min_score:           Mindest-Score (vor Boni) — Treffer unterhalb werden
                             verworfen. Für de2goa empfohlen: 50 (nur echte Wort-
                             Matches, keine fuzzy-Zufallstreffer).
        """
        q = query.strip()
        if not q:
            return []
        q_low = q.lower()

        field = "goauld" if direction == "goa2de" else "meaning"

        results: list[tuple[float, dict]] = []

        for e in self.entries:
            val = e[field].lower()
            # FIX 3 (translation-bugs-findings.md): Dynamischer Fuzzy-Threshold für kurze Wörter
            eff_threshold = fuzzy_threshold
            if len(q_low) <= 6:
                eff_threshold = max(fuzzy_threshold, 0.7)  # Höherer Threshold für kurze Wörter
            base_score = self._score(q_low, val, fuzzy_threshold=eff_threshold, direction=direction)
            if base_score > 0 and base_score >= min_score:
                # Sprach-Bonus: bevorzugte Sprache +8 Punkte
                lang_bonus = 8 if e.get("lang", "de") == lang_pref else 0
                # Einzelwort-Bonus: bei Einzelwort-Eingabe kurze Übersetzungen bevorzugen
                # (vermeidet dass "liebe" → "Pal tiem shree tal ma" statt "mel")
                short_bonus = 0
                if prefer_short_target:
                    target_field = "goauld" if direction == "de2goa" else "meaning"
                    target_val = e[target_field].strip()
                    if " " not in target_val:   # einwortiges Ziel
                        short_bonus = 15
                # de2goa-Bonus: exakte/partielle Übereinstimmung priorisieren
                de2goa_bonus = 0
                if direction == "de2goa":
                    # Exakter oder Prefix-Match in meaning → Bonus
                    if val == q_low or val.startswith(q_low):
                        de2goa_bonus = 10
                    # Whole-word match in meaning → Bonus
                    if re.search(rf"\b{re.escape(q_low)}\b", val, re.IGNORECASE):
                        de2goa_bonus = max(de2goa_bonus, 5)
                # FIX 5 (translation-bugs-findings.md): Sekundäre Quellen strafen
                source_penalty = 0
                src = e.get("source", "")
                if src in ("Goa'uld-Fictionary.md", "Goa_uld-Fictionary.md",
                           "Goa'uld-Neologikum.md", "Goa_uld-Neologikum.md"):
                    source_penalty = 15  # -15 Punkte für Fictionary/Neologikum
                final_score = base_score + lang_bonus + short_bonus + de2goa_bonus - source_penalty
                # FIX 4 (translation-bugs-findings.md): Debug-Logging für fehlende Wörter
                if base_score == 0 and q_low in ("stirb", "vernichten", "deine", "mensch", "human"):
                    log.warning("FEHLER: '%s' hat base_score=0 für Eintrag: %s", q_low, e)
                results.append((final_score, e))

        results.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in results[:max_results]]

    def search_all(self, query: str, max_results: int = 80) -> list[dict]:
        """Suche in beiden Feldern gleichzeitig."""
        q = query.strip()
        if not q:
            return []
        q_low = q.lower()
        # FIX P5c: Index statt id(e) — id() kann bei GC recycelt werden
        best: dict[int, tuple[int, dict]] = {}  # index → (score, entry)

        for idx, e in enumerate(self.entries):
            score_g = self._score(q_low, e["goauld"].lower())
            score_m = self._score(q_low, e["meaning"].lower())
            score = max(score_g, score_m)
            if score > 0:
                if idx not in best or best[idx][0] < score:
                    best[idx] = (score, e)

        results = sorted(best.values(), key=lambda x: x[0], reverse=True)
        return [e for _, e in results[:max_results]]

    # ─── private ─────────────────────────────────────────────────────────────

    @staticmethod
    def _score(query: str, value: str, fuzzy_threshold: float = 0.42,
               direction: str = "goa2de") -> int:
        """
        Bewertungsfunktion für Similarity-Score.

        Strategie (priorisiert):
        1. Exakter Match (100)
        2. Prefix-Match (85)
        3. Whole-word match (75)
        4. Teilwort-Match (65)
        5. Wort-Level-Match (55-60)
        6. Fuzzy-Match (0-45)

        Bonus für Längen-Ähnlichkeit: Kürzere, passende Treffer erhalten
        einen zusätzlichen Score-Bonus.

        direction: 'de2goa' → höhere Schwellenwerte für meaningful matches
        """
        if value == query:
            return 100
        if value.startswith(query):
            return 85
        # Whole-word match: query als ganzes Wort in value
        if re.search(rf"\b{re.escape(query)}\b", value, re.IGNORECASE):
            return 75
        if query in value:
            return 65
        # word-level match
        value_words = re.split(r"[\s,;/!?()]+", value)
        if any(w.startswith(query) for w in value_words if w):
            return 60
        if any(query in w for w in value_words if w):
            return 55
        # Substring match mit Längen-Bonus
        if len(query) > 3:
            for w in value_words:
                if w and query[:max(4, len(query)//2)] in w:
                    return 45
        # fuzzy
        ratio = difflib.SequenceMatcher(None, query, value).ratio()
        if ratio >= fuzzy_threshold:
            # Längen-Bonus: ähnliche Längen erhalten höheren Score
            len_ratio = min(len(query), len(value)) / max(len(query), len(value))
            return int(ratio * 45 * (0.5 + 0.5 * len_ratio))
        return 0
