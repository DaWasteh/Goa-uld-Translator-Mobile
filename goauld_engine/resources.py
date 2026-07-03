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

# MD-Kandidaten für EN- und DE-Dateien (Apostroph-frei für APK-Kompatibilität)
MD_CANDIDATES_EN = [
    "Goa_uld-Dictionary.md",
    "Goa_uld-Fictionary.md",
    "Goa_uld-Neologikum.md",
]
MD_CANDIDATES_DE = [
    "Goa_uld-Wörterbuch.md",
]


def get_app_dir() -> Path:
    """Liefert das Verzeichnis, in dem Asset-Dateien gesucht werden.

    Reihenfolge:
    1. Wenn ``GOAULD_ASSETS_DIR`` ENV gesetzt ist und existiert: dort suchen (Flet-Mobile).
    2. Wenn ``GOAULD_ASSETS_DIR`` gesetzt ist, aber das direkte Verzeichnis nicht existiert:
       nach Asset-Dateien im ENV-Pfad und seinen Unterverzeichnissen suchen.
    3. Wenn ``sys.frozen`` (PyInstaller-Desktop): neben der EXE.
    4. Dev-Modus: Repo-Root / assets/-Unterordner.
    5. Fallback: das Verzeichnis dieses Files (goauld_engine/).
    """
    # Alle relevanten Asset-Dateinamen (Apostroph-frei für APK-Kompatibilität)
    _ASSET_NAMES = (
        "goa_uld_lexicon.yaml",
        "goauld_lexicon.yaml",
        "goauld_overrides.yaml",
        "goauld_root_registry.yaml",
        "GOAULD_GRAMMAR.md",
        "Goa_uld-Dictionary.md",
        "Goa_uld-Wörterbuch.md",
        "Goa_uld-Fictionary.md",
        "Goa_uld-Neologikum.md",
        "goauld_expansion_v1.yaml",
        "goauld_expansion_v2.yaml",
        "goauld_expansion_v3.yaml",
        "goauld_expansion_v4.yaml",
        "goauld_expansion_v5.yaml"
    )

    # ── Flet-Mobile / Android: Flet sets FLET_ASSETS_DIR; GOAULD_ASSETS_DIR is a manual override.
    env_dir = os.environ.get("GOAULD_ASSETS_DIR") or os.environ.get("FLET_ASSETS_DIR")
    if env_dir:
        p = Path(env_dir)
        if p.exists() and p.is_dir():
            # Direkter Pfad existiert — prüfe, ob Assets vorhanden sind
            has_assets = any((p / n).exists() for n in _ASSET_NAMES)
            if has_assets:
                log.debug("get_app_dir: ENV asset dir exists with Assets: %s", p)
                return p
            # Verzeichnis existiert, aber keine Assets direkt — suche rekursiv
            log.debug("get_app_dir: ENV existiert, aber keine Assets direkt — suche rekursiv: %s", p)
            for root, dirs, files in os.walk(str(p)):
                for fname in _ASSET_NAMES:
                    if fname in files:
                        found = Path(root) / fname
                        log.debug("get_app_dir: Asset-Datei gefunden in Unterordner: %s", found.parent)
                        return found.parent
            log.warning("get_app_dir: ENV gesetzt (%s), aber keine Asset-Dateien gefunden", p)
            return p

        # ENV ist gesetzt, aber der Pfad existiert gar nicht.
        # Das kann passieren, wenn die ENV-Variable falsch gesetzt ist.
        log.warning("get_app_dir: ENV asset dir is set, but path does not exist: %s", p)
        # Fahre fort mit nächster Strategie (Dev-Modus)

    # ── PyInstaller-Frozen ────────────────────────────────────────────────────
    frozen = getattr(sys, "frozen", False)
    if frozen:
        exe_parent = Path(sys.executable).parent
        log.debug("get_app_dir: sys.frozen=True, exe_parent=%s", exe_parent)
        return exe_parent

    # ── Dev-Modus: Repo-Root / assets/-Unterordner ───────────────────────────
    repo_root = Path(__file__).resolve().parent.parent

    # Wenn ein assets/-Unterordner existiert: bevorzugen
    assets = repo_root / "assets"
    if assets.exists() and assets.is_dir():
        if any((assets / n).exists() for n in _ASSET_NAMES):
            log.debug("get_app_dir: Dev-Modus, assets/-Verzeichnis gefunden: %s", assets)
            return assets

    # Fallback: goauld_engine/-Verzeichnis (falls YAML dort liegt)
    engine_dir = Path(__file__).resolve().parent
    yaml_names = ("goa_uld_lexicon.yaml", "goauld_lexicon.yaml")
    if any((engine_dir / n).exists() for n in yaml_names):
        log.debug("get_app_dir: Fallback auf engine_dir: %s", engine_dir)
        return engine_dir

    # Letzter Fallback: repo_root (evtl. liegen Assets dort)
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