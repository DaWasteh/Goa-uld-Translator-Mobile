# -*- coding: utf-8 -*-
"""Token-by-token sentence analysis with curated YAML primary maps."""

from __future__ import annotations

import logging
import re
from typing import Optional

from . import translator
from .lemma import (
    ENGLISH_ARTICLES,
    ENGLISH_AUXILIARIES,
    ENGLISH_PREPOSITIONS,
    ENGLISH_STOP_WORDS,
    GERMAN_ARTICLES,
    GERMAN_AUXILIARIES,
    GERMAN_PREPOSITIONS,
    GERMAN_STOP_WORDS,
    STOP_WORDS_BY_LANG,
    de_lemma_candidates,
    detect_lang,
    en_lemma_candidates,
    normalize_lookup,
)
from .search import SearchEngine

log = logging.getLogger(__name__)


class SentenceAnalyzer:
    """
    Analyze sentences token by token.

    Translation mode is intentionally stricter than free-form search: multi-word
    spans are consumed only by exact primary-map hits or exact dictionary
    phrases. Prefix/fuzzy matches remain search suggestions, not automatic
    translation units.
    """

    _WORD_RE = re.compile(r"^[\w'äöüÄÖÜß]+$", re.UNICODE)

    def __init__(self, entries: list[dict] | SearchEngine) -> None:
        self.engine = entries if isinstance(entries, SearchEngine) else SearchEngine(entries)

    def is_sentence(self, text: str) -> bool:
        return len(text.strip().split()) > 1

    def _language_order(self, lang_pref: str) -> list[str]:
        primary = "en" if lang_pref == "en" else "de"
        secondary = "de" if primary == "en" else "en"
        return [primary, secondary]

    @staticmethod
    def _stop_reason(token: str, lang: str) -> str:
        low = normalize_lookup(token)
        if lang == "en":
            if low in ENGLISH_ARTICLES:
                return "article"
            if low in ENGLISH_AUXILIARIES:
                return "auxiliary"
            if low in ENGLISH_PREPOSITIONS:
                return "preposition"
            return "function"
        if low in GERMAN_ARTICLES:
            return "Artikel"
        if low in GERMAN_AUXILIARIES:
            return "Hilfsverb"
        if low in GERMAN_PREPOSITIONS:
            return "Präposition"
        return "Funktionswort"

    def _is_stop_word(self, token: str, lang_pref: str) -> bool:
        lang = "en" if lang_pref == "en" else "de"
        return normalize_lookup(token) in STOP_WORDS_BY_LANG[lang]

    def _lemma_candidates(self, token: str, lang: str) -> list[str]:
        return en_lemma_candidates(token) if lang == "en" else de_lemma_candidates(token)

    @staticmethod
    def _entry_rank(entry: dict, lang_pref: str) -> tuple[int, int, int, int]:
        lang_bonus = 10 if entry.get("lang") == lang_pref else 0
        priority = int(entry.get("priority", 0) or 0)
        source = str(entry.get("source", ""))
        source_priority = SearchEngine._SOURCE_PRIORITY.get(source, 0)
        exact_phrase = 1 if entry.get("phrase_exact") else 0
        return priority, source_priority, lang_bonus, exact_phrase

    def _find_entry_metadata(self, goauld: str, meaning_key: str, lang: str) -> Optional[dict]:
        goauld_low = normalize_lookup(goauld)
        meaning_low = normalize_lookup(meaning_key)
        candidates = [
            e for e in self.engine.entries
            if normalize_lookup(str(e.get("goauld", ""))) == goauld_low
            and normalize_lookup(str(e.get("meaning", ""))) == meaning_low
            and e.get("lang") == lang
        ]
        if not candidates:
            candidates = [
                e for e in self.engine.entries
                if normalize_lookup(str(e.get("goauld", ""))) == goauld_low
                and e.get("lang") == lang
            ]
        if not candidates:
            return None
        return max(candidates, key=lambda e: self._entry_rank(e, lang))

    def _synthetic_map_entry(self, token: str, matched_key: str, goauld: str,
                             lang: str, confidence: float = 0.94) -> dict:
        metadata = self._find_entry_metadata(goauld, matched_key, lang)
        entry = dict(metadata) if metadata else {
            "goauld": goauld,
            "meaning": token,
            "section": "YAML primary map",
            "source": "YAML",
            "lang": lang,
        }
        entry.update({
            "goauld": goauld,
            "meaning": token,
            "lang": lang,
            "matched_key": matched_key,
            "match_type": "primary_map",
            "confidence": confidence,
        })
        return entry

    @staticmethod
    def _select_lexical_override(matched_key: str, goauld: str, lang: str,
                                 context_words: list[str]) -> str:
        """Rule-based lexical selection for high-conflict glosses."""
        del lang
        key = normalize_lookup(matched_key)
        ctx = {normalize_lookup(w) for w in context_words}

        collective = {
            "menschheit", "menschenvolk", "volk der menschen", "menschliche rasse",
            "humanity", "humankind", "human race", "human people", "race", "rasse",
        }
        generic = {
            "menschlich", "generischer mensch", "mensch als gattung", "person",
            "generic human", "human as species", "human person", "human (generic)",
        }
        slave_status = {"menschlicher sklave", "sklave", "diener", "human slave", "slave", "servant"}
        human_default = {"mensch", "menschen", "human", "humans", "erdmensch", "erdmenschen"}
        if key in collective or ctx.intersection(collective):
            return "Tap'tar"
        if key in slave_status or ctx.intersection(slave_status):
            return "Lo'taur"
        if key in generic:
            return "Tar"
        if key in human_default:
            return "Tau'ri"

        if key in {"nicht", "not", "don't", "dont", "do not", "does not", "did not"}:
            return "ia"
        if key in {"kein", "keine", "keinen", "keinem", "keiner", "keines", "nein", "no", "none", "not any"}:
            return "Ka"

        if key in {"groß", "grosse", "große", "gross", "big", "large"}:
            physical_context = {
                "körper", "koerper", "physisch", "schiff", "haus", "raum", "tor",
                "body", "physical", "ship", "house", "room", "gate",
            }
            divine_context = {"gott", "goa'uld", "macht", "mächtig", "god", "power", "powerful"}
            if ctx.intersection(physical_context):
                return "Tun'le"
            if ctx.intersection(divine_context):
                return "Onak"

        return goauld

    def _lookup_primary_map(self, token: str, lang_pref: str,
                            context_words: list[str], *,
                            allow_lemma: bool) -> tuple[Optional[dict], list[dict]]:
        token_key = normalize_lookup(token)
        for lang in self._language_order(lang_pref):
            keys = [token_key]
            if allow_lemma and " " not in token_key:
                keys = self._lemma_candidates(token_key, lang)
            for key in keys:
                goauld = translator.PRIMARY_GOAULD_MAPS.get(lang, {}).get(key)
                if not goauld:
                    continue
                selected = self._select_lexical_override(key, goauld, lang, context_words)
                primary = self._synthetic_map_entry(token, key, selected, lang)
                alternatives: list[dict] = []
                for alt in translator.SECONDARY_GOAULD_MAPS.get(lang, {}).get(key, [])[:5]:
                    if normalize_lookup(alt) == normalize_lookup(selected):
                        continue
                    alternatives.append(self._synthetic_map_entry(token, key, alt, lang, confidence=0.72))
                return primary, alternatives
        return None, []

    def _exact_engine_matches(self, phrase: str, direction: str,
                              lang_pref: str) -> list[dict]:
        phrase_low = normalize_lookup(phrase)
        field = "goauld" if direction == "goa2de" else "meaning"
        matches = [
            e for e in self.engine.entries
            if normalize_lookup(str(e.get(field, ""))) == phrase_low
        ]
        lang_order = self._language_order(lang_pref)

        def sort_key(entry: dict) -> tuple[int, int, int, int, int]:
            entry_lang = str(entry.get("lang", ""))
            lang_score = len(lang_order) - lang_order.index(entry_lang) if entry_lang in lang_order else 0
            priority, source_priority, lang_bonus, exact_phrase = self._entry_rank(entry, lang_pref)
            return lang_score, priority, source_priority, lang_bonus, exact_phrase

        matches.sort(key=sort_key, reverse=True)
        return matches

    def _append_skip(self, result: list[dict], token: str, lang_pref: str) -> None:
        lang = "en" if lang_pref == "en" else "de"
        result.append({
            "token": token,
            "raw": token,
            "primary": None,
            "alternatives": [],
            "found": False,
            "skipped": True,
            "skip_reason": self._stop_reason(token, lang),
            "confidence": 1.0,
        })

    def analyze(self, text: str, direction: str, lang_pref: str = "de") -> list[dict]:
        raw_tokens = re.split(r"(\s+)", text.strip())
        words: list[str] = []
        for tok in raw_tokens:
            clean = tok.strip(".,!?;:()[]{}\"“”„")
            if clean and self._WORD_RE.match(clean):
                words.append(clean)

        if not words:
            return []

        # Satzsprache heuristisch bestimmen: Stopword-Tilgung folgt der
        # tatsächlichen Eingabesprache statt nur lang_pref (löst z. B.
        # EN-Artikel "the" bei lang_pref="de" korrekt auf).
        if direction == "de2goa":
            lang_pref = detect_lang(text)

        max_phrase = 6
        result: list[dict] = []
        i = 0

        while i < len(words):
            matched = False
            window = min(max_phrase, len(words) - i)

            if direction == "de2goa":
                if self._is_stop_word(words[i], lang_pref):
                    self._append_skip(result, words[i], lang_pref)
                    i += 1
                    continue

                for n in range(window, 1, -1):
                    phrase = " ".join(words[i:i + n])
                    primary, alternatives = self._lookup_primary_map(
                        phrase, lang_pref, words, allow_lemma=False,
                    )
                    if primary:
                        result.append({
                            "token": phrase,
                            "raw": phrase,
                            "primary": primary,
                            "alternatives": alternatives[:3],
                            "found": True,
                            "skipped": False,
                            "confidence": primary.get("confidence", 0.94),
                        })
                        i += n
                        matched = True
                        break

                if matched:
                    continue

                for n in range(window, 1, -1):
                    phrase = " ".join(words[i:i + n])
                    matches = self._exact_engine_matches(phrase, direction, lang_pref)
                    if matches:
                        primary = dict(matches[0])
                        primary.setdefault("match_type", "exact_phrase")
                        primary.setdefault("confidence", 0.9)
                        result.append({
                            "token": phrase,
                            "raw": phrase,
                            "primary": primary,
                            "alternatives": matches[1:3],
                            "found": True,
                            "skipped": False,
                            "confidence": primary.get("confidence", 0.9),
                        })
                        i += n
                        matched = True
                        break

                if matched:
                    continue

                token = words[i]
                primary, alternatives = self._lookup_primary_map(
                    token, lang_pref, words, allow_lemma=True,
                )
                if not primary:
                    matches = self._exact_engine_matches(token, direction, lang_pref)
                    if matches:
                        primary = dict(matches[0])
                        primary.setdefault("match_type", "exact_token")
                        primary.setdefault("confidence", 0.86)
                        alternatives = matches[1:4]

                result.append({
                    "token": token,
                    "raw": token,
                    "primary": primary,
                    "alternatives": alternatives[:3] if alternatives else [],
                    "found": primary is not None,
                    "skipped": False,
                    "confidence": primary.get("confidence", 0.0) if primary else 0.0,
                })
                i += 1
                continue

            for n in range(window, 0, -1):
                phrase = " ".join(words[i:i + n])
                matches = self._exact_engine_matches(phrase, direction, lang_pref)
                if matches:
                    primary = dict(matches[0])
                    primary.setdefault("match_type", "exact_phrase" if n > 1 else "exact_token")
                    primary.setdefault("confidence", 0.9 if n > 1 else 0.86)
                    result.append({
                        "token": phrase,
                        "raw": phrase,
                        "primary": primary,
                        "alternatives": matches[1:4],
                        "found": True,
                        "skipped": False,
                        "confidence": primary.get("confidence", 0.9),
                    })
                    i += n
                    matched = True
                    break

            if not matched:
                result.append({
                    "token": words[i],
                    "raw": words[i],
                    "primary": None,
                    "alternatives": [],
                    "found": False,
                    "skipped": False,
                    "confidence": 0.0,
                })
                i += 1

        return result

    @staticmethod
    def _extract_core_meaning(meaning: str) -> str:
        m = meaning.strip()
        m = re.sub(r"^[\-–▸→✦◆◉☓\s]+", "", m)
        m = re.sub(r"\s*\([^)]*\)\s*", " ", m)
        segments = re.split(r"\s*[;—/,]\s*", m)
        segments = [s.strip().strip('"\'„"').strip() for s in segments if s.strip()]
        if not segments:
            return ""
        shortest = min(segments, key=lambda s: len(s.split()))
        words_in_shortest = shortest.split()
        if len(words_in_shortest) > 5:
            shortest = " ".join(words_in_shortest[:3]) + "…"
        return re.sub(r"\s+", " ", shortest).strip()

    @staticmethod
    def _is_canonical_entry(entry: dict) -> bool:
        tier = str(entry.get("tier", "")).lower()
        source = str(entry.get("source", "")).lower()
        return tier.startswith("canon") or source in {
            "sg1-kanon", "kanon", "kanon-ext", "rpg-lexikon",
        }

    @staticmethod
    def _apply_goauld_style(text: str) -> str:
        if not text or text == "—":
            return text
        if "Tal shak!" in text and not text.endswith("Kree!"):
            return f"{text} Kree!"
        return text

    def build_translation(self, analysis: list[dict],
                          direction: str = "goa2de",
                          mode: str = "extended") -> str:
        """
        Build compact translation from analysis.

        Modes:
          extended     Canon + Fanon (default)
          canonical    Prefer/require canonical entries
          literal      Strict token-by-token output
          goauld_style Extended output plus light martial/register polish
        """
        parts: list[str] = []
        for item in analysis:
            if item.get("skipped"):
                continue
            if not item.get("found"):
                parts.append(f"[{item['token']}?]")
                continue

            prim = item["primary"]
            if not prim:
                parts.append(f"[{item['token']}?]")
                continue

            if direction == "de2goa":
                chosen = prim
                if mode == "canonical" and not self._is_canonical_entry(prim):
                    canonical_alt = next(
                        (alt for alt in item.get("alternatives", []) if self._is_canonical_entry(alt)),
                        None,
                    )
                    if canonical_alt is None:
                        parts.append(f"[{item['token']}?]")
                        continue
                    chosen = canonical_alt
                word = str(chosen.get("goauld", "")).strip()
                if word:
                    parts.append(word)
            else:
                best = prim
                for alt in item.get("alternatives", []):
                    if alt.get("lang") == "de" and prim.get("lang") != "de":
                        best = alt
                        break
                if " " in item["token"]:
                    m = str(best.get("meaning", "")).strip().strip('"\'„"').strip()
                    m = re.sub(r"\s*\([^)]*\)\s*", " ", m).strip()
                    m = re.sub(r"\s+", " ", m).strip()
                else:
                    m = self._extract_core_meaning(str(best.get("meaning", "")))
                if m:
                    parts.append(m)
        output = " ".join(parts) if parts else "—"
        if direction == "de2goa" and mode == "goauld_style":
            return self._apply_goauld_style(output)
        return output
    