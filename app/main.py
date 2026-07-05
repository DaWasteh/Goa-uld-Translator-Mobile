# -*- coding: utf-8 -*-
"""Goa'uld Translator Mobile — Flet entry point."""

import asyncio
import logging
import os
import sys
import traceback
from pathlib import Path
from typing import Any

import flet as ft

# Engine-Pfad hinzufügen — funktioniert in Dev und im APK
_me = Path(__file__).resolve().parent
_engine_candidates = [
    _me.parent,            # Repo-Root (wenn app/ Unterordner ist)
    _me,                   # app/ selbst (wenn goauld_engine/ im selben Verzeichnis)
]
for _cand in _engine_candidates:
    if (Path(_cand) / "goauld_engine").exists():
        if str(_cand) not in sys.path:
            sys.path.insert(0, str(_cand))
        break
else:
    if (_me.parent.parent / "goauld_engine").exists():
        if str(_me.parent.parent) not in sys.path:
            sys.path.insert(0, str(_me.parent.parent))

from goauld_engine import (  # noqa: E402
    load_full_lexicon,
    SearchEngine,
    SentenceAnalyzer,
    build_mapping,
    translate_text,
    get_app_dir,
)

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("goauld.mobile")

class AppState:
    def __init__(self):
        self.lexicon: Any = None
        self.search_engine: Any = None
        self.analyzer: Any = None
        self.goa2de_map: dict = {}
        self.de2goa_map: dict = {}
        self.direction: str = "de2goa"
        self.refresh_lexicon = None
        self.refresh_translator = None

    def load(self):
        app_dir = get_app_dir()
        self.lexicon = load_full_lexicon()
        
        if not self.lexicon.entries:
            log.error("Lexicon leer!")
            raise RuntimeError("Lexicon leer — keine Wörterbuch-Dateien gefunden.")
        
        self.search_engine = SearchEngine(self.lexicon.entries)
        self.analyzer = SentenceAnalyzer(self.lexicon.entries)
        self.goa2de_map = build_mapping(self.lexicon.entries, "goa2de")
        self.de2goa_map = build_mapping(self.lexicon.entries, "de2goa")
        log.info("Lexicon geladen: %d Einträge", len(self.lexicon.entries))

STATE = AppState()

def _direction_label() -> str:
    return "GOA → DE" if STATE.direction == "goa2de" else "DE → GOA"

def _build_header(page: ft.Page) -> ft.Control:
    def toggle_direction(e):
        STATE.direction = "de2goa" if STATE.direction == "goa2de" else "goa2de"
        direction_label.value = _direction_label()

        if STATE.refresh_lexicon: STATE.refresh_lexicon()
        if STATE.refresh_translator: page.run_task(STATE.refresh_translator)
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

def _show_detail_sheet(hit: dict, page: ft.Page):
    def close_sheet(e):
        sheet.open = False
        page.update()

    term = hit.get("goa") or hit.get("goauld") or hit.get("term") or "?"
    lang = hit.get("lang", "??").upper()

    rows = [
        ft.Row([
            ft.Text(term, size=24, weight=ft.FontWeight.BOLD, color="#d4af37", font_family="Courier", expand=True),
            ft.IconButton(ft.Icons.CLOSE, on_click=close_sheet, icon_color="#888888")
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Text(f"Sprache: {lang}", size=12, color="#888888"),
        ft.Divider(height=1, color="#1a3a5c"),
    ]

    if "meaning" in hit:
        rows.append(ft.Text("BEDEUTUNG", size=10, weight=ft.FontWeight.BOLD, color="#d4af37"))
        rows.append(ft.Text(hit['meaning'], size=16, color="#e0e0e0"))

    if hit.get("etymology"):
        rows.append(ft.Text("ETYMOLOGIE", size=10, weight=ft.FontWeight.BOLD, color="#d4af37"))
        rows.append(ft.Text(hit['etymology'], size=14, color="#a0c0e0", italic=True))

    metadata = []
    if hit.get("source"): metadata.append(f"Quelle: {hit['source']}")
    if hit.get("section"): metadata.append(f"Section: {hit['section']}")

    if metadata:
        rows.append(ft.Text("\n".join(metadata), size=10, color="#666666"))

    sheet = ft.BottomSheet(
        ft.Container(
            ft.Column(rows, tight=True, spacing=10),
            padding=20,
            bgcolor="#0f1f33",
            border_radius=ft.border_radius.only(top_left=16, top_right=16),
        ),
        open=True,
    )
    page.overlay.append(sheet)
    page.update()

def _make_result_row(hit: dict, page: ft.Page) -> ft.Control:
    term = hit.get("goa") or hit.get("goauld") or hit.get("term") or "?"
    meaning = hit.get("meaning") or ""

    return ft.Container(
        content=ft.Column([
            ft.Text(term, size=16, weight=ft.FontWeight.BOLD, color="#d4af37", font_family="Courier"),
            ft.Text(meaning, size=14, color="#e0e0e0", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
        ], spacing=2),
        padding=12,
        bgcolor="#0f1f33",
        border_radius=8,
        on_click=lambda _: _show_detail_sheet(hit, page),
        ink=True,
    )

def _build_lexicon_tab(page: ft.Page) -> ft.Control:
    search_input = ft.TextField(
        label="Lexikon durchsuchen",
        hint_text="Jaffa, kree …",
        prefix_icon=ft.Icons.SEARCH,
        text_style=ft.TextStyle(font_family="Courier"),
        border_color="#1a3a5c",
        focused_border_color="#d4af37",
    )

    results_list = ft.ListView(expand=True, spacing=8, padding=12)

    def do_search(e=None):
        query = search_input.value.strip()
        results_list.controls.clear()
        if len(query) < 2:
            page.update()
            return
        hits = STATE.search_engine.search(query, direction=STATE.direction, max_results=30)
        for hit in hits:
            results_list.controls.append(_make_result_row(hit, page))
        page.update()

    search_input.on_change = do_search
    STATE.refresh_lexicon = do_search

    return ft.Column([
        ft.Container(content=search_input, padding=12),
        results_list,
    ], expand=True)

def _make_analysis_row(token: dict) -> ft.Control:
    raw = token.get("raw") or token.get("token") or "?"
    primary = token.get("primary") or token.get("translation")
    primary_text = ""
    if isinstance(primary, dict):
        goa = primary.get("goauld") or primary.get("term") or ""
        mean = primary.get("meaning") or ""
        primary_text = f"{goa} ({mean})" if goa and mean else (goa or mean)
    else:
        primary_text = str(primary) if primary else "—"

    return ft.Container(
        content=ft.Row([
            ft.Text(raw, size=14, weight=ft.FontWeight.BOLD, color="#d4af37", font_family="Courier", width=100),
            ft.Text(f"→ {primary_text}", size=14, color="#e0e0e0", expand=True),
        ]),
        padding=8,
        bgcolor="#0a1828",
        border_radius=4,
    )

def _build_translator_tab(page: ft.Page) -> ft.Control:
    input_field = ft.TextField(
        label="Satz eingeben",
        multiline=True,
        min_lines=2,
        max_lines=4,
        hint_text="Jaffa, kree!",
        text_style=ft.TextStyle(font_family="Courier"),
    )

    live_output = ft.Text("…", size=18, color="#d4af37", font_family="Courier", weight=ft.FontWeight.BOLD)
    analysis_list = ft.ListView(expand=True, spacing=4)

    async def update_translation():
        await asyncio.sleep(0.3)
        text = input_field.value.strip()
        analysis_list.controls.clear()

        if not text:
            live_output.value = "…"
        else:
            mapping = STATE.goa2de_map if STATE.direction == "goa2de" else STATE.de2goa_map
            analysis = STATE.analyzer.analyze(text, direction=STATE.direction)
            live_output.value = (
                STATE.analyzer.build_translation(analysis, direction=STATE.direction)
                if analysis else translate_text(text, mapping, direction=STATE.direction)
            )
            for token in analysis:
                analysis_list.controls.append(_make_analysis_row(token))

        page.update()

    debounce_task = {"task": None}
    def on_change(e):
        if debounce_task["task"] and not debounce_task["task"].done():
            debounce_task["task"].cancel()
        debounce_task["task"] = page.run_task(update_translation)

    input_field.on_change = on_change
    STATE.refresh_translator = update_translation

    return ft.Column([
        ft.Container(content=input_field, padding=12),
        ft.Container(
            content=ft.Column([
                ft.Text("DIREKT-ÜBERSETZUNG", size=10, weight=ft.FontWeight.BOLD, color="#888888"),
                live_output,
                ft.Divider(height=20, color="#1a3a5c"),
                ft.Text("WORT-ANALYSE", size=10, weight=ft.FontWeight.BOLD, color="#888888"),
                analysis_list
            ], expand=True),
            padding=12,
            expand=True
        )
    ], expand=True)

def _build_error_view(error_msg: str, stack_trace: str = "") -> ft.Column:
    return ft.Column([
        ft.Icon(ft.Icons.WARNING_AMBER, size=64, color="#ff6b6b"),
        ft.Text("FEHLER BEIM START", size=20, weight=ft.FontWeight.BOLD, color="#ff6b6b"),
        ft.Text(error_msg, size=14, color="#e0e0e0", text_align=ft.TextAlign.CENTER),
    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)

def main(page: ft.Page):
    page.title = "Goa'uld Translator"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0a1628"
    page.padding = 0

    loading = ft.Container(
        ft.Column([
            ft.ProgressRing(color="#d4af37"),
            ft.Text("Initialisiere Lexicon...", color="#d4af37")
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        alignment=ft.Alignment(0, 0),
        expand=True
    )
    page.add(loading)
    page.update()

    try:
        STATE.load()
    except Exception as e:
        page.controls.clear()
        page.add(_build_error_view(str(e), traceback.format_exc()))
        page.update()
        return

    page.controls.clear()
    header = _build_header(page)

    _tabs = ft.Tabs(
        length=2,
        selected_index=0,
        expand=True,
        content=ft.Column([
            ft.TabBar(
                tabs=[
                    ft.Tab(label="Lexikon", icon=ft.Icons.BOOK),
                    ft.Tab(label="Übersetzer", icon=ft.Icons.TRANSLATE),
                ],
                label_color="#d4af37",
                unselected_label_color="#8a7228",
                indicator_color="#d4af37",
            ),
            ft.TabBarView(
                expand=True,
                controls=[
                    _build_lexicon_tab(page),
                    _build_translator_tab(page),
                ],
            ),
        ], expand=True),
    )

    page.add(header, _tabs)

if __name__ == "__main__":
    ft.app(target=main)
    