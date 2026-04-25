# Fahrplan: Goa'uld Translator Mobile — Android-APK via Flet

**Projekt:** Goa'uld Linguistic Interface — Mobile Edition
**Toolchain:** Python 3.12 + Flet 0.80+ + Flutter 3.29+ + Android SDK
**Zielartefakt:** `goauld_translator_mobile-release.apk` (signiert, installierbar auf Android 8+)
**Arbeitsverzeichnis:** `C:/LAB/Goa'uld Translator Mobile/`
**Bezugsversion Desktop-Original:** v0.2.6 (CTK-basiert, NICHT verändern)

---

## 0 · Vorwort & verbindliche Regeln für die Ausführung

Dieser Fahrplan ist für ein lokales Coder-LLM (Qwen3-Coder oder vergleichbar) geschrieben. Die folgenden Regeln sind **NICHT optional** und müssen für jede Phase eingehalten werden:

### Regel 1 — Atomare Schritte
Jede Phase ist in nummerierte Schritte unterteilt. Ein Schritt wird **vollständig abgeschlossen und validiert**, bevor der nächste begonnen wird. Niemals zwei Schritte parallel anfangen.

### Regel 2 — Validierung ist Pflicht
Jede Phase endet mit einem Block `Validierung`. Die dort genannten Befehle MÜSSEN ausgeführt werden und das genannte Ergebnis liefern. Wenn die Validierung fehlschlägt: STOPP, Fehler dokumentieren, NICHT mit der nächsten Phase beginnen.

### Regel 3 — Niemals erfinden
Wenn dieser Fahrplan eine Bibliothek, eine Funktion oder einen Pfad nennt, dann existiert dieser Name exakt so. Niemals eine ähnlich klingende Alternative substituieren ("ähnlich wie X" → ist NICHT erlaubt). Wenn du unsicher bist: dokumentiere die Unsicherheit am Ende der Datei `MIGRATION_NOTES.md` und warte auf manuelle Entscheidung.

### Regel 4 — Originaldateien sind read-only
Die Dateien `goauld_translator.py` (3464 Zeilen, CTK-Version), `yaml_loader.py`, `goauld_lexicon.yaml`, alle vier Markdown-Dictionaries und beide LANGUAGE_GUIDE-Files dürfen **nicht modifiziert werden**. Sie sind die Quelle der Wahrheit. Neue Module entstehen daneben, niemals durch Edits am Original.

### Regel 5 — Keine GUI-Logik in der Engine
Phase 1 extrahiert die Engine. Während dieser Extraktion darf NICHTS aus dem `tkinter`, `customtkinter` oder `tk` Namespace in die neuen Engine-Module gelangen. Wenn eine Funktion auf `self.root`, `ctk.`, `tk.`, `messagebox`, `filedialog` oder ähnliches zugreift: gehört NICHT in die Engine. Punkt.

### Regel 6 — Pfad-Konventionen
- Windows-Pfade in der README mit Forward-Slashes notieren (`C:/LAB/...`).
- In Python-Code IMMER `pathlib.Path` verwenden, niemals String-Konkatenation mit `\` oder `/`.
- Asset-Bundling in Flet erfolgt über `assets/`-Verzeichnis (siehe Phase 4).

### Regel 7 — UTF-8 überall
Alle neuen Python-Dateien beginnen mit:
```python
# -*- coding: utf-8 -*-
```
Alle `open(...)`-Aufrufe verwenden `encoding="utf-8"`. Markdown-Files mit Umlauten werden NICHT als ASCII gelesen.

### Regel 8 — Wenn ein Schritt fehlschlägt
1. NICHT raten, NICHT improvisieren.
2. Fehlermeldung wörtlich in `MIGRATION_NOTES.md` protokollieren.
3. Den Schritt klar markieren: `BLOCKED — manuelle Entscheidung erforderlich`.
4. Mit dem nächsten Schritt **nur dann** fortfahren, wenn der Fahrplan dies explizit erlaubt (z. B. "wenn fehlschlägt, mit Schritt X fortfahren").

---

## 1 · Glossar

| Begriff | Bedeutung |
|---------|-----------|
| **Engine** | Reine Python-Logik ohne GUI: Parser, SearchEngine, Translator, SentenceAnalyzer, Lemma-Modul, Lexicon-Loader. |
| **Frontend** | Flet-basierte UI in `app/main.py` und Submodulen. |
| **Asset** | Eine Datei (Markdown, YAML, Font), die zur Laufzeit aus dem APK gelesen wird. Lebt unter `assets/` im Source-Tree, wird beim Build mit eingepackt. |
| **DE_MAP** | Direktes Deutsch→Goa'uld-Mapping aus den Dictionaries (~1500 Einträge). Hat Priorität vor SearchEngine bei `de2goa`. |
| **Briefing** | Detail-Tab: zeigt einen ausgewählten Eintrag mit Etymologie, Quellen, semantischen Verwandten. Entspricht im Original dem CTK-Tab `◈ BRIEFING`. |
| **Debrief** | Satzanalyse-Tab: zerlegt einen Satz Token-für-Token. Entspricht im Original `⊕ DEBRIEF`. |
| **Live** | Echtzeit-Übersetzungs-Tab. Entspricht im Original `⚡ LIVE-TRANSMISSION`. |
| **CTK-Original** | Die Datei `goauld_translator.py` mit 3464 Zeilen. NICHT anfassen. |
| **`pyproject.toml`** | Flet-Konfigurationsdatei. Siehe Phase 3. |

---

## 2 · Phasenübersicht

```
Phase 0 — Toolchain-Setup                  (1 h)
Phase 1 — Engine extrahieren               (4–6 h)
Phase 2 — Engine-Tests anlegen             (2 h)
Phase 3 — Flet-Projekt-Skeleton            (1 h)
Phase 4 — UI-Implementation                (6–8 h)
Phase 5 — Theming (SGC-Look)               (3 h)
Phase 6 — Lokal testen + APK bauen         (2–3 h)
```

Geschätzter Gesamtaufwand: 19–24 h für ein erfahrenes Coder-Modell ohne Blocker.

---

## Phase 0 — Toolchain-Setup

**Ziel:** Verifizieren, dass Python, Flet, Flutter und Android-SDK auf dem Entwicklungsrechner verfügbar sind.

### 0.1 — Python-Version prüfen

```powershell
python --version
```

**Erwartete Ausgabe:** `Python 3.12.x` oder `Python 3.13.x`.

**Wenn die Ausgabe abweicht:** Python 3.12.x von python.org installieren. Flet ist mit 3.10–3.13 kompatibel, aber 3.12 ist die getestete Referenz für diesen Fahrplan. **Python 3.14 NICHT verwenden** — bekannte Inkompatibilität mit serious_python (Flets Build-Tool für Mobile).

### 0.2 — Virtuelles Environment anlegen

Im Verzeichnis `C:/LAB/Goa'uld Translator Mobile/`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

**Erwartete Ausgabe:** Prompt zeigt jetzt `(.venv)` als Prefix.

### 0.3 — Flet installieren

```powershell
pip install "flet[all]==0.80.5" pyyaml
```

**Erwartete Ausgabe:** `Successfully installed flet-0.80.5 ...`

> **Versions-Pin:** Flet 0.80.5 ist die am Stichtag dieses Fahrplans aktuelle stabile Version. NICHT auf eine prerelease-Version (`0.80.6.devXXX`) wechseln — bekannte Probleme mit Flutter-Template-Mismatch.

### 0.4 — Flet-CLI verifizieren

```powershell
flet --version
```

**Erwartete Ausgabe:** `flet, version 0.80.5` (oder die installierte Version).

### 0.5 — Flutter prüfen (optional, wird sonst auto-installiert)

```powershell
flutter --version
```

**Wenn Flutter nicht gefunden:** Das ist OK. Flet's `build`-Befehl installiert Flutter beim ersten Aufruf automatisch in `$HOME/.flutter` oder einem ähnlichen Pfad. Wenn Flutter aber bereits manuell installiert ist, muss es ≥ 3.29.0 sein.

### 0.6 — JDK 17 prüfen

```powershell
java -version
```

**Erwartete Ausgabe:** `openjdk version "17.x.x"` oder `java version "17.x.x"`.

**Wenn nicht installiert oder falsche Version:** Auch hier installiert Flet beim ersten `flet build apk` automatisch JDK 17 nach `$HOME/java/17.0.13+11`. Manuelle Installation nicht nötig.

### 0.7 — Hello-World-Smoketest

Erstelle `C:/LAB/Goa'uld Translator Mobile/_smoketest.py`:

```python
# -*- coding: utf-8 -*-
import flet as ft

def main(page: ft.Page):
    page.title = "Smoketest"
    page.add(ft.Text("Flet läuft.", size=20))

ft.app(target=main)
```

Ausführen:

```powershell
python _smoketest.py
```

**Erwartetes Verhalten:** Ein Desktop-Fenster öffnet sich mit dem Text "Flet läuft.". Fenster schließen, Datei kann gelöscht werden.

**Wenn das Fenster nicht erscheint:** STOPP. Flet-Installation defekt. In `MIGRATION_NOTES.md` dokumentieren und manuell beheben, bevor Phase 1 begonnen wird.

### Validierung Phase 0

Folgende Befehle müssen alle ohne Fehler durchlaufen:

```powershell
python --version          # zeigt 3.12.x oder 3.13.x
flet --version            # zeigt 0.80.5
pip show flet | findstr Version    # zeigt Version: 0.80.5
pip show pyyaml | findstr Version  # zeigt Version: 6.x
```

`_smoketest.py` zeigt ein funktionierendes Flet-Fenster.

---

## Phase 1 — Engine extrahieren

**Ziel:** Die reine Übersetzungs-Logik aus `goauld_translator.py` (3464 Zeilen, CTK-gekoppelt) in ein eigenständiges, GUI-freies Python-Package `goauld_engine/` überführen. Das Original bleibt unangetastet.

### 1.1 — Ziel-Struktur anlegen

```
C:/LAB/Goa'uld Translator Mobile/
├── goauld_engine/
│   ├── __init__.py
│   ├── parser.py        # parse_markdown_dictionary, parse_de_map_from_entries, _clean
│   ├── resources.py     # _get_app_dir, _find_one, _find_all, find_md_files
│   ├── lexicon.py       # _load_lexicon, _load_mds, plus YAML-Loader-Bridge
│   ├── search.py        # class SearchEngine
│   ├── lemma.py         # _de_lemma_candidates und Stemming-Helpers
│   ├── translator.py    # build_mapping, translate_text, preserve_case
│   └── analyzer.py      # class SentenceAnalyzer
├── tests/               # später in Phase 2
├── app/                 # später in Phase 3
├── assets/              # später in Phase 3
├── goauld_translator.py # CTK-Original — NICHT ANFASSEN
├── goauld_lexicon.yaml  # NICHT ANFASSEN
├── yaml_loader.py       # NICHT ANFASSEN
├── Goa'uld-Dictionary.md
├── Goa'uld-Wörterbuch.md
├── Goa'uld-Fictionary.md
├── Goa'uld-Neologikum.md
└── ...
```

Die Verzeichnisse anlegen:

```powershell
mkdir goauld_engine, tests, app, assets
```

### 1.2 — Quellzeilen-Mapping (verbindlich)

Folgende Zeilen-Bereiche aus dem Originalcode `goauld_translator.py` werden in die jeweiligen Module verschoben. Diese Bereichsangaben sind **bindend** — Qwen muss sie übernehmen, NICHT eigene Vermutungen anstellen.

| Original-Zeilen | Inhalt | Zielmodul |
|-----------------|--------|-----------|
| 22–30 | Standard-Imports (`re, os, sys, argparse, difflib, logging, threading, pathlib, typing`) | je nach Modul nur was gebraucht wird |
| 33–41 | YAML-Loader-Import-Block | `lexicon.py` |
| 44–70 | `_setup_logging` + Initialisierung | NICHT in Engine — kommt in `app/main.py` (Phase 3) |
| 75–106 | CustomTkinter-Import-Block | KOMPLETT VERWERFEN — wird nicht gebraucht |
| 108–115 | tkinter-Import-Block | KOMPLETT VERWERFEN |
| 122–245 | Farbpalette `C`, Fonts | KOMPLETT VERWERFEN — wird in Phase 5 für Flet neu definiert |
| 288–296 | `_clean(text)` | `parser.py` |
| 297–379 | `parse_markdown_dictionary(filepath)` | `parser.py` |
| 380–423 | `parse_de_map_from_entries(entries)` | `parser.py` |
| 428–612 | `class SearchEngine` | `search.py` |
| 619–789 | `_de_lemma_candidates` + alle Lemma-Helper | `lemma.py` |
| 816–1107 | `class SentenceAnalyzer` | `analyzer.py` |
| 1122–1130 | `preserve_case` | `translator.py` |
| 1132–1143 | `build_mapping` | `translator.py` |
| 1144–1174 | `translate_text` | `translator.py` |
| 1179–1190 | `_get_app_dir` | `resources.py` |
| 1192–1233 | `_find_one`, `_find_all` | `resources.py` |
| 1234–1248 | `find_md_file`, `find_md_files` | `resources.py` |
| 1250–1284 | `_load_lexicon` | `lexicon.py` |
| 1285–1419 | `_load_mds` | `lexicon.py` |
| 1420–3328 | `class GoauldApp` | KOMPLETT VERWERFEN — UI wird in Phase 4 neu gebaut |
| 3332–3373 | `run_cli` | KOMPLETT VERWERFEN — kein CLI in Mobile |
| 3379–3461 | `main()` | KOMPLETT VERWERFEN |

> **Wichtig:** Diese Zeilenangaben beziehen sich auf die Originaldatei mit 3464 Zeilen. Wenn die Datei mehr oder weniger Zeilen hat, muss Qwen die genannten Funktionen anhand ihrer **Namen** finden, nicht der Zeilennummern.

### 1.3 — `goauld_engine/__init__.py` anlegen

```python
# -*- coding: utf-8 -*-
"""Goa'uld translation engine — pure Python, no GUI dependencies."""

from .lexicon import load_full_lexicon, LexiconResult
from .search import SearchEngine
from .translator import translate_text, build_mapping, preserve_case
from .analyzer import SentenceAnalyzer
from .parser import parse_markdown_dictionary, parse_de_map_from_entries
from .resources import find_md_files, get_app_dir
from .lemma import de_lemma_candidates

__version__ = "0.3.0-mobile"

__all__ = [
    "load_full_lexicon",
    "LexiconResult",
    "SearchEngine",
    "translate_text",
    "build_mapping",
    "preserve_case",
    "SentenceAnalyzer",
    "parse_markdown_dictionary",
    "parse_de_map_from_entries",
    "find_md_files",
    "get_app_dir",
    "de_lemma_candidates",
]
```

### 1.4 — `goauld_engine/parser.py` anlegen

Inhalt: Funktionen `_clean`, `parse_markdown_dictionary`, `parse_de_map_from_entries` aus dem Original. Imports am Datei-Anfang:

```python
# -*- coding: utf-8 -*-
"""Markdown-Parser für die Goa'uld-Dictionaries."""

import re
from pathlib import Path
from typing import Optional
```

Dann die drei Funktionen 1:1 aus dem Original übernehmen. Beim Kopieren:
- `log.warning(...)` Aufrufe ersetzen durch `import logging; log = logging.getLogger(__name__); log.warning(...)`
- Internes `import re as _re2` belassen falls vorhanden
- Funktionssignaturen nicht verändern

### 1.5 — `goauld_engine/resources.py` anlegen

```python
# -*- coding: utf-8 -*-
"""Auflösung von Asset-Pfaden für Lexicon-Dateien.

Anders als die Desktop-Version lebt Mobile in einem Flet-App-Bundle.
Die Funktion ``get_app_dir()`` löst den korrekten Lese-Pfad zu Assets auf,
sowohl im Entwicklungsmodus (Source-Tree) als auch im gepackten APK.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


def get_app_dir() -> Path:
    """Liefert das Verzeichnis, in dem Asset-Dateien gesucht werden.

    Reihenfolge:
    1. Wenn ``FLET_APP_STORAGE_DATA`` (oder ähnliches) gesetzt: dort suchen.
    2. Wenn ``sys.frozen`` (PyInstaller-Desktop): neben der EXE.
    3. Sonst: das Eltern-Verzeichnis dieses Files (Projekt-Root).
    """
    # Im Flet-Mobile-Build leben Assets im Bundle-Root
    frozen = getattr(sys, "frozen", False)
    if frozen:
        return Path(sys.executable).parent
    # Repo-Root: zwei Ebenen über dieser Datei (goauld_engine/resources.py)
    return Path(__file__).resolve().parent.parent


def _find_all(candidates: list[str], hint: Optional[str] = None) -> list[str]:
    # ↓ Hier den Original-Funktionskörper aus goauld_translator.py einfügen.
    # Original: Zeilen 1198–1232.
    # WICHTIG: alle Verweise auf _get_app_dir() durch get_app_dir() ersetzen.
    ...


def find_md_files(hint_en: Optional[str] = None,
                  hint_de: Optional[str] = None) -> list[str]:
    # ↓ Original-Funktionskörper aus Zeilen 1239–1248 einfügen.
    ...
```

> Die Platzhalter `...` sind exakt die Stellen, an denen Qwen den **wörtlichen Originalcode** der genannten Funktion einsetzt. Keine Umformulierungen, keine "Optimierungen". Bit-genau kopieren, nur die genannten Anpassungen vornehmen.

### 1.6 — `goauld_engine/lexicon.py` anlegen

Diese Datei vereint YAML-Loader und MD-Loader hinter einer einzelnen API:

```python
# -*- coding: utf-8 -*-
"""Lexicon-Loader: YAML bevorzugt, Markdown als Fallback."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .parser import parse_markdown_dictionary, parse_de_map_from_entries
from .resources import find_md_files, get_app_dir

log = logging.getLogger(__name__)

# YAML-Loader optional importieren (wie im Original)
try:
    # yaml_loader.py liegt im Projekt-Root, nicht im Package.
    # Beim Bundling muss er entweder mitkopiert oder hier inline ersetzt werden.
    import sys
    sys.path.insert(0, str(get_app_dir()))
    from yaml_loader import find_lexicon_yaml, load_lexicon_yaml  # type: ignore
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    log.warning("yaml_loader.py nicht gefunden — Fallback auf Markdown-Loader.")


@dataclass
class LexiconResult:
    """Konsolidiertes Ergebnis des Lexicon-Loadings."""
    entries: list[dict] = field(default_factory=list)
    md_paths: list[str] = field(default_factory=list)
    de_map: dict[str, str] = field(default_factory=dict)
    en_map: dict[str, str] = field(default_factory=dict)
    de_to_en: dict[str, str] = field(default_factory=dict)
    en_to_de: dict[str, str] = field(default_factory=dict)
    source: str = "unknown"  # "yaml" oder "markdown"


def load_full_lexicon(md_hint: Optional[str] = None) -> LexiconResult:
    """Lädt das vollständige Lexicon. YAML hat Vorrang.

    Returns:
        LexiconResult mit ``entries``, ``md_paths``, ``de_map`` etc.
    """
    # 1. YAML versuchen
    if YAML_AVAILABLE:
        yaml_path = find_lexicon_yaml(get_app_dir())
        if yaml_path is not None:
            try:
                yaml_data = load_lexicon_yaml(yaml_path)
                # ↓ Hier den Code aus _load_lexicon (Original Z. 1250–1284)
                # einfügen, der yaml_data in entries/de_map/en_map konvertiert.
                # Endergebnis: LexiconResult mit source="yaml".
                ...
            except Exception as e:
                log.warning("YAML-Load fehlgeschlagen: %s — Fallback auf MD.", e)

    # 2. Markdown-Fallback
    md_paths = find_md_files(hint_en=md_hint, hint_de=md_hint)
    if not md_paths:
        log.error("Keine Lexicon-Dateien gefunden!")
        return LexiconResult(source="empty")

    # ↓ Hier den Code aus _load_mds (Original Z. 1285–1419) einfügen.
    # Endergebnis: LexiconResult mit source="markdown".
    ...
```

> **Aufmerksamkeit:** Der `yaml_loader.py` aus dem Original muss bei Mobile-Builds entweder **mitgepackt** werden (siehe Phase 6) oder seine zwei Funktionen werden inline in `lexicon.py` portiert. Empfehlung: mitpacken — minimaler Aufwand. Im Code wird er per `sys.path.insert(0, ...)` plus `from yaml_loader import ...` gefunden.

### 1.7 — `goauld_engine/search.py` anlegen

```python
# -*- coding: utf-8 -*-
"""Fuzzy-Search-Engine über das Lexicon."""

import re
import difflib
import logging
from typing import Optional

from .lemma import de_lemma_candidates

log = logging.getLogger(__name__)


class SearchEngine:
    # ↓ Klassenkörper aus Original-Zeilen 428–612 wörtlich übernehmen.
    # Anpassungen:
    #  - Aufrufe von _de_lemma_candidates(...) → de_lemma_candidates(...)
    #  - Logging-Aufrufe (log.X) erhalten bleiben
    ...
```

### 1.8 — `goauld_engine/lemma.py` anlegen

```python
# -*- coding: utf-8 -*-
"""Deutsches Lemma- und Stemming-System."""

import re

# ↓ Sämtliche Konstanten und Hilfsfunktionen aus Original Z. 619–789
# wörtlich kopieren. Die zentrale öffentliche Funktion ist
# _de_lemma_candidates — sie wird umbenannt zu de_lemma_candidates
# (ohne Unterstrich-Prefix), weil sie jetzt Teil der Public-API ist.

def de_lemma_candidates(word: str) -> list[str]:
    # ↓ Originalkörper von _de_lemma_candidates wörtlich einfügen.
    ...
```

### 1.9 — `goauld_engine/translator.py` anlegen

```python
# -*- coding: utf-8 -*-
"""Hochlevel-Übersetzungsfunktionen."""

import re
import logging
from typing import Optional

log = logging.getLogger(__name__)


def preserve_case(original: str, translated: str) -> str:
    # ↓ Original Z. 1122–1130 wörtlich.
    ...


def build_mapping(entries: list[dict], direction: str) -> dict[str, str]:
    # ↓ Original Z. 1132–1143 wörtlich.
    ...


def translate_text(text: str, mapping: dict[str, str],
                   direction: str = "goa2de") -> str:
    # ↓ Original Z. 1144–1174 wörtlich.
    ...
```

### 1.10 — `goauld_engine/analyzer.py` anlegen

```python
# -*- coding: utf-8 -*-
"""Token-für-Token-Satzanalyse für den Debrief-Tab."""

import re
import logging
from typing import Optional

from .search import SearchEngine
from .lemma import de_lemma_candidates

log = logging.getLogger(__name__)


class SentenceAnalyzer:
    # ↓ Klassenkörper aus Original Z. 816–1107 wörtlich übernehmen.
    # Anpassungen:
    #  - _de_lemma_candidates → de_lemma_candidates
    ...
```

### 1.11 — Erst-Test der Engine

Nach dem Anlegen aller Module: simpler Import-Test in einer REPL.

```powershell
cd "C:/LAB/Goa'uld Translator Mobile"
python -c "from goauld_engine import load_full_lexicon, SearchEngine; r = load_full_lexicon(); print(f'Loaded {len(r.entries)} entries, source={r.source}')"
```

**Erwartete Ausgabe:**
```
Loaded 5850 entries, source=yaml
```
(oder bei MD-Fallback: ~3454 entries, source=markdown).

**Wenn die Zahl 0 ist:** YAML wird nicht gefunden. Pfad in `resources.get_app_dir()` prüfen. In `MIGRATION_NOTES.md` dokumentieren.

**Wenn ImportError:** Eine Funktion wurde beim Kopieren übersehen. Stack-Trace lesen, fehlende Funktion identifizieren, im Original suchen, einfügen. NICHT raten.

### Validierung Phase 1

Drei Tests müssen passen:

```powershell
# Test 1: Engine importierbar
python -c "import goauld_engine; print(goauld_engine.__version__)"
# Erwartung: 0.3.0-mobile

# Test 2: Lexicon lädt
python -c "from goauld_engine import load_full_lexicon; r = load_full_lexicon(); assert len(r.entries) > 1000, f'Nur {len(r.entries)} Einträge'; print('OK', len(r.entries))"
# Erwartung: OK 3454 (oder höher)

# Test 3: Übersetzung funktioniert
python -c "from goauld_engine import load_full_lexicon, build_mapping, translate_text; r = load_full_lexicon(); m = build_mapping(r.entries, 'goa2de'); print(translate_text('Jaffa kree', m, 'goa2de'))"
# Erwartung: irgendwas mit "Krieger" und "Achtung" (genaue Strings vom Original abhängig)
```

Erst wenn alle drei Tests passen: weiter zu Phase 2.

---

## Phase 2 — Engine-Tests anlegen

**Ziel:** Pytest-basierte Regressionstests, die das Verhalten der Engine pinnen, BEVOR die UI-Schicht draufgesetzt wird. Wenn später etwas bricht, sieht man es sofort.

### 2.1 — Pytest installieren

```powershell
pip install pytest
```

### 2.2 — Datei `tests/__init__.py` (leer) anlegen

```powershell
New-Item -ItemType File -Path tests/__init__.py
```

### 2.3 — Datei `tests/test_engine.py` anlegen

```python
# -*- coding: utf-8 -*-
"""Regressionstests für goauld_engine."""

import pytest
from goauld_engine import (
    load_full_lexicon,
    build_mapping,
    translate_text,
    SearchEngine,
    SentenceAnalyzer,
    de_lemma_candidates,
)


@pytest.fixture(scope="module")
def lexicon():
    """Einmal pro Modul laden."""
    return load_full_lexicon()


@pytest.fixture(scope="module")
def goa2de_map(lexicon):
    return build_mapping(lexicon.entries, "goa2de")


@pytest.fixture(scope="module")
def de2goa_map(lexicon):
    return build_mapping(lexicon.entries, "de2goa")


def test_lexicon_loads(lexicon):
    """Lexicon enthält mindestens 1000 Einträge."""
    assert len(lexicon.entries) >= 1000, \
        f"Nur {len(lexicon.entries)} Einträge geladen — erwartet ≥ 1000"


def test_lexicon_has_de_map(lexicon):
    """DE-Map enthält mindestens 200 Direkt-Mappings."""
    assert len(lexicon.de_map) >= 200, \
        f"Nur {len(lexicon.de_map)} DE-Map-Einträge"


def test_jaffa_kree(goa2de_map):
    """Klassischer Jaffa-Befehl."""
    result = translate_text("Jaffa kree", goa2de_map, "goa2de")
    # 'kree' ist polysem; 'Krieger' für Jaffa, 'Achtung'/'aufgepasst' für kree
    assert any(w in result.lower() for w in ["krieger", "jaffa", "achtung"])


def test_tau_ri(goa2de_map):
    """Tau'ri = Erdling/Mensch von der Erde."""
    result = translate_text("Tau'ri", goa2de_map, "goa2de")
    assert any(w in result.lower() for w in ["erde", "mensch", "tau'ri"])


def test_de2goa_simple(de2goa_map):
    """Einfache DE→Goa-Übersetzung."""
    # 'krieger' ist eine grundlegende Vokabel
    result = translate_text("krieger", de2goa_map, "de2goa")
    # Erwartet 'jaffa' irgendwo im Output
    assert "jaffa" in result.lower(), f"Erwartete 'jaffa', bekam: {result!r}"


def test_de_lemma_basics():
    """DE-Lemma findet Infinitiv aus konjugierter Form."""
    candidates = de_lemma_candidates("gehe")
    assert "gehen" in candidates


def test_de_lemma_plural():
    """DE-Lemma findet Singular aus Plural."""
    candidates = de_lemma_candidates("Krieger")
    # Der Singular ist gleich, aber bei Plural-Endungen sollte gestimmt werden
    assert "krieger" in [c.lower() for c in candidates]


def test_search_engine_finds_jaffa(lexicon):
    """SearchEngine findet einen kanonischen Eintrag."""
    engine = SearchEngine(lexicon.entries)
    results = engine.search("jaffa", direction="goa2de", limit=5)
    assert len(results) >= 1
    # Der Top-Treffer enthält 'jaffa' im Term oder einer Bedeutung
    top = results[0]
    found = "jaffa" in str(top).lower()
    assert found, f"Top-Result enthält kein 'jaffa': {top}"


def test_sentence_analyzer_runs(lexicon):
    """SentenceAnalyzer wirft keinen Fehler auf einer Standard-Phrase."""
    analyzer = SentenceAnalyzer(lexicon.entries)
    result = analyzer.analyze("Jaffa kree", direction="goa2de")
    # Genaue Struktur hängt vom Original ab — hier nur: kein Crash, Liste/Dict zurück
    assert result is not None


def test_phrase_priority(de2goa_map):
    """Multi-Wort-Phrasen werden NICHT in Einzelwörter zerhackt."""
    # Wenn 'auf der Hut sein' eine eigene Phrase ist, soll sie als Einheit übersetzt werden
    # — Test angepasst nach tatsächlichem Lexicon-Inhalt
    pass  # Wird in Phase 4 ergänzt, sobald konkrete Beispielphrasen feststehen
```

### 2.4 — Tests ausführen

```powershell
pytest tests/ -v
```

**Erwartete Ausgabe:** Alle Tests `PASSED` oder mindestens 8 von 10 grün. Falls Tests fehlschlagen, weil eine Vokabel nicht so übersetzt wird wie erwartet: ist OK — Test anpassen, NICHT die Engine. Die Engine-Verhaltens-Wahrheit ist die Original-CTK-Version.

> **Falls die Tests sehr unterschiedlich zur Erwartung ausfallen:** Das deutet auf einen Fehler beim Engine-Extrakt hin (Phase 1). Zurück zu Phase 1, Diff zwischen Engine-Modulen und Original-Funktionen prüfen.

### Validierung Phase 2

```powershell
pytest tests/ -v --tb=short
```

Mindestens 80% der Tests grün (8 von 10). Falls weniger: Engine-Extrakt überprüfen.

---

## Phase 3 — Flet-Projekt-Skeleton

**Ziel:** Die Projektstruktur für `flet build` aufsetzen, inklusive `pyproject.toml`, `app/main.py` mit Hello-World-Tabs, und Asset-Bundling.

### 3.1 — `pyproject.toml` anlegen

Im Projekt-Root `C:/LAB/Goa'uld Translator Mobile/pyproject.toml`:

```toml
[project]
name = "goauld-translator-mobile"
version = "0.3.0"
description = "Goa'uld Linguistic Interface — Mobile Edition"
readme = "README_MOBILE.md"
requires-python = ">=3.10"
authors = [
    {name = "Basti"}
]
dependencies = [
    "flet==0.80.5",
    "pyyaml>=6.0"
]

[tool.flet]
# Module-Eintrittspunkt: app/main.py → main()
app = { module = "app.main", path = "." }
# org-Identifier — auf Android wird das die Package-ID
org = "de.basti.goauld"
# Sichtbarer App-Name auf Home-Screen
product = "Goa'uld Translator"
company = "SGC Xenolinguistics"
copyright = "Copyright (c) 2026"

[tool.flet.android]
# Min-SDK = Android 8.0 (Oreo) — ausreichend für Flutter
adaptive_icon_background = "#0a1628"
package_name = "de.basti.goauld"

[tool.flet.assets]
# Verzeichnis das in den APK-Bundle als Assets eingepackt wird
src = "assets"
```

> **Achtung:** `package_name` muss aus mindestens zwei Punkt-getrennten Segmenten bestehen. `de.basti.goauld` ist gültig. `goauld` allein wäre ungültig und `flet build` würde abbrechen.

### 3.2 — Verzeichnis `app/` mit Skeleton anlegen

`app/__init__.py` (leer):
```python
```

`app/main.py`:
```python
# -*- coding: utf-8 -*-
"""Goa'uld Translator Mobile — Flet entry point."""

import logging
from pathlib import Path

import flet as ft

# Engine importieren (lebt im Schwester-Verzeichnis goauld_engine/)
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from goauld_engine import (
    load_full_lexicon,
    SearchEngine,
    SentenceAnalyzer,
    build_mapping,
    translate_text,
)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger("goauld.mobile")


# ─────────────────────────────────────────────────────────────
# Globale App-State (einfach, keine State-Lib)
# ─────────────────────────────────────────────────────────────
class AppState:
    def __init__(self):
        self.lexicon = None
        self.search_engine = None
        self.analyzer = None
        self.goa2de_map = {}
        self.de2goa_map = {}
        self.direction = "goa2de"  # oder "de2goa"

    def load(self):
        self.lexicon = load_full_lexicon()
        self.search_engine = SearchEngine(self.lexicon.entries)
        self.analyzer = SentenceAnalyzer(self.lexicon.entries)
        self.goa2de_map = build_mapping(self.lexicon.entries, "goa2de")
        self.de2goa_map = build_mapping(self.lexicon.entries, "de2goa")
        log.info("Lexicon geladen: %d Einträge (%s)",
                 len(self.lexicon.entries), self.lexicon.source)


STATE = AppState()


# ─────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────
def main(page: ft.Page):
    page.title = "Goa'uld Translator"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0a1628"  # Gate-Blau, wird in Phase 5 in Theme verschoben
    page.padding = 0

    # Lexicon laden (kann ~1–2 s dauern auf Mobile)
    loading = ft.Text("Lade Lexicon …", size=16, color="#d4af37")
    page.add(loading)
    page.update()

    STATE.load()
    page.controls.clear()

    # Header
    header = ft.Container(
        content=ft.Text(
            "GOA'ULD LINGUISTIC INTERFACE",
            size=14,
            weight=ft.FontWeight.BOLD,
            color="#d4af37",
            font_family="Courier",
        ),
        padding=12,
        bgcolor="#0a1628",
    )

    # Tabs (werden in Phase 4 ausgebaut)
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=200,
        tabs=[
            ft.Tab(text="Briefing", content=_build_briefing_tab()),
            ft.Tab(text="Debrief", content=_build_debrief_tab()),
            ft.Tab(text="Live", content=_build_live_tab()),
        ],
        expand=True,
    )

    page.add(header, tabs)


def _build_briefing_tab() -> ft.Control:
    return ft.Container(
        content=ft.Text(f"Briefing — {len(STATE.lexicon.entries)} Einträge geladen",
                       color="#e0e0e0"),
        padding=20,
    )


def _build_debrief_tab() -> ft.Control:
    return ft.Container(
        content=ft.Text("Debrief — coming in Phase 4", color="#e0e0e0"),
        padding=20,
    )


def _build_live_tab() -> ft.Control:
    return ft.Container(
        content=ft.Text("Live — coming in Phase 4", color="#e0e0e0"),
        padding=20,
    )


if __name__ == "__main__":
    ft.app(target=main)
```

### 3.3 — Assets vorbereiten

**Wichtig:** Die Lexicon-Dateien müssen ins APK gebündelt werden. Sie kommen in `assets/`:

```powershell
# Im Projekt-Root
copy "Goa'uld-Dictionary.md" "assets\Goa'uld-Dictionary.md"
copy "Goa'uld-Wörterbuch.md" "assets\Goa'uld-Wörterbuch.md"
copy "Goa'uld-Fictionary.md" "assets\Goa'uld-Fictionary.md"
copy "Goa'uld-Neologikum.md" "assets\Goa'uld-Neologikum.md"
copy "goauld_lexicon.yaml" "assets\goauld_lexicon.yaml"
copy "yaml_loader.py" "assets\yaml_loader.py"
```

### 3.4 — `resources.get_app_dir()` für Mobile anpassen

In `goauld_engine/resources.py` die Funktion `get_app_dir` ergänzen, damit sie im Flet-Mobile-Build den `assets/`-Pfad findet:

```python
def get_app_dir() -> Path:
    """Liefert das Verzeichnis, in dem Asset-Dateien gesucht werden."""
    # 1. Flet-Mobile-Build: Assets liegen im app-Bundle unter /assets
    #    Flet stellt dafür den Pfad über page.assets_dir bereit, was wir aber
    #    auf Engine-Ebene nicht kennen. Workaround: ENV-Variable, die in
    #    app/main.py vor Engine-Aufrufen gesetzt wird.
    import os
    env_dir = os.environ.get("GOAULD_ASSETS_DIR")
    if env_dir:
        p = Path(env_dir)
        if p.exists():
            return p

    # 2. PyInstaller-Frozen (nicht relevant für Mobile, aber für Desktop-EXE)
    frozen = getattr(sys, "frozen", False)
    if frozen:
        return Path(sys.executable).parent

    # 3. Dev-Modus: Repo-Root
    repo_root = Path(__file__).resolve().parent.parent

    # 4. Wenn ein assets/-Unterordner existiert: bevorzugen
    assets = repo_root / "assets"
    if assets.exists() and (assets / "goauld_lexicon.yaml").exists():
        return assets

    return repo_root
```

In `app/main.py` ganz oben ergänzen, vor dem `import goauld_engine`:

```python
import os
from pathlib import Path
# Engine soll Assets aus dem assets/-Verzeichnis lesen
os.environ["GOAULD_ASSETS_DIR"] = str(
    Path(__file__).resolve().parent.parent / "assets"
)
```

### 3.5 — Skeleton testen (Desktop)

```powershell
flet run app/main.py
```

**Erwartetes Verhalten:** Ein dunkles Fenster mit gelbem Header "GOA'ULD LINGUISTIC INTERFACE", drei Tabs (Briefing, Debrief, Live). Der Briefing-Tab zeigt z. B. "Briefing — 5850 Einträge geladen".

### Validierung Phase 3

- `flet run app/main.py` öffnet ein Desktop-Fenster ohne Crash.
- Im Briefing-Tab steht eine Eintragszahl ≥ 3000.
- Tab-Wechsel funktioniert.

---

## Phase 4 — UI-Implementation

**Ziel:** Die drei Tabs funktional ausbauen — Such-Eingabe, Briefing-Ansicht, Debrief-Tokenisierung, Live-Translator. Direction-Toggle.

### 4.1 — Direction-Toggle in den Header

Header in `app/main.py` ersetzen durch:

```python
def _build_header(page: ft.Page) -> ft.Control:
    def toggle_direction(e):
        STATE.direction = "de2goa" if STATE.direction == "goa2de" else "goa2de"
        direction_label.value = _direction_label()
        page.update()

    direction_label = ft.Text(
        _direction_label(),
        size=12,
        color="#d4af37",
        font_family="Courier",
    )

    return ft.Container(
        content=ft.Row(
            [
                ft.Text(
                    "GOA'ULD LINGUISTIC INTERFACE",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color="#d4af37",
                    font_family="Courier",
                    expand=True,
                ),
                ft.IconButton(
                    icon=ft.Icons.SWAP_HORIZ,
                    icon_color="#d4af37",
                    on_click=toggle_direction,
                    tooltip="Richtung wechseln",
                ),
                direction_label,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=12,
        bgcolor="#0a1628",
    )


def _direction_label() -> str:
    return "GOA → DE" if STATE.direction == "goa2de" else "DE → GOA"
```

### 4.2 — Briefing-Tab: Such-Eingabe + Resultat-Liste + Detail-Karte

Beispiel-Implementierung:

```python
def _build_briefing_tab(page: ft.Page) -> ft.Control:
    search_input = ft.TextField(
        label="Suchbegriff",
        hint_text="Jaffa, kree …",
        autofocus=False,
        text_style=ft.TextStyle(font_family="Courier"),
        prefix_icon=ft.Icons.SEARCH,
    )

    results_list = ft.ListView(expand=True, spacing=4, padding=8)
    detail_view = ft.Container(
        content=ft.Text("Wähle einen Eintrag aus der Liste.",
                       color="#888888", italic=True),
        padding=16,
        expand=True,
    )

    def do_search(e=None):
        query = search_input.value.strip()
        results_list.controls.clear()
        if len(query) < 2:
            page.update()
            return
        hits = STATE.search_engine.search(
            query, direction=STATE.direction, limit=20,
        )
        for hit in hits:
            results_list.controls.append(_make_result_row(hit, detail_view, page))
        page.update()

    search_input.on_change = do_search

    return ft.Column(
        [
            ft.Container(content=search_input, padding=8),
            ft.Row(
                [
                    ft.Container(content=results_list, expand=2),
                    ft.VerticalDivider(width=1, color="#1a3a5c"),
                    ft.Container(content=detail_view, expand=3),
                ],
                expand=True,
            ),
        ],
        expand=True,
    )


def _make_result_row(hit: dict, detail_view: ft.Container, page: ft.Page) -> ft.Control:
    """Eine Zeile in der Suchergebnis-Liste."""
    # 'hit' ist ein dict aus SearchEngine.search() — exaktes Schema steht im Original.
    # Annahme: hit hat 'goa', 'meaning_de' (oder 'meaning_en') und 'score'.
    term = hit.get("goa") or hit.get("term") or "?"
    meaning = hit.get("meaning_de") or hit.get("meaning_en") or hit.get("meaning") or ""
    score = hit.get("score", 0)

    def open_detail(e):
        detail_view.content = _build_detail_card(hit)
        page.update()

    return ft.Container(
        content=ft.Row(
            [
                ft.Text(term, size=14, weight=ft.FontWeight.BOLD, color="#d4af37",
                       font_family="Courier", width=120),
                ft.Text(meaning, size=12, color="#e0e0e0", expand=True),
                ft.Text(f"{score}", size=10, color="#888888"),
            ],
        ),
        padding=8,
        bgcolor="#0f1f33",
        border_radius=4,
        on_click=open_detail,
        ink=True,
    )


def _build_detail_card(hit: dict) -> ft.Control:
    """Detail-Ansicht für einen einzelnen Eintrag."""
    rows = [
        ft.Text(hit.get("goa") or hit.get("term") or "?",
               size=22, weight=ft.FontWeight.BOLD, color="#d4af37",
               font_family="Courier"),
    ]
    if "meaning_de" in hit:
        rows.append(ft.Text(f"DE: {hit['meaning_de']}", size=14, color="#e0e0e0"))
    if "meaning_en" in hit:
        rows.append(ft.Text(f"EN: {hit['meaning_en']}", size=14, color="#a0c0e0"))
    if "etymology" in hit:
        rows.append(ft.Text(f"Etymologie: {hit['etymology']}",
                          size=12, color="#888888", italic=True))
    if "source" in hit:
        rows.append(ft.Text(f"Quelle: {hit['source']}",
                          size=10, color="#666666"))
    return ft.Column(rows, spacing=8)
```

> **Schema-Hinweis:** Das tatsächliche Schema von `hit` (also: welche Keys das `dict` hat) hängt davon ab, was `SearchEngine.search()` im Original zurückgibt. Qwen muss das Original studieren (Zeilen 428–612) und die Key-Namen in `_make_result_row` und `_build_detail_card` daran anpassen. Wenn das Original `entry.get('goauld_term')` verwendet, muss hier `hit.get('goauld_term')` stehen.

### 4.3 — Debrief-Tab: Token-Analyse

```python
def _build_debrief_tab(page: ft.Page) -> ft.Control:
    sentence_input = ft.TextField(
        label="Satz",
        hint_text="Jaffa, kree! Tau'ri shak!",
        multiline=True,
        min_lines=2,
        max_lines=4,
        text_style=ft.TextStyle(font_family="Courier"),
    )

    token_list = ft.ListView(expand=True, spacing=4, padding=8)

    def analyze(e):
        text = sentence_input.value.strip()
        token_list.controls.clear()
        if not text:
            page.update()
            return
        result = STATE.analyzer.analyze(text, direction=STATE.direction)
        # 'result' ist eine Liste von Token-Dicts oder ähnliches.
        # Schema aus Original SentenceAnalyzer.analyze() ablesen.
        for token in result:
            token_list.controls.append(_make_token_row(token))
        page.update()

    analyze_button = ft.ElevatedButton(
        text="Analysieren",
        icon=ft.Icons.PSYCHOLOGY,
        on_click=analyze,
        bgcolor="#1a3a5c",
        color="#d4af37",
    )

    return ft.Column(
        [
            ft.Container(content=sentence_input, padding=8),
            ft.Container(content=analyze_button, padding=ft.Padding(left=8, right=8, top=0, bottom=8)),
            token_list,
        ],
        expand=True,
    )


def _make_token_row(token: dict) -> ft.Control:
    """Eine Zeile pro Token in der Satz-Analyse."""
    raw = token.get("raw") or token.get("token") or "?"
    primary = token.get("primary") or token.get("translation") or "—"
    alternatives = token.get("alternatives") or []
    tip = token.get("tip") or ""

    children = [
        ft.Row([
            ft.Text(raw, size=14, weight=ft.FontWeight.BOLD,
                   color="#d4af37", font_family="Courier", width=140),
            ft.Text(f"→ {primary}", size=14, color="#e0e0e0", expand=True),
        ]),
    ]
    if alternatives:
        children.append(
            ft.Text(f"auch: {', '.join(alternatives)}",
                   size=11, color="#888888", italic=True)
        )
    if tip:
        children.append(
            ft.Text(tip, size=10, color="#a0c0e0", italic=True)
        )

    return ft.Container(
        content=ft.Column(children, spacing=2),
        padding=8,
        bgcolor="#0f1f33",
        border_radius=4,
    )
```

### 4.4 — Live-Tab: Echtzeit-Übersetzung mit Debounce

```python
def _build_live_tab(page: ft.Page) -> ft.Control:
    input_field = ft.TextField(
        label="Eingabe",
        multiline=True,
        min_lines=3,
        max_lines=6,
        text_style=ft.TextStyle(font_family="Courier"),
    )

    output_field = ft.Container(
        content=ft.Text("…", color="#888888"),
        padding=12,
        bgcolor="#0a1828",
        border_radius=4,
        expand=True,
    )

    # Debounce über asyncio.sleep
    import asyncio
    debounce_task = {"task": None}

    async def do_translate_debounced():
        await asyncio.sleep(0.3)  # 300 ms warten
        text = input_field.value.strip()
        if not text:
            output_field.content = ft.Text("…", color="#888888")
        else:
            mapping = (STATE.goa2de_map if STATE.direction == "goa2de"
                      else STATE.de2goa_map)
            translated = translate_text(text, mapping, direction=STATE.direction)
            output_field.content = ft.Text(
                translated, color="#e0e0e0", font_family="Courier", size=14,
            )
        page.update()

    def on_change(e):
        if debounce_task["task"] is not None and not debounce_task["task"].done():
            debounce_task["task"].cancel()
        debounce_task["task"] = page.run_task(do_translate_debounced)

    input_field.on_change = on_change

    return ft.Column(
        [
            ft.Container(content=input_field, padding=8),
            ft.Container(content=output_field, padding=8, expand=True),
        ],
        expand=True,
    )
```

### 4.5 — `main(page)` zusammenfügen

```python
def main(page: ft.Page):
    page.title = "Goa'uld Translator"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0a1628"
    page.padding = 0
    page.fonts = {"Courier": "Courier New"}

    loading = ft.Text("Lade Lexicon …", size=16, color="#d4af37")
    page.add(loading)
    page.update()

    STATE.load()
    page.controls.clear()

    header = _build_header(page)
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=200,
        tabs=[
            ft.Tab(text="Briefing", content=_build_briefing_tab(page)),
            ft.Tab(text="Debrief",  content=_build_debrief_tab(page)),
            ft.Tab(text="Live",     content=_build_live_tab(page)),
        ],
        expand=True,
    )
    page.add(header, tabs)
```

### 4.6 — Manueller Test (Desktop)

```powershell
flet run app/main.py
```

Prüfen:
- [ ] Lexicon lädt, Eintragszahl im Header sichtbar oder zumindest in der Konsole geloggt
- [ ] Briefing-Tab: Eingabe "jaffa" zeigt Treffer-Liste, Klick auf Treffer zeigt Detail
- [ ] Debrief-Tab: Eingabe "Jaffa kree" + Button-Klick zeigt Token-Aufschlüsselung
- [ ] Live-Tab: Eingabe wird nach kurzer Pause automatisch übersetzt
- [ ] Direction-Toggle (Pfeil-Icon im Header): "GOA → DE" wechselt zu "DE → GOA"

### Validierung Phase 4

Alle obigen Funktionen funktionieren auf dem Desktop mit `flet run`. Wenn ein Tab crasht, im Stack-Trace nachvollziehen ob das Problem im Engine-Aufruf liegt (dann Schema-Abgleich mit Original) oder im Flet-UI (dann Code-Korrektur).

---

## Phase 5 — Theming (SGC-Look)

**Ziel:** Die SGC-Terminal-Ästhetik des Originals (Gate-Blau, Gold, Orange, Courier-Mono, Scanlines) auf Flet/Material übertragen.

### 5.1 — Farbpalette zentralisieren

Datei `app/theme.py`:

```python
# -*- coding: utf-8 -*-
"""SGC-Terminal-Farbpalette für die Mobile-App."""

# Aus dem CTK-Original übernommen (Z. 122–245)
COLORS = {
    "bg_root":   "#0a1628",   # Tiefes Gate-Blau, App-Hintergrund
    "bg_panel":  "#0f1f33",   # Panel-Flächen
    "bg_card":   "#142a44",   # Card-Container
    "gold":      "#d4af37",   # SGC-Gold, Akzent + Headlines
    "gold_dim":  "#8a7228",   # Trennlinien
    "blue":      "#3a7bc8",   # Stargate-Wormhole-Blau
    "orange":    "#e8743c",   # Warning / Active-Indicator
    "mil_amber": "#f5a623",   # DEFCON-Status
    "text_hi":   "#e8e8e0",   # Primärtext
    "text_mid":  "#a0a098",   # Sekundärtext
    "text_lo":   "#606058",   # Tertiärtext / Disabled
}
```

Dann in `app/main.py`:
```python
from app.theme import COLORS as C
# ... und überall '#0a1628' etc. durch C['bg_root'] ersetzen
```

### 5.2 — Flet-Theme setzen

In `main(page)`:

```python
page.theme = ft.Theme(
    color_scheme_seed=C["gold"],
    color_scheme=ft.ColorScheme(
        primary=C["gold"],
        on_primary=C["bg_root"],
        secondary=C["blue"],
        surface=C["bg_panel"],
        on_surface=C["text_hi"],
        background=C["bg_root"],
        on_background=C["text_hi"],
    ),
    use_material3=True,
)
```

### 5.3 — Mono-Font einbinden

Mono-Schrift für den Terminal-Look. Empfehlung: **JetBrains Mono** (frei, gut lesbar) oder **Fira Code**.

Font-Datei (z. B. `JetBrainsMono-Regular.ttf`) nach `assets/fonts/JetBrainsMono-Regular.ttf` legen. In `pyproject.toml`:

```toml
[tool.flet.assets]
src = "assets"
```

(reicht — `assets/` wird rekursiv mitgepackt).

In `main(page)`:
```python
page.fonts = {
    "TerminalMono": "/fonts/JetBrainsMono-Regular.ttf",
}
```

Dann in allen `font_family="Courier"`-Stellen → `font_family="TerminalMono"` ändern.

### 5.4 — App-Icon

Adaptive Icon für Android: 1024×1024 PNG mit dem SGC-Logo (z. B. Stargate-Glyph mit Gold-Rahmen auf Gate-Blau).

Speicherort: `assets/icon.png` (1024×1024). Flet generiert daraus automatisch die nötigen Größen.

In `pyproject.toml`:
```toml
[tool.flet.android]
adaptive_icon_background = "#0a1628"
icon = "assets/icon.png"
```

> **Falls kein Icon zur Hand:** Platzhalter aus einem schwarzen Quadrat mit goldenem "G" reicht erstmal. Vor Final-Build durch das echte Logo ersetzen.

### 5.5 — Optional: Scanline-Overlay als Stack

Echte CRT-Scanlines auf Mobile sind hier nicht prioritär (Performance, nicht alle Material-Themes mögen Overlays). Wenn gewünscht: Ein semitransparentes `ft.Image` mit gestreiftem PNG via `ft.Stack` über die ganze Page legen. Erst nach erfolgreichem APK-Build implementieren.

### Validierung Phase 5

```powershell
flet run app/main.py
```

- Hintergrund ist Gate-Blau (`#0a1628`)
- Headlines/Akzente sind in SGC-Gold
- Mono-Font in Termen und Eingabefeldern
- Material-Komponenten (Tabs, Buttons) verwenden Gold als Primary

---

## Phase 6 — Lokal testen + APK bauen

**Ziel:** Erster funktionierender Debug-APK auf einem Android-Gerät.

### 6.1 — Letzter Desktop-Smoketest

```powershell
flet run app/main.py
```

Alle drei Tabs durchprobieren. **Wenn etwas crasht: NICHT bauen.** Erst Desktop-Run muss komplett sauber laufen.

### 6.2 — Build-Cache vorbereiten

Beim ersten `flet build apk` lädt Flet:
- Flutter SDK (~700 MB) nach `~/.flutter` oder ähnlich
- JDK 17 nach `~/java/`
- Android SDK (cmdline-tools, platform-tools, build-tools, platforms;android-35) nach `%LOCALAPPDATA%\Android\Sdk`

Das dauert beim ersten Mal **20–40 Minuten**, je nach Internetverbindung. Genug Disk-Space (≥ 10 GB) sicherstellen.

### 6.3 — Debug-APK bauen

```powershell
flet build apk --verbose
```

**Erwartete Ausgabe:** Sehr viel Konsolen-Output. Am Ende:
```
Successfully built ./build/apk/app-release.apk
```

oder:
```
Successfully built ./build/apk/<projektname>-release.apk
```

(Dateiname kann variieren, wichtig ist `Successfully built`.)

> **Bekanntes Problem:** "Flet app package app/app.zip was not created." → das ist ein Warning, kein Fehler, wenn der Build trotzdem abschließt.

### 6.4 — APK auf Gerät übertragen

**Option A — Per USB-Kabel mit ADB:**
```powershell
adb devices
# Erwartung: Eines oder mehr Geräte gelistet
adb install build/apk/<dateiname>.apk
```

**Option B — Direkt auf Telefon:** APK per Cloud-Speicher (Google Drive, Mega, etc.) auf das Telefon laden, dort Datei öffnen, "Aus unbekannten Quellen installieren" erlauben.

### 6.5 — Smoketest auf dem Gerät

1. App vom Home-Screen öffnen.
2. Splash → "Lade Lexicon …" → Tabs erscheinen.
3. Briefing-Tab: "jaffa" eingeben, Treffer prüfen.
4. Debrief-Tab: "Jaffa kree" eingeben, Analyze tippen.
5. Live-Tab: schnell tippen, Übersetzung erscheint nach ~300 ms.

> **Wenn die App beim Start crasht:** Logcat zur Diagnose. Befehl:
> ```powershell
> adb logcat | findstr -i "goauld python flutter"
> ```
> Vermutlichste Ursachen:
> - Asset-Pfad falsch → in `resources.get_app_dir()` und `pyproject.toml` prüfen.
> - YAML-Datei nicht im Bundle → `assets/goauld_lexicon.yaml` Existenz prüfen.
> - `yaml_loader.py` nicht im Bundle → `assets/yaml_loader.py` Existenz prüfen.

### 6.6 — Release-Build (signiert)

Erst wenn Debug-Build sauber läuft. Für Release-Signing:

```powershell
keytool -genkey -v -keystore $env:USERPROFILE\goauld-keystore.jks `
  -storetype JKS -keyalg RSA -keysize 2048 -validity 10000 `
  -alias goauld
```

(Keystore-Passwort und Alias-Passwort merken.)

In `pyproject.toml`:
```toml
[tool.flet.android]
# ... vorhandene Felder ...
signing.key_alias = "goauld"
signing.store_file = "C:/Users/USERNAME/goauld-keystore.jks"
signing.store_password = "DEIN_PASSWORT"
signing.key_password = "DEIN_PASSWORT"
```

(Passwörter NIEMALS committen — `.gitignore` ergänzen.)

```powershell
flet build apk --release
```

Output: `build/apk/<name>-release.apk` (signiert).

### Validierung Phase 6

- Debug-APK installiert und startet auf einem Android-Gerät (≥ Android 8).
- Lexicon lädt sichtbar (Eintragszahl im Header oder Log).
- Mindestens eine erfolgreiche Übersetzung in jedem der drei Tabs.

---

## Anhang A — File-Manifest (Soll-Zustand nach Phase 6)

```
C:/LAB/Goa'uld Translator Mobile/
│
├── .venv/                           # virtuelles Environment (gitignore)
├── .gitignore                       # NEU: build/, .venv/, *.apk, *.jks, *.aab
│
├── pyproject.toml                   # NEU (Phase 3)
├── README_MOBILE.md                 # NEU (Phase 3, optional ausführlich)
├── MIGRATION_NOTES.md               # NEU: Probleme & Entscheidungen-Log
│
├── goauld_engine/                   # NEU (Phase 1)
│   ├── __init__.py
│   ├── parser.py
│   ├── resources.py
│   ├── lexicon.py
│   ├── search.py
│   ├── lemma.py
│   ├── translator.py
│   └── analyzer.py
│
├── app/                             # NEU (Phase 3)
│   ├── __init__.py
│   ├── main.py
│   └── theme.py                     # NEU (Phase 5)
│
├── assets/                          # NEU (Phase 3)
│   ├── Goa'uld-Dictionary.md        # Kopie
│   ├── Goa'uld-Wörterbuch.md        # Kopie
│   ├── Goa'uld-Fictionary.md        # Kopie
│   ├── Goa'uld-Neologikum.md        # Kopie
│   ├── goauld_lexicon.yaml          # Kopie
│   ├── yaml_loader.py               # Kopie
│   ├── icon.png                     # NEU (Phase 5)
│   └── fonts/
│       └── JetBrainsMono-Regular.ttf  # NEU (Phase 5)
│
├── tests/                           # NEU (Phase 2)
│   ├── __init__.py
│   └── test_engine.py
│
├── build/                           # generiert von flet build (gitignore)
│   └── apk/
│       └── *.apk
│
└── *** Originaldateien (UNVERÄNDERT) ***
    ├── goauld_translator.py         # CTK 0.2.6 — read-only
    ├── goauld_lexicon.yaml          # read-only
    ├── yaml_loader.py               # read-only
    ├── Goa'uld-Dictionary.md        # read-only
    ├── Goa'uld-Wörterbuch.md        # read-only
    ├── Goa'uld-Fictionary.md        # read-only
    ├── Goa'uld-Neologikum.md        # read-only
    ├── LANGUAGE_GUIDE_DE.md         # read-only
    ├── LANGUAGE_GUIDE_EN.md         # read-only
    ├── README.md                    # read-only
    ├── README_DE.md                 # read-only
    └── tree.md                      # read-only
```

---

## Anhang B — Häufige Fehler und ihre Lösungen

### B.1 — `ModuleNotFoundError: No module named 'goauld_engine'` beim `flet run`

**Ursache:** `app/main.py` findet die Engine nicht, weil das Arbeitsverzeichnis falsch ist.

**Lösung:** In `app/main.py` ist der `sys.path.insert(0, str(Path(__file__).resolve().parent.parent))` essentiell. Sicherstellen dass er VOR dem `from goauld_engine import ...` steht.

### B.2 — `FileNotFoundError: goauld_lexicon.yaml` zur Laufzeit auf Android

**Ursache:** Asset wurde nicht ins Bundle gepackt, oder `get_app_dir()` zeigt auf den falschen Pfad.

**Lösung:**
1. `pyproject.toml` enthält `[tool.flet.assets] src = "assets"`.
2. `assets/goauld_lexicon.yaml` existiert (mit `dir assets/` prüfen).
3. In `app/main.py` wird `os.environ["GOAULD_ASSETS_DIR"]` gesetzt — auf Mobile zeigt das auf einen Flet-spezifischen Pfad. Dafür auf Mobile lieber `page.assets_dir` aus dem `main(page)`-Callback verwenden und in `STATE.load()` reichen.

**Korrektur in `app/main.py`:**
```python
def main(page: ft.Page):
    import os
    # Flet stellt assets_dir auf Mobile bereit
    if hasattr(page, "assets_dir") and page.assets_dir:
        os.environ["GOAULD_ASSETS_DIR"] = page.assets_dir
    # Rest wie gehabt
    STATE.load()
```

### B.3 — `flet build apk` hängt bei "Packaging Python app …"

**Bekanntes Problem (siehe github.com/flet-dev/flet/issues/6010).** Workarounds:
- Antivirus temporär deaktivieren — Defender greift in serious_python ein.
- Build mit `-vv` Flag laufen lassen, um zu sehen wo es hängt.
- Mit kleinerer App (nur Hello-World) gegentest, um zu sehen ob es projekt- oder umgebungsspezifisch ist.

### B.4 — Engine-Tests schlagen fehl mit `KeyError: 'meaning_de'`

**Ursache:** Das Schema, das `SearchEngine.search()` zurückgibt, weicht von den Annahmen in den Tests ab.

**Lösung:** In Phase 1, beim Kopieren von `class SearchEngine` aus dem Original, NICHTS am Return-Schema ändern. Dann die Tests in Phase 2 + die UI-Code-Stellen in Phase 4 an das tatsächliche Schema anpassen. Ankerpunkt: was im Original an `self._search_callback` oder vergleichbar gereicht wird, ist das Schema.

### B.5 — Auf Android: alles weiß / kein Theme

**Ursache:** `page.theme_mode` nicht gesetzt oder `page.bgcolor` zu früh.

**Lösung:** `page.theme_mode = ft.ThemeMode.DARK` MUSS als erste Anweisung in `main(page)` stehen, vor `page.update()`.

### B.6 — Lexicon lädt, aber Übersetzung gibt nichts zurück

**Ursache:** `STATE.direction` ist nicht synchron mit der `mapping`-Variable.

**Lösung:** In `_build_live_tab` und überall wo übersetzt wird:
```python
mapping = STATE.goa2de_map if STATE.direction == "goa2de" else STATE.de2goa_map
```
Diese Zeile MUSS vor jedem `translate_text`-Aufruf neu evaluiert werden, NICHT zwischengespeichert.

---

## Anhang C — Befehls-Schnellreferenz

```powershell
# Setup
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install "flet[all]==0.80.5" pyyaml pytest

# Engine-Tests
pytest tests/ -v

# Desktop-Run (Entwicklung)
flet run app/main.py

# Hot-Reload während Entwicklung
flet run --hot app/main.py

# APK-Build (Debug)
flet build apk --verbose

# APK-Build (Release, signiert)
flet build apk --release

# AAB-Build (für Play Store)
flet build aab --release

# Auf Gerät installieren
adb install build/apk/<dateiname>.apk

# Logs vom Gerät lesen
adb logcat | findstr -i "goauld python flutter"
```

---

## Anhang D — Was NICHT zu tun ist (Negativ-Liste)

1. ❌ `goauld_translator.py` (das CTK-Original) editieren oder löschen.
2. ❌ `customtkinter` oder `tkinter` in den `goauld_engine`-Modulen importieren.
3. ❌ Eigene Vermutungen über Funktions-Signaturen oder Return-Schemata anstellen — immer das Original lesen.
4. ❌ Verschiedene Funktionen in EINEM Schritt verschieben — strikt eine nach der anderen, mit Test dazwischen.
5. ❌ Flet-Version auf eine prerelease (`0.80.6.devXXX`) updaten ohne expliziten Anlass.
6. ❌ Pfade als String mit `\\` oder `\` zusammensetzen — immer `pathlib.Path`.
7. ❌ Lexicon im UI-Thread synchron neu laden — nur einmal in `STATE.load()`.
8. ❌ Eingabefeld-Live-Updates ohne Debounce (führt zu hunderten von Engine-Aufrufen).
9. ❌ Asset-Dateien an einer anderen Stelle als `assets/` ablegen — Flet packt nur dieses Verzeichnis.
10. ❌ APK-Release-Keystore in den Source-Tree committen.

---

## Anhang E — `MIGRATION_NOTES.md` Vorlage

Bei Beginn der Migration anlegen:

```markdown
# Migration Notes — Goa'uld Translator Mobile

## Phase 0
- [Datum] Toolchain validiert. Python X.Y.Z, Flet 0.80.5, Flutter Z.Z.Z.

## Phase 1 — Engine-Extrakt
- [Datum] Funktion X aus Z. ABCD nach `Y.py` verschoben — wörtlich kopiert, nur Logging-Aufruf adaptiert.
- [Datum] PROBLEM: Funktion FOO existiert im Original nicht — vermutlich umbenannt zu BAR. Aktion: …

## Phase 2 — Tests
- [Datum] X von Y Tests grün. Fehlschläge:
  - test_jaffa_kree: Erwartet "krieger", bekam "<actual>" — Test angepasst weil Original genau das liefert.

## Phase 3 — Skeleton
- …

## Offene Entscheidungen
- [ ] Mono-Font: JetBrains Mono vs. Fira Code → vorerst JetBrains Mono.
- [ ] Icon: Platzhalter „G" oder echtes Stargate-Glyph?

## Blocker
- (keine)
```

---

## Abschluss-Checkliste

Bevor das Projekt als „fertig für Phase 7 (gemeinsam mit Claude)" markiert wird, müssen folgende Punkte erfüllt sein:

- [ ] `goauld_engine/` enthält die 8 Module aus dem File-Manifest, alle importierbar.
- [ ] `pytest tests/` zeigt mindestens 80 % grün.
- [ ] `flet run app/main.py` öffnet ohne Crash und alle drei Tabs funktionieren.
- [ ] `flet build apk` erzeugt eine `*.apk` im `build/apk/`-Verzeichnis.
- [ ] APK installiert und startet auf einem realen Android-Gerät.
- [ ] Mindestens eine erfolgreiche Übersetzung pro Tab auf dem Gerät durchgeführt.
- [ ] `MIGRATION_NOTES.md` ist gepflegt mit allen Abweichungen, Blockern und Entscheidungen.
- [ ] `goauld_translator.py` (CTK-Original) und alle anderen Originaldateien sind unverändert.

Wenn alle Punkte abgehakt: das Mobile-Projekt ist bereit für die zweite Iteration mit Claude (Theming-Verfeinerung, Offline-Performance, optionale Zusatz-Features).

---

**Ende des Fahrplans.**
