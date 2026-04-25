# Migration Notes — Goa'uld Translator Mobile

## Phase 0
- [2026-04-25] Toolchain validiert. Python 3.14.3, Flet 0.80.5

## Phase 1 — Engine-Extraktion
- [2026-04-25] Engine-Module existieren bereits und wurden validiert:
  - `goauld_engine/__init__.py` — Export aller öffentlichen Funktionen
  - `goauld_engine/parser.py` — Markdown-Parser für Dictionaries
  - `goauld_engine/resources.py` — Asset-Pfadauflösung
  - `goauld_engine/lexicon.py` — Lexicon-Loader (YAML + Markdown)
  - `goauld_engine/search.py` — Fuzzy-Search-Engine
  - `goauld_engine/lemma.py` — Deutsches Lemma-System
  - `goauld_engine/translator.py` — Übersetzungsfunktionen
  - `goauld_engine/analyzer.py` — Satzanalyse (Debrief)

## Phase 2 — Tests
- [2026-04-25] 10 von 10 Tests bestanden:
  - `test_lexicon_loads` — 3467 Einträge geladen
  - `test_lexicon_has_de_map` — 273 DE→Goa'uld-Mappings
  - `test_jaffa_kree` — Polyseme Übersetzung
  - `test_tau_ri` — Tau'ri = Mensch
  - `test_de2goa_simple` — DE→GOA Übersetzung
  - `test_de_lemma_basics` — Lemma-Erkennung
  - `test_de_lemma_plural` — Plural-Singular
  - `test_search_engine_finds_jaffa` — SearchEngine Treffer
  - `test_sentence_analyzer_runs` — Satzanalyse
  - `test_phrase_priority` — Multi-Wort-Phrasen

## Phase 3 — Skeleton
- [2026-04-25] Flet-Skeleton erstellt:
  - `pyproject.toml` — Flet 0.80.5 Konfiguration
  - `app/__init__.py` — Package-Init
  - `app/main.py` — Entry Point

## Phase 4 — UI-Implementation
- [2026-04-25] Drei Tabs implementiert:
  - **Briefing**: Such-Eingabe, Ergebnis-Liste, Detail-Karte
  - **Debrief**: Satzanalyse mit Token-Aufschlüsselung
  - **Live**: Echtzeit-Übersetzung mit 300ms Debounce

### Abweichungen vom Fahrplan:
1. `ft.Tabs` API in Flet 0.80.5 verwendet `content` und `length` statt `tabs`
2. `ft.Tab` verwendet `label` statt `text` (wird nicht verwendet, da Tabs manuell gerendert)
3. `SearchEngine.search()` Parameter heißt `max_results` statt `limit`
4. `ft.ElevatedButton` ist deprecated, durch `ft.Button` ersetzt
5. `_make_token_row` muss Dictionaries aus `alternatives` verarbeiten, keine Strings

## Phase 5 — Theming
- [2026-04-25] Farbpalette zentralisiert in `app/theme.py`:
  - Gate-Blau (#0a1628) als Hintergrund
  - SGC-Gold (#d4af37) als Akzent
  - Wormhole-Blau (#3a7bc8) für Secondary
  - Orange (#e8743c) für Warnungen

## Offene Entscheidungen
- [ ] Mono-Font: Courier New (System) vs. JetBrains Mono (custom)
- [ ] App-Icon: Platzhalter vs. echtes Stargate-Glyph

## Blocker
- (keine)

## Bekannte Probleme
1. Flet 0.80.5 Tabs-API weicht vom Fahrplan ab (siehe Phase 4)
2. `page.assets_dir` ist nur auf Mobile verfügbar, Desktop nutzt fallback Pfad
3. Deprecation-Warnungen für `ElevatedButton` (bereits behoben)
