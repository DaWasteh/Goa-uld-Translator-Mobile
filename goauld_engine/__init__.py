# -*- coding: utf-8 -*-
"""Goa'uld Linguistic Engine — Public API."""

from .lexicon import load_full_lexicon, LexiconResult
from .search import SearchEngine
from .analyzer import SentenceAnalyzer
from .translator import build_mapping, translate_text, DE_GOAULD_MAP
from .lemma import de_lemma_candidates, GERMAN_STOP_WORDS
from .resources import get_app_dir
from .parser import parse_markdown_dictionary, parse_de_map_from_entries

__all__ = [
    "load_full_lexicon",
    "LexiconResult",
    "SearchEngine",
    "SentenceAnalyzer",
    "build_mapping",
    "translate_text",
    "DE_GOAULD_MAP",
    "de_lemma_candidates",
    "GERMAN_STOP_WORDS",
    "get_app_dir",
    "parse_markdown_dictionary",
    "parse_de_map_from_entries",
]
