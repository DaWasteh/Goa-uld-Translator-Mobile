# -*- coding: utf-8 -*-
"""Auflösung von Asset-Pfaden für Lexicon-Dateien.

Anders als die Desktop-Version lebt Mobile in einem Flet-App-Bundle.
Die Funktion ``get_app_dir()`` löst den korrekten Lese-Pfad zu Assets auf,
sowohl im Entwicklungsmodus (Source-Tree) als auch im gepackten APK.
"""

import sys
import logging
import os
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

# MD-Kandidaten für EN- und DE-Dateien (Rückwärtskompatibilität zum Original)
MD_CANDIDATES_EN = [
    "Goa'uld-Dictionary.md",
    "Goa_uld-Dictionary.md",
    "Goa'uld-Fictionary.md",
    "Goa_uld-Fictionary.md",
    "Goa'uld-Neologikum.md",
    "Goa_uld-Neologikum.md",
]
MD_CANDIDATES_DE = [
    "Goa'uld-Wörterbuch.md",
    "Goa_uld-Wörterbuch.md",
]


def get_app_dir() -> Path:
    """Liefert das Verzeichnis, in dem Asset-Dateien gesucht werden.

    Reihenfolge:
    1. Wenn ``GOAULD_ASSETS_DIR`` ENV gesetzt ist und existiert: dort suchen (Flet-Mobile).
    2. Wenn ``GOAULD_ASSETS_DIR`` gesetzt ist, aber nicht existiert: versuche
       relative Pfade wie ``assets/`` oder ``../assets`` (Flet-Asset-Mount).
    3. Wenn ``sys.frozen`` (PyInstaller-Desktop): neben der EXE.
    4. Dev-Modus: Repo-Root / assets/-Unterordner.
    5. Fallback: das Verzeichnis dieses Files (goauld_engine/).
    """
    # Flet-Mobile-Build: Assets liegen im assets/-Verzeichnis
    env_dir = os.environ.get("GOAULD_ASSETS_DIR")
    if env_dir:
        p = Path(env_dir)
        if p.exists():
            log.debug("get_app_dir: ENV GOAULD_ASSETS_DIR existiert: %s", p)
            return p
        # ENV ist gesetzt, aber der direkte Pfad existiert nicht.
        # Versuche relative Pfade (Flet mountet Assets manchmal anders).
        for rel_candidate in ("assets", "../assets", "goa'uld_lexicon"):
            candidate = p / rel_candidate
            if candidate.exists() and candidate.is_dir():
                log.debug("get_app_dir: ENV-Relativpfad gefunden: %s", candidate)
                return candidate
        # Letzter Versuch: den ENV-Pfad selbst zurueckgeben (Dateien koennten
        # dort sein, aber wir haben sie noch nicht geprüft).
        log.warning("get_app_dir: ENV GOAULD_ASSETS_DIR gesetzt, aber nicht gefunden: %s", p)
        return p

    # PyInstaller-Frozen
    frozen = getattr(sys, "frozen", False)
    if frozen:
        exe_parent = Path(sys.executable).parent
        log.debug("get_app_dir: sys.frozen=True, exe_parent=%s", exe_parent)
        return exe_parent

    # Dev-Modus: Repo-Root
    repo_root = Path(__file__).resolve().parent.parent

    # Wenn ein assets/-Unterordner existiert: bevorzugen
    assets = repo_root / "assets"
    _yaml_names = ("goauld_lexicon.yaml", "goa_uld_lexicon.yaml", "goa'uld_lexicon.yaml")
    if assets.exists() and any((assets / n).exists() for n in _yaml_names):
        log.debug("get_app_dir: Dev-Modus, assets/-Verzeichnis gefunden: %s", assets)
        return assets

    # Fallback: goauld_engine/-Verzeichnis (falls YAML dort liegt)
    engine_dir = Path(__file__).resolve().parent
    if any((engine_dir / n).exists() for n in _yaml_names):
        log.debug("get_app_dir: Fallback auf engine_dir: %s", engine_dir)
        return engine_dir

    log.warning("get_app_dir: Kein Asset-Verzeichnis gefunden! Return repo_root=%s", repo_root)
    return repo_root


def _find_all(candidates: list[str], hint: Optional[str] = None) -> list[str]:
    """Sucht ALLE vorhandenen Dateien aus einer Kandidatenliste.
    Gibt eine nach Kandidaten-Reihenfolge sortierte Liste zurück; keine Duplikate.
    """
    app_dir = get_app_dir()
    meipass = getattr(sys, '_MEIPASS', None)
    found: list[str] = []
    seen: set[str] = set()

    # Optionaler Hint zuerst
    if hint and Path(hint).is_file():
        resolved = str(Path(hint).resolve())
        if resolved not in seen:
            seen.add(resolved)
            found.append(str(hint))

    for name in candidates:
        search_paths = [
            app_dir / name,
            Path.cwd() / name,
            Path.home() / name,
        ]
        if meipass:
            search_paths.append(Path(meipass) / name)
        for p in search_paths:
            if p.is_file():
                resolved = str(p.resolve())
                if resolved not in seen:
                    seen.add(resolved)
                    found.append(str(p))
                break  # nächster Kandidat — selber Name aus verschiedenen Dirs ist derselbe

    return found


def find_md_files(hint_en: Optional[str] = None,
                  hint_de: Optional[str] = None) -> tuple[list[str], list[str]]:
    """
    Sucht ALLE EN- und DE-Wörterbuchdateien.
    Gibt ([en_paths], [de_paths]) zurück — beide können leer sein.
    """
    en = _find_all(MD_CANDIDATES_EN, hint_en)
    de = _find_all(MD_CANDIDATES_DE, hint_de)
    return en, de


def get_app_dir_public() -> Path:
    """Public alias für get_app_dir."""
    return get_app_dir()