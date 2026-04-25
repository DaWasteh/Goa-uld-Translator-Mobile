@echo off
cd /d "c:\LAB\Goa'uld Translator Mobile"
call .venv\Scripts\activate.bat
flet build apk --verbose
