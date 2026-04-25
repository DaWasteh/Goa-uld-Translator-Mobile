# Goa'uld Translator Mobile

Flet-basierte Android-App für das Goa'uld Linguistische Interface.

## Voraussetzungen

- Flutter SDK (`flutter doctor`)
- Android SDK mit akzeptierten Lizenzen (`flutter doctor --android-licenses`)
- Python ≥ 3.10 mit Flet ≥ 0.21.0

## Build

Siehe [BUILD_APK.md](BUILD_APK.md) für Details.


# Gradle-Daemon killen (der hält die .jar-Datei)
Get-Process | Where-Object { $_.Name -match "java|gradle" } | Stop-Process -Force

# Kurz warten
Start-Sleep -Seconds 2

# Jetzt löschen
Remove-Item -Recurse -Force ".\build"

# Alle Java-Prozesse hart beenden
taskkill /F /IM java.exe /T

Start-Sleep -Seconds 2
Remove-Item -Recurse -Force ".\build"

flet build apk --template "C:\LAB\flet-build-template.zip" --verbose