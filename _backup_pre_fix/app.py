"""Flet entry point for Goa'uld Translator Mobile."""

import flet as ft
from app.main import main


def main_entry():
    """Flet app entry point."""
    ft.app(target=main)


if __name__ == "__main__":
    main_entry()