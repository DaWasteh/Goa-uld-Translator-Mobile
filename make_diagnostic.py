# -*- coding: utf-8 -*-
"""
make_diagnostic.py — Macht die App sichtbar-debugbar.

Was es tut:
  • Verschiebt app.py (Root) und app/__main__.py (falls vorhanden) ins
    _backup_pre_fix/ — beide kollidieren mit dem app-Paket.
  • Sichert app/main.py → app/main.py.original (nur einmal).
  • Schreibt eine DIAGNOSE-Version von app/main.py, die bei jedem
    Schritt eine Statuszeile auf den Bildschirm schreibt und bei jeder
    Exception die volle Traceback anzeigt.

Verwendung:
    cd "C:\\LAB\\Goa'uld Translator Mobile"
    python make_diagnostic.py
    flet build apk --verbose
    # dann APK installieren und starten

Wenn die App jetzt startet, siehst du eine Liste in Gold:
    BOOT: main() gestartet
    BOOT: assets_dir = /...
    BOOT: lade Lexicon ...
    ...
oder eine Traceback in Rot. Genau das brauchen wir.

Wenn der Bug gefunden ist, kann man die Original-Datei wiederherstellen:
    python make_diagnostic.py --restore
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT / "app"
MAIN_PY = APP_DIR / "main.py"
ORIG = APP_DIR / "main.py.original"
BACKUP = ROOT / "_backup_pre_fix"


# ─────────────────────────────────────────────────────────────────────────
# Diagnose-Version von app/main.py
# ─────────────────────────────────────────────────────────────────────────

DIAGNOSTIC_MAIN = r'''# -*- coding: utf-8 -*-
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
'''


# ─────────────────────────────────────────────────────────────────────────
# Hilfsfunktionen
# ─────────────────────────────────────────────────────────────────────────

def info(msg): print(f"[INFO] {msg}")
def ok(msg):   print(f"[ OK ] {msg}")
def warn(msg): print(f"[WARN] {msg}")
def fail(msg): print(f"[FAIL] {msg}")


def stash_to_backup(src: Path, label: str) -> bool:
    if not src.exists():
        return False
    BACKUP.mkdir(exist_ok=True)
    target = BACKUP / src.name
    if target.exists():
        target.unlink()
    shutil.move(str(src), str(target))
    ok(f"{label}: {src.relative_to(ROOT)} → {target.relative_to(ROOT)}")
    return True


# ─────────────────────────────────────────────────────────────────────────
# Aktionen
# ─────────────────────────────────────────────────────────────────────────

def install_diagnostic() -> int:
    if not APP_DIR.is_dir():
        fail(f"app/-Ordner fehlt unter {APP_DIR}")
        fail("Erst fix_structure.py laufen lassen.")
        return 2

    if not MAIN_PY.exists():
        fail(f"app/main.py fehlt unter {MAIN_PY}")
        return 2

    # 1. Kollisionen wegräumen
    info("Räume Kollisionen weg ...")
    stash_to_backup(ROOT / "app.py", "Root app.py weggeräumt")
    stash_to_backup(APP_DIR / "__main__.py", "app/__main__.py weggeräumt")

    # 2. Original sichern (nur einmal)
    if not ORIG.exists():
        shutil.copy2(MAIN_PY, ORIG)
        ok(f"Original gesichert: {ORIG.relative_to(ROOT)}")
    else:
        info(f"Original-Sicherung existiert bereits: {ORIG.relative_to(ROOT)}")

    # 3. Diagnose-main.py schreiben
    MAIN_PY.write_text(DIAGNOSTIC_MAIN, encoding="utf-8")
    ok(f"Diagnose-Variante geschrieben: {MAIN_PY.relative_to(ROOT)}")

    # 4. Smoke-Test (Syntax)
    info("Smoke-Test: Syntax ...")
    import py_compile
    try:
        py_compile.compile(str(MAIN_PY), doraise=True)
        ok("Syntax OK")
    except py_compile.PyCompileError as e:
        fail(f"Syntax-Fehler: {e}")
        return 3

    print()
    ok("Fertig. Nächste Schritte:")
    print("    flutter clean")
    print("    flet build apk --verbose")
    print("    adb install -r build\\\\apk\\\\goauld-translator-mobile.apk")
    print("    # dann App vom Launcher starten")
    print()
    print("Du solltest goldene Boot-Zeilen sehen oder rote Fehlerzeilen.")
    print("Sende mir entweder das Screen-Foto davon oder schreibe es ab.")
    return 0


def restore() -> int:
    if not ORIG.exists():
        fail(f"Original-Sicherung fehlt: {ORIG.relative_to(ROOT)}")
        return 2
    shutil.copy2(ORIG, MAIN_PY)
    ok(f"Original wiederhergestellt: {MAIN_PY.relative_to(ROOT)}")
    ok("Du kannst jetzt wieder normal bauen.")
    return 0


# ─────────────────────────────────────────────────────────────────────────
# Entry
# ─────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Repo-Root: {ROOT}")
    print()
    if "--restore" in sys.argv:
        sys.exit(restore())
    sys.exit(install_diagnostic())
