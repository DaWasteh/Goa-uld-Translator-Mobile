# -*- coding: utf-8 -*-
"""Goa'uld Translator Mobile — Flet entry point."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

import flet as ft

# Set GOAULD_ASSETS_DIR before engine imports (Flet mobile asset path)
# Auf Desktop: assets/-Verzeichnis; auf Mobile: page.assets_dir (wird in main gesetzt)
os.environ["GOAULD_ASSETS_DIR"] = str(
    Path(__file__).resolve().parent.parent / "assets"
)

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
        self.lexicon: Any = None
        self.search_engine: Any = None
        self.analyzer: Any = None
        self.goa2de_map: dict = {}
        self.de2goa_map: dict = {}
        self.direction: str = "goa2de"  # oder "de2goa"

    def load(self):
        self.lexicon = load_full_lexicon()
        self.search_engine = SearchEngine(self.lexicon.entries)
        self.analyzer = SentenceAnalyzer(self.lexicon.entries)
        self.goa2de_map = build_mapping(self.lexicon.entries, "goa2de")
        self.de2goa_map = build_mapping(self.lexicon.entries, "de2goa")
        log.info("Lexicon geladen: %d Einträge (%s)",
                 len(self.lexicon.entries),
                 self.lexicon.source)


STATE = AppState()


# ─────────────────────────────────────────────────────────────
# UI-Hilfsfunktionen
# ─────────────────────────────────────────────────────────────
def _direction_label() -> str:
    """Label für die aktuelle Richtung."""
    return "GOA → DE" if STATE.direction == "goa2de" else "DE → GOA"


def _build_header(page: ft.Page) -> ft.Control:
    """Header mit Direction-Toggle."""
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


def _build_detail_card(hit: dict) -> ft.Control:
    """Detail-Ansicht für einen einzelnen Eintrag."""
    rows: list[ft.Control] = [
        ft.Text(
            hit.get("goa") or hit.get("goauld") or hit.get("term") or "?",
            size=22,
            weight=ft.FontWeight.BOLD,
            color="#d4af37",
            font_family="Courier",
        ),
    ]
    if "meaning_de" in hit:
        rows.append(ft.Text(f"DE: {hit['meaning_de']}", size=14, color="#e0e0e0"))
    if "meaning_en" in hit:
        rows.append(ft.Text(f"EN: {hit['meaning_en']}", size=14, color="#a0c0e0"))
    if "meaning" in hit:
        rows.append(ft.Text(
            f"Bedeutung: {hit['meaning']}",
            size=14,
            color="#e0e0e0",
        ))
    if "etymology" in hit:
        rows.append(ft.Text(
            f"Etymologie: {hit['etymology']}",
            size=12,
            color="#888888",
            italic=True,
        ))
    if "source" in hit:
        rows.append(ft.Text(
            f"Quelle: {hit['source']}",
            size=10,
            color="#666666",
        ))
    if "section" in hit:
        rows.append(ft.Text(
            f"Section: {hit['section']}",
            size=10,
            color="#666666",
        ))
    return ft.Column(rows, spacing=8)


def _make_result_row(
    hit: dict,
    detail_view: ft.Container,
    page: ft.Page,
) -> ft.Control:
    """Eine Zeile in der Suchergebnis-Liste."""
    term = hit.get("goa") or hit.get("goauld") or hit.get("term") or "?"
    meaning = (
        hit.get("meaning_de")
        or hit.get("meaning_en")
        or hit.get("meaning")
        or ""
    )
    score = hit.get("score", 0)

    def open_detail(e):
        detail_view.content = _build_detail_card(hit)
        page.update()

    return ft.Container(
        content=ft.Row(
            [
                ft.Text(
                    term,
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color="#d4af37",
                    font_family="Courier",
                    width=120,
                ),
                ft.Text(
                    meaning,
                    size=12,
                    color="#e0e0e0",
                    expand=True,
                ),
                ft.Text(
                    f"{score}",
                    size=10,
                    color="#888888",
                ),
            ],
        ),
        padding=8,
        bgcolor="#0f1f33",
        border_radius=4,
        on_click=open_detail,
        ink=True,
    )


def _build_briefing_tab(page: ft.Page) -> ft.Control:
    """Briefing-Tab: Such-Eingabe + Resultat-Liste + Detail-Karte."""
    search_input = ft.TextField(
        label="Suchbegriff",
        hint_text="Jaffa, kree …",
        autofocus=False,
        text_style=ft.TextStyle(font_family="Courier"),
        prefix_icon=ft.Icons.SEARCH,
    )

    results_list = ft.ListView(expand=True, spacing=4, padding=8)
    detail_view = ft.Container(
        content=ft.Text(
            "Wähle einen Eintrag aus der Liste.",
            color="#888888",
            italic=True,
        ),
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
            query,
            direction=STATE.direction,
            max_results=20,
        )
        for hit in hits:
            results_list.controls.append(
                _make_result_row(hit, detail_view, page),
            )
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


def _get_primary_text(primary) -> str:
    """Extrahiert den primären Übersetzungstext aus einem Token."""
    if primary is None:
        return "—"
    if isinstance(primary, dict):
        # primary ist ein Dictionary aus SearchEngine
        goa = primary.get("goauld") or primary.get("term") or ""
        mean = primary.get("meaning_de") or primary.get("meaning_en") or primary.get("meaning") or ""
        if goa and mean:
            return f"{goa} ({mean})"
        return goa or mean or "—"
    return str(primary)


def _get_alternative_texts(alternatives: list) -> list[str]:
    """Extrahiert Goa'uld-Terme aus Alternative-Dictionaries."""
    texts: list[str] = []
    for alt in (alternatives or []):
        if isinstance(alt, dict):
            term = alt.get("goauld") or alt.get("term") or ""
            if term:
                texts.append(term)
        elif alt:
            texts.append(str(alt))
    return texts


def _make_token_row(token: dict) -> ft.Control:
    """Eine Zeile pro Token in der Satz-Analyse."""
    raw = token.get("raw") or token.get("token") or "?"
    primary = token.get("primary") or token.get("translation") or None
    primary_text = _get_primary_text(primary)
    alternatives = token.get("alternatives") or []
    alt_texts = _get_alternative_texts(alternatives)
    tip = token.get("tip") or ""

    children: list[ft.Control] = [
        ft.Row([
            ft.Text(
                raw,
                size=14,
                weight=ft.FontWeight.BOLD,
                color="#d4af37",
                font_family="Courier",
                width=140,
            ),
            ft.Text(
                f"→ {primary_text}",
                size=14,
                color="#e0e0e0",
                expand=True,
            ),
        ]),
    ]
    if alt_texts:
        children.append(
            ft.Text(
                f"auch: {', '.join(alt_texts)}",
                size=11,
                color="#888888",
                italic=True,
            )
        )
    if tip:
        children.append(
            ft.Text(
                tip,
                size=10,
                color="#a0c0e0",
                italic=True,
            )
        )

    return ft.Container(
        content=ft.Column(children, spacing=2),
        padding=8,
        bgcolor="#0f1f33",
        border_radius=4,
    )


def _build_debrief_tab(page: ft.Page) -> ft.Control:
    """Debrief-Tab: Token-Analyse."""
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
        result = STATE.analyzer.analyze(
            text,
            direction=STATE.direction,
        )
        # 'result' ist eine Liste von Token-Dicts
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
            ft.Container(
                content=analyze_button,
                padding=ft.Padding(left=8, right=8, top=0, bottom=8),
            ),
            token_list,
        ],
        expand=True,
    )


def _build_live_tab(page: ft.Page) -> ft.Control:
    """Live-Tab: Echtzeit-Übersetzung mit Debounce."""
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
    debounce_task: dict[str, Any] = {"task": None}

    async def do_translate_debounced():
        await asyncio.sleep(0.3)  # 300 ms warten
        text = input_field.value.strip()
        if not text:
            output_field.content = ft.Text("…", color="#888888")
        else:
            mapping = (
                STATE.goa2de_map
                if STATE.direction == "goa2de"
                else STATE.de2goa_map
            )
            translated = translate_text(
                text,
                mapping,
                direction=STATE.direction,
            )
            output_field.content = ft.Text(
                translated,
                color="#e0e0e0",
                font_family="Courier",
                size=14,
            )
        page.update()

    def on_change(e):
        if (
            debounce_task["task"] is not None
            and not debounce_task["task"].done()
        ):
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


def main(page: ft.Page):
    page.title = "Goa'uld Translator"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0a1628"
    page.padding = 0

    # Flet stellt assets_dir auf Mobile bereit
    assets_dir = getattr(page, "assets_dir", None)
    if assets_dir:
        os.environ["GOAULD_ASSETS_DIR"] = assets_dir

    loading = ft.Text("Lade Lexicon …", size=16, color="#d4af37")
    page.add(loading)
    page.update()

    STATE.load()
    page.controls.clear()

    header = _build_header(page)
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=200,
        expand=True,
        tabs=[
            ft.Tab(
                label="Briefing",
                icon=ft.Icons.SEARCH,
                content=ft.Container(
                    content=_build_briefing_tab(page),
                    expand=True,
                ),
            ),
            ft.Tab(
                label="Debrief",
                icon=ft.Icons.PSYCHOLOGY,
                content=ft.Container(
                    content=_build_debrief_tab(page),
                    expand=True,
                ),
            ),
            ft.Tab(
                label="Live",
                icon=ft.Icons.BOLT,
                content=ft.Container(
                    content=_build_live_tab(page),
                    expand=True,
                ),
            ),
        ],
    )
    page.add(header, tabs)


if __name__ == "__main__":
    ft.app(target=main)