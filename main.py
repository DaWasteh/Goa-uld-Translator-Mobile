# -*- coding: utf-8 -*-
"""Flet/serious_python entry point for packaged builds.

Flet's build tool resolves the entry point as a Python file stem in the app
root.  The real UI lives in :mod:`app.main`; this small shim keeps packaging
unambiguous and avoids the old app.py vs. app/ package name collision.
"""

import flet as ft

from app.main import main


if __name__ == "__main__":
    ft.app(target=main)
