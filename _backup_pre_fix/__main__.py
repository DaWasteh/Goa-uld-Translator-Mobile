# -*- coding: utf-8 -*-
"""
Entry point for: python -m app
Flet (serious_python) ruft das hier auf wenn es das app-Package startet.
"""
import flet as ft
from app.main import main

ft.app(target=main)