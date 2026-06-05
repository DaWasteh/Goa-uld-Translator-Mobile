@echo off
setlocal
cd /d "%~dp0"

REM Android Studio bringt ein passendes JDK mit; fuer CLI-Builds in PATH setzen.
if exist "C:\Program Files\Android\Android Studio\jbr\bin\java.exe" (
    set "JAVA_HOME=C:\Program Files\Android\Android Studio\jbr"
    set "PATH=%JAVA_HOME%\bin;%PATH%"
)

REM Optionales venv nur aktivieren, wenn es nicht defekt ist.
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -c "import sys" >nul 2>nul
    if not errorlevel 1 call ".venv\Scripts\activate.bat"
)

flet --version >nul 2>nul
if errorlevel 1 (
    echo Flet CLI wurde nicht gefunden oder das lokale .venv ist defekt.
    echo Bitte z.B. ausfuehren: py -3 -m pip install flet==0.85.2 pyyaml==6.0.2
    exit /b 1
)

flet build apk --arch arm64-v8a --verbose
