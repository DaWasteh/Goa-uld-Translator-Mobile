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
    echo Bitte z.B. ausfuehren: py -3 -m pip install flet==0.85.2 certifi pyyaml==6.0.2
    exit /b 1
)

REM Alte Gradle/Kotlin-Daemons koennen unter Windows Lint-/Cache-Dateien sperren.
if exist "build\flutter\android\gradlew.bat" (
    pushd "build\flutter\android"
    call gradlew.bat --stop >nul 2>nul
    popd
)
set "GRADLE_OPTS=-Dorg.gradle.daemon=false -Dkotlin.compiler.execution.strategy=in-process %GRADLE_OPTS%"

echo Bereinige alte Build-Artefakte, damit kein x86_64-site-packages-Bundle im ARM64-APK landet...
if exist "build\site-packages" rmdir /s /q "build\site-packages"
if exist "build\flutter" rmdir /s /q "build\flutter"
if exist "build\apk" rmdir /s /q "build\apk"

flet build apk --arch arm64-v8a --clear-cache --verbose --yes
if errorlevel 1 exit /b %errorlevel%

python -c "import pathlib, sys, zipfile; apk=pathlib.Path('build/apk/goauld-translator-mobile.apk'); assert apk.exists(), f'Missing {apk}'; names=zipfile.ZipFile(apk).namelist(); required=['lib/arm64-v8a/libpythonsitepackages.so','assets/flutter_assets/app/app.zip']; missing=[n for n in required if n not in names]; assert not missing, 'APK unvollstaendig: '+', '.join(missing); print('APK OK:', apk)"
if errorlevel 1 exit /b %errorlevel%
