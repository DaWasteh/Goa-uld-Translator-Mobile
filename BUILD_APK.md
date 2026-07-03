# APK-Build Anleitung

## Voraussetzungen

1. **Flutter SDK** — Flet baut auf Flutter auf
   ```powershell
   # Prüfen ob Flutter installiert ist
   flutter doctor
   ```
   Falls nicht installiert: [Flutter Installation](https://flutter.dev/docs/get-started/install/windows)

2. **Java JDK** (11 oder höher) — für Android-Build
   ```powershell
   # Prüfen
   java --version
   ```

3. **Android SDK** — wird von Flutter automatisch bezogen, kann aber manuell benötigt werden:
   ```powershell
   flutter doctor --android-licenses
   ```

## Projektstruktur (bereinigt)

```
Goa'uld Translator Mobile/
├── app/                    # Flet App-Modul (main.py, theme.py)
├── goauld_engine/          # Engine-Modul (lexicon.py, yaml_loader.py, ...)
├── assets/                 # Nur Assets: YAML-Lexicon + MD-Dateien
│   ├── goa'uld_lexicon.yaml
│   ├── Goa'uld-Dictionary.md
│   ├── Goa'uld-Fictionary.md
│   ├── Goa'uld-Neologikum.md
│   └── Goa'uld-Wörterbuch.md
├── tests/                  # Tests
├── pyproject.toml          # Flet-Konfiguration mit Assets-Pfad
└── BUILD_APK.md            # Diese Datei
```

> **Wichtig:** Alle Daten-Dateien liegen NUR im `assets/`-Verzeichnis.
> Duplikate im Root wurden entfernt.

## Build-Schritte

### 1. Debug-APK (schnell, zum Testen)

```powershell
cd "H:\LAB\Goa'uld Translator Mobile"
flet build apk --arch arm64-v8a --clear-cache --verbose --yes
```

Oder per Skript:

```powershell
.\build_apk.bat
```

> Wichtig: Den generierten Ordner `build/flutter` nicht als primäre Quelle in
> Android Studio pflegen. `flet build apk` erzeugt dort `app/app.zip`, setzt die
> nötige `SERIOUS_PYTHON_SITE_PACKAGES`-Umgebung für Gradle und aktualisiert den
> Entrypoint. Wenn du direkt aus Android Studio startest, muss diese Env-Variable
> auf `<Projekt>\build\site-packages` zeigen.
>
> Der S25-Ultra-Fehler `ModuleNotFoundError: No module named "certifi"` entsteht,
> wenn ein x86_64/emulatorisches Python-Site-Packages-Bundle in einer ARM64-APK
> landet. Vor Geräte-Builds daher alte Artefakte löschen oder `--clear-cache`
> verwenden und anschließend prüfen, dass die APK `lib/arm64-v8a/libpythonsitepackages.so`
> enthält.

Die APK wird erstellt in:
```
build/apk/goauld-translator-mobile.apk
```

### 2. Release-APK (signiert, für Store/Verteilung)

#### Keystore erstellen (erstmals)

```powershell
# Keystore im Home-Verzeichnis erstellen
keytool -genkey -v -keystore "%USERPROFILE%\goauld-keystore.jks" `
  -storetype JKS -keyalg RSA -keysize 2048 -validity 10000 `
  -alias goauld `
  -dname "CN=Goa'uld Translator, OU=SGC, O=Xenolinguistics, C=DE" `
  -storepass "DEIN_PASSWORT" -keypass "DEIN_PASSWORT"
```

#### Signierung konfigurieren

In [`pyproject.toml`](pyproject.toml) die Signierung aktivieren:

```toml
[tool.flet]
bundle_id = "de.basti.goauld"

[tool.flet.android]
adaptive_icon_background = "#0a1628"

# Signierung (auskommentieren für Release-Build)
# signing.key_alias = "goauld"
# signing.store_file = "C:/Users/Sebas/goauld-keystore.jks"
# signing.store_password = "DEIN_PASSWORT"
# signing.key_password = "DEIN_PASSWORT"
```

#### Release-Build starten

```powershell
cd "L:\GitHub\Goa'uld Translator Mobile"
flet build apk --arch arm64-v8a --clear-cache --verbose --yes
```

## Deployment auf Gerät

### Per ADB (USB-Debugging)

```powershell
# Gerät verbinden und prüfen
adb devices

# APK installieren
adb install -r build/apk/goauld-translator-mobile.apk

# App starten
adb shell am start -n de.basti.goauld/.MainActivity
```

### Per Datei-Transfer (SD-Karte)

1. APK-Datei auf das Gerät kopieren
2. Datei-Manager öffnen und APK installieren
3. "Unbekannte Quellen" muss erlaubt sein

## Fehlerbehebung

### "Flutter SDK not found" / "flutter: command not found"

- Flutter SDK ist nicht im PATH
- Lösung: Flutter installieren oder Pfad setzen:
  ```powershell
  $env:PATH += ";C:\src\flutter\bin"
  flutter doctor
  ```

### "Flet app package app/app.zip was not created"

- Das ist ein echter Packaging-Fehler: ohne `build/flutter/app/app.zip` startet Python im APK nicht.
- Prüfen ob Paket und APK-Dateien existieren:
  ```powershell
  dir build\flutter\app\app.zip
  dir build\apk\*.apk
  ```
- Wenn keine APKs: Siehe "Build crasht mit Error" unten

### "Build failed" / "Gradle build failed"

```powershell
# Build-Artefakte löschen und Flet sauber neu paketieren
rmdir /s /q build
flet build apk --arch arm64-v8a --clear-cache --verbose --yes
```

Wenn Gradle/Lint unter Windows mit `FileSystemException ... kann nicht auf die Datei zugreifen`
oder Kotlin-Cache-Fehlern abbricht, sind meist alte Java/Gradle/Kotlin-Daemons oder Android
Studio an Cache-Dateien gebunden:

```powershell
# Android Studio schließen, dann Daemons finden/stoppen
jps -l
# PIDs von GradleDaemon/KotlinCompileDaemon ersetzen:
taskkill /PID <PID> /F /T

rmdir /s /q build
flet build apk --arch arm64-v8a --clear-cache --verbose --yes
```

### APK startet mit schwarzem Bildschirm

- Logs prüfen:
  ```powershell
  adb logcat | findstr -i "goauld python flutter"
  ```
- Asset-Pfade in [`goauld_engine/resources.py`](goauld_engine/resources.py) prüfen
- Umgebungsvariable `GOAULD_ASSETS_DIR` wird korrekt gesetzt?
- In [`app/main.py`](app/main.py:14) wird der Pfad vor Engine-Import gesetzt

### "Lexicon nicht gefunden" / "No YAML file found"

- `assets/goa'uld_lexicon.yaml` muss im APK enthalten sein
- Prüfen in [`pyproject.toml`](pyproject.toml:32):
  ```toml
  [tool.flet.assets]
  src = "assets"
  ```
- Das gesamte `assets/`-Verzeichnis wird automatisch ins APK gepackt

### "ImportError: yaml_loader"

- `yaml_loader.py` muss im `goauld_engine/`-Verzeichnis sein
- Nicht in `assets/` — das ist ein Python-Modul, kein Asset!

## Debugging auf Gerät

### Vollständige Logs

```powershell
# Alle Logs
adb logcat > logcat.txt

# Nur Goauld-Logs
adb logcat | findstr -i "goauld"

# Python-Logs
adb logcat | findstr -i "python"

# Flutter-Errors
adb logcat | findstr -i "flutter error"
```

### Asset-Verifikation im APK

```powershell
# APK ist eine ZIP-Datei
cd build\apk
7z l goauld-translator-mobile.apk

# Prüfen ob assets enthalten sind:
# assets/
# assets/goa'uld_lexicon.yaml
# assets/Goa'uld-Dictionary.md
# ...
```

## Manuelles Testen im Dev-Modus

```powershell
# Virtual Environment aktivieren
.venv\Scripts\activate

# App starten
python app.py

# Logs mit Debug-Level
python -c "import logging; logging.basicConfig(level=logging.DEBUG); exec(open('app.py').read())"
```

## Checkliste vor Release

- [ ] Flutter SDK installiert (`flutter doctor` zeigt OK)
- [ ] Android SDK Lizenzen akzeptiert (`flutter doctor --android-licenses`)
- [ ] Keystore erstellt (für Release)
- [ ] Signierung in `pyproject.toml` konfiguriert
- [ ] Assets in `assets/` vollständig (YAML + 4 MD-Dateien)
- [ ] `yaml_loader.py` in `goauld_engine/` (nicht in `assets/`!)
- [ ] Debug-APK erfolgreich gebaut und getestet
- [ ] Release-APK signiert gebaut
- [ ] APK auf Gerät installiert und gestartet

## Bekannte Einschränkungen

1. **Android 10+** benötigt `MANAGE_EXTERNAL_STORAGE` für bestimmte Asset-Zugriffe
2. **APK-Größe** — Flutter-Bundle ist ~20-30 MB, YAML + MD-Dateien sind minimal
3. **64-bit only** — Flet baut nur arm64-v8a und x86_64, keine armeabi-v7a
