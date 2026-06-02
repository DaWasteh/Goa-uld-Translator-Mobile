# -*- coding: utf-8 -*-
"""Fallback entry point fuer: python -m app.

Der reguläre Flet/APK-Entrypoint ist inzwischen das Root-Modul main.py.
Diese Datei bleibt als kompatibler Fallback erhalten, falls manuell
``python -m app`` oder ein altes Flet-Template mit module="app" genutzt wird.
"""
import flet as ft
from app.main import main

ft.app(target=main)
