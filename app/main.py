# -*- coding: utf-8 -*-
"""DIAGNOSE-Variante von main.py - zeigt Boot-Schritte und Fehler im UI."""

import os
import sys
import traceback
from pathlib import Path

import flet as ft

# Engine-Pfad VOR dem Import auf sys.path setzen
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

# Default-Assets (wird in main() ggf. ueberschrieben)
os.environ.setdefault("GOAULD_ASSETS_DIR", str(_REPO_ROOT / "assets"))


def main(page: ft.Page):
    page.title = "Goauld Translator (DIAGNOSE)"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0a1628"
    page.padding = 12

    # Sichtbares Log-Panel
    log_view = ft.ListView(expand=True, spacing=2, auto_scroll=True)
    page.add(
        ft.Text(
            "GOAULD BOOT-DIAGNOSE",
            size=14,
            weight=ft.FontWeight.BOLD,
            color="#d4af37",
            font_family="Courier",
        ),
        ft.Divider(color="#1a3a5c"),
        log_view,
    )
    page.update()

    def log(msg, color="#d4af37"):
        log_view.controls.append(
            ft.Text(str(msg), color=color, size=11,
                    font_family="Courier", selectable=True),
        )
        try:
            page.update()
        except Exception:
            pass

    def log_traceback(exc):
        log("FAIL: " + type(exc).__name__ + ": " + str(exc), "#ff5555")
        for line in traceback.format_exc().splitlines():
            log(line, "#ff5555")

    log("BOOT: main() gestartet", "#d4af37")
    log("BOOT: __file__ = " + str(__file__), "#a0c0e0")
    log("BOOT: cwd       = " + str(Path.cwd()), "#a0c0e0")
    log("BOOT: sys.path[0:3] = " + str(sys.path[:3]), "#a0c0e0")

    # Schritt 1: assets_dir
    try:
        assets_dir = getattr(page, "assets_dir", None)
        if assets_dir:
            os.environ["GOAULD_ASSETS_DIR"] = str(assets_dir)
            log("OK  : page.assets_dir = " + str(assets_dir), "#85c97a")
        else:
            log("WARN: page.assets_dir ist None", "#f5a623")
        env_val = os.environ.get("GOAULD_ASSETS_DIR", "")
        log("OK  : GOAULD_ASSETS_DIR = " + env_val, "#85c97a")

        assets_path = Path(env_val) if env_val else Path()
        if assets_path.exists():
            files = sorted(p.name for p in assets_path.iterdir())
            log("OK  : assets enthaelt " + str(len(files)) + " Dateien",
                "#85c97a")
            for n in files[:10]:
                log("      - " + n, "#a0c0e0")
        else:
            log("FAIL: assets-Ordner existiert NICHT: " + str(assets_path),
                "#ff5555")
    except Exception as e:
        log_traceback(e)
        return

    # Schritt 2: Engine importieren
    try:
        log("BOOT: importiere goauld_engine ...", "#d4af37")
        from goauld_engine import (
            load_full_lexicon,
            SearchEngine,
            SentenceAnalyzer,
            build_mapping,
            translate_text,
        )
        log("OK  : goauld_engine importiert", "#85c97a")
    except Exception as e:
        log_traceback(e)
        return

    # Schritt 3: Lexicon laden
    try:
        log("BOOT: lade Lexicon ...", "#d4af37")
        lex = load_full_lexicon()
        log("OK  : Lexicon geladen (" + str(len(lex.entries))
            + " Eintraege, source=" + str(lex.source) + ")", "#85c97a")
        log("OK  : DE-Map=" + str(len(lex.de_map))
            + "  EN-Map=" + str(len(lex.en_map)), "#85c97a")
        for p in lex.found_paths or []:
            log("      via " + str(p), "#a0c0e0")
    except Exception as e:
        log_traceback(e)
        return

    # Schritt 4: SearchEngine + Analyzer + Maps
    try:
        log("BOOT: baue SearchEngine + Analyzer ...", "#d4af37")
        engine = SearchEngine(lex.entries)
        SentenceAnalyzer(lex.entries)
        goa2de = build_mapping(lex.entries, "goa2de")
        de2goa = build_mapping(lex.entries, "de2goa")
        log("OK  : Engine bereit (" + str(len(engine.entries))
            + " dedupliziert)", "#85c97a")
        log("OK  : goa2de-Map=" + str(len(goa2de))
            + "  de2goa-Map=" + str(len(de2goa)), "#85c97a")
    except Exception as e:
        log_traceback(e)
        return

    # Schritt 5: Mini-Funktionstest
    try:
        out = translate_text("Jaffa kree", goa2de, "goa2de")
        log("TEST: Jaffa kree -> " + str(out), "#85c97a")
    except Exception as e:
        log_traceback(e)

    log("=" * 40, "#d4af37")
    log("FERTIG. Engine laeuft auf dem Geraet.", "#d4af37")
    log("Diese Variante ist nur zum Diagnostizieren!", "#f5a623")
    log("Original wiederherstellen mit:", "#a0c0e0")
    log("  python make_diagnostic.py --restore", "#a0c0e0")


if __name__ == "__main__":
    ft.app(target=main)
