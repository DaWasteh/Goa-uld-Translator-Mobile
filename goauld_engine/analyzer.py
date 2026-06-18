# -*- coding: utf-8 -*-
"""Token-für-Token-Satzanalyse für den Debrief-Tab."""

import re
import logging
from typing import Optional

from .search import SearchEngine
from .lemma import de_lemma_candidates, GERMAN_STOP_WORDS
from .translator import DE_GOAULD_MAP

log = logging.getLogger(__name__)


class SentenceAnalyzer:
    """
    Analysiert Sätze Token für Token.
    Gibt für jedes Wort primäre Übersetzung + Alternativen zurück.
    """

    _WORD_RE = re.compile(r"^[\w'äöüÄÖÜß]+$", re.UNICODE)

    def __init__(self, entries: list[dict]) -> None:
        self.engine = SearchEngine(entries)

    def is_sentence(self, text: str) -> bool:
        """True wenn der Text mehr als ein Wort enthält."""
        return len(text.strip().split()) > 1

    def analyze(self, text: str, direction: str, lang_pref: str = "de") -> list[dict]:
        """
        Returns list of token dicts:
            token        – original word (may be a phrase if matched as unit)
            primary      – best-match entry or None
            alternatives – up to 3 further entries
            found        – True/False
            skipped      – True when a stop word was silently dropped

        Uses greedy longest-phrase-first matching:
          • DE→Goa'uld: articles/particles are silently dropped (no Goa'uld equivalent).
            DE_MAP multi-word hits are only used when no shorter Goa'uld entry exists.
          • Goa'uld→DE: multi-word Goa'uld phrases are recognised as one unit.
        """
        # ── 1. Flatten to clean word list ─────────────────────────────────────
        raw_tokens = re.split(r"(\s+)", text.strip())
        words: list[str] = []
        for tok in raw_tokens:
            clean = tok.strip(".,!?;:")
            if clean and self._WORD_RE.match(clean):
                words.append(clean)

        if not words:
            return []

        _MAX_PHRASE = 6        # max window size (words)
        result: list[dict] = []
        i = 0

        # ── 2. Greedy longest-match loop ──────────────────────────────────────
        while i < len(words):
            matched = False
            window = min(_MAX_PHRASE, len(words) - i)

            # ── DE → Goa'uld ─────────────────────────────────────────────────
            if direction == "de2goa":

                # a) Stop word? → skip silently, don't add to translation
                # Nur skippen, wenn NICHT im DE_GOAULD_MAP vorhanden (z.B. ia/ka)
                if (
                    words[i].lower() in GERMAN_STOP_WORDS
                    and words[i].lower() not in DE_GOAULD_MAP
                ):
                    result.append({
                        "token":        words[i],
                        "primary":      None,
                        "alternatives": [],
                        "found":        False,
                        "skipped":      True,   # stop-word, not a failure
                    })
                    i += 1
                    continue

                # b) Try multi-word DE_MAP hits first (window → 2), then Engine
                de_map_hit: Optional[tuple[str, str]] = None  # (phrase, goauld)
                for n in range(window, 1, -1):
                    phrase    = " ".join(words[i:i + n])
                    # Try exact phrase first, then lemma candidates for multi-word
                    hit = DE_GOAULD_MAP.get(phrase.lower())
                    if hit:
                        de_map_hit = (phrase, hit)
                        # Immediately consume multi-word phrase and move on
                        synthetic = {
                            "goauld":  hit,
                            "meaning": phrase,
                            "section": "Deutsch→Goa'uld",
                            "source":  "DE_MAP",
                            "lang":    "de",
                        }
                        result.append({
                            "token":        phrase,
                            "primary":      synthetic,
                            "alternatives": [],
                            "found":        True,
                            "skipped":      False,
                        })
                        i += n
                        matched = True
                        break

                if matched:
                    continue

                # b2) Multi-word Engine search (neue Funktion)
                #     Suche auch in der Engine nach Multi-Wort-Phrasen
                for n in range(window, 1, -1):
                    phrase    = " ".join(words[i:i + n])
                    phrase_low = phrase.lower()
                    engine_phrases = self.engine.search(
                        phrase, direction=direction,
                        max_results=3, lang_pref=lang_pref,
                        min_score=60,
                    )
                    if engine_phrases:
                        top_val = engine_phrases[0]["meaning"].lower()
                        score = self.engine._score(phrase_low, top_val)
                        if score >= 75:  # exact oder gute Übereinstimmung
                            result.append({
                                "token":        phrase,
                                "primary":      engine_phrases[0],
                                "alternatives": engine_phrases[1:3],
                                "found":        True,
                                "skipped":      False,
                            })
                            i += n
                            matched = True
                            break

                if matched:
                    continue

                # c) Single word – DE_MAP hat IMMER Vorrang vor Engine
                phrase    = words[i]
                phrase_low = phrase.lower()

                # Lemma fallback: try "zerstör" → "zerstöre" → "zerstören" etc.
                de_map_single: Optional[str] = None
                for candidate in de_lemma_candidates(phrase_low):
                    de_map_single = DE_GOAULD_MAP.get(candidate)
                    if de_map_single:
                        break

                engine_matches = self.engine.search(
                    phrase, direction=direction,
                    max_results=7, lang_pref=lang_pref,
                    prefer_short_target=True,
                    min_score=50,   # require real word-match, not fuzzy noise
                )

                # DE_MAP hat IMMER Priorität — Engine nur als Alternative
                if de_map_single:
                    # DE_MAP gefunden → immer verwenden
                    chosen_primary = {
                        "goauld":  de_map_single,
                        "meaning": phrase,
                        "section": "Deutsch→Goa'uld",
                        "source":  "DE_MAP",
                        "lang":    "de",
                    }
                    chosen_alts = engine_matches[:3] if engine_matches else []
                elif engine_matches:
                    chosen_primary = engine_matches[0]
                    chosen_alts    = engine_matches[1:4]
                else:
                    chosen_primary = None
                    chosen_alts = []

                result.append({
                    "token":        phrase,
                    "primary":      chosen_primary,
                    "alternatives": chosen_alts,
                    "found":        chosen_primary is not None,
                    "skipped":      False,
                })
                i += 1
                continue

            # ── Goa'uld → DE ─────────────────────────────────────────────────
            for n in range(window, 0, -1):
                phrase     = " ".join(words[i:i + n])
                phrase_low = phrase.lower()

                if n > 1:
                    # Multi-word: only use if goauld field matches phrase exactly/nearly
                    matches = self.engine.search(phrase, direction=direction,
                                                 max_results=3, lang_pref=lang_pref)
                    if matches:
                        top_val = matches[0]["goauld"].lower()
                        score = self.engine._score(phrase_low, top_val)
                        if score >= 85:   # exact (100) or prefix (85)
                            result.append({
                                "token":        phrase,
                                "primary":      matches[0],
                                "alternatives": matches[1:3],
                                "found":        True,
                                "skipped":      False,
                            })
                            i += n
                            matched = True
                            break
                else:
                    # Single word: prefer entries with shorter German meanings
                    matches = self.engine.search(phrase, direction=direction,
                                                 max_results=7, lang_pref=lang_pref,
                                                 prefer_short_target=True,
                                                 min_score=40)
                    result.append({
                        "token":        phrase,
                        "primary":      matches[0] if matches else None,
                        "alternatives": matches[1:4] if matches else [],
                        "found":        bool(matches),
                        "skipped":      False,
                    })
                    i += 1
                    matched = True
                    break

            if not matched:
                result.append({
                    "token":        words[i],
                    "primary":      None,
                    "alternatives": [],
                    "found":        False,
                    "skipped":      False,
                })
                i += 1

        return result

    @staticmethod
    def _extract_core_meaning(meaning: str) -> str:
        """
        Extrahiert die kürzeste sinnvolle Kernbedeutung aus einem Wörterbuch-Eintrag.

        Strategie:
          1. Entfernt Klammern, Markdown-Dekoratoren
          2. Splittet an mehreren Trennzeichen (;  —  /  ,)
          3. Wählt das kürzeste nicht-leere Segment ≥ 1 Wort
          4. Bereinigt Anführungszeichen und führende Sonderzeichen
        """
        m = meaning.strip()
        # Strip leading decorators/bullets
        m = re.sub(r"^[\-–▸→✦◆◉☓\s]+", "", m)
        # Remove bracketed annotations like (Pronomen), (Substantiv) etc.
        m = re.sub(r"\s*\([^)]*\)\s*", " ", m)
        # Split on major meaning separators
        segments = re.split(r"\s*[;—/,]\s*", m)
        segments = [s.strip().strip('"\'„"').strip() for s in segments if s.strip()]
        if not segments:
            return ""
        # Prefer the shortest segment (most likely the core word/phrase)
        shortest = min(segments, key=lambda s: len(s.split()))
        # If shortest is still very long (>5 words), take just the first 3 words as fallback
        words_in_shortest = shortest.split()
        if len(words_in_shortest) > 5:
            shortest = " ".join(words_in_shortest[:3]) + "…"
        return re.sub(r"\s+", " ", shortest).strip()

    def build_translation(self, analysis: list[dict],
                          direction: str = "goa2de") -> str:
        """
        Erzeugt die kompakte Übersetzung.
        goa2de → gibt die deutsche/englische Kernbedeutung aus
        de2goa → gibt das Goa'uld-Wort aus
        Stop words (skipped=True) werden stillschweigend ignoriert.
        """
        parts: list[str] = []
        for item in analysis:
            # Stop words & unmatched tokens
            if item.get("skipped"):
                continue        # Artikel etc. still schweigend überspringen
            if not item["found"]:
                parts.append(f"[{item['token']}?]")
                continue

            prim = item["primary"]

            if direction == "de2goa":
                word = prim["goauld"].strip()
                if word:
                    parts.append(word)
            else:
                # Prefer DE-lang entries for meaning output
                best = prim
                for alt in item["alternatives"]:
                    if alt.get("lang") == "de" and prim.get("lang") != "de":
                        best = alt
                        break
                # Multi-word token = phrase match → full meaning; single token → extract core
                if " " in item["token"]:
                    # Phrase match: clean up but don't shorten
                    m = best["meaning"].strip().strip('"\'„"').strip()
                    m = re.sub(r"\s*\([^)]*\)\s*", " ", m).strip()
                    m = re.sub(r"\s+", " ", m).strip()
                else:
                    m = self._extract_core_meaning(best["meaning"])
                if m:
                    parts.append(m)
        return " ".join(parts) if parts else "—"
