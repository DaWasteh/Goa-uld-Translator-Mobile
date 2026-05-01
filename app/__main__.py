# -*- coding: utf-8 -*-
"""Entry point fuer: python -m app
serious_python ruft das hier auf, wenn es das app-Package auf Android startet.
DIESE DATEI MUSS EXISTIEREN, sonst bleibt der Bildschirm nach dem Splash
einfach blau (Python crasht mit ImportError, bevor irgendwelche UI gemalt
werden kann).
"""
import flet as ft
from app.main import main

ft.app(target=main)
