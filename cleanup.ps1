# cleanup.ps1 — Räumt veraltete Dateien, Backups und Build-Caches aus dem
# Goa'uld Translator Mobile-Projekt auf.
#
# Default ist DRY-RUN: zeigt nur was getan WÜRDE, löscht nichts.
# Erst mit -Force wird tatsächlich gelöscht.
#
# Nutzung:
#   .\cleanup.ps1                          # Dry-Run, zeigt Plan
#   .\cleanup.ps1 -Force                   # Tatsächlich löschen
#   .\cleanup.ps1 -Force -IncludeBuild     # Auch build/ löschen
#   .\cleanup.ps1 -Force -Verbose          # Mit Details

[CmdletBinding()]
param(
    [string]$Root = (Get-Location).Path,
    [switch]$Force,           # Ohne Force = Dry-Run
    [switch]$IncludeBuild     # Auch build/ löschen (kostet beim nächsten Build viel Zeit)
)

# ───────────────────────────────────────────────────────────────────────
# Was weg soll
# ───────────────────────────────────────────────────────────────────────

# Konkrete Dateien im Projekt-Root
$FilesToRemove = @(
    'make_diagnostic.py',          # Altes Diagnose-Onewayskript
    'patch_flet_api_v2.py',        # Altes Flet-Patch-Skript, mit Flet 0.84 obsolet
    'MIGRATION_NOTES.md',          # Alte Migrations-Doku
    'build.log',                   # Alte Build-Logs
    'build_attempt.log',
    'tree.md',                     # Tree-Skript-Output
    'treefull.md',                 # Vollständiger Tree-Dump
    'main_py.before_v2',           # Alte main.py-Backups
    'main_py.original',
    'main_py.pre_apipatch'
)

# Verzeichnisse im Projekt-Root die komplett weg sollen
$DirsToRemove = @(
    '_backup_pre_fix'              # Alter Pre-Fix-Backup
)

# Glob-Patterns für Datei-Müll (rekursiv im gesamten Projekt, AUSSER .venv)
$FilePatternsRecursive = @(
    '*.pyc',
    '*.pyo'
)

# Ordner die rekursiv gefunden und gelöscht werden (AUSSER in .venv)
$DirPatternsRecursive = @(
    '__pycache__',
    '.pytest_cache',
    '.mypy_cache',
    '.ruff_cache'
)

# Optional: build/ (mit -IncludeBuild)
if ($IncludeBuild) {
    $DirsToRemove += 'build'
}

# ───────────────────────────────────────────────────────────────────────
# Hilfs-Funktionen
# ───────────────────────────────────────────────────────────────────────

# Bytes lesbar formatieren
function Format-Size {
    param([long]$Bytes)
    if ($Bytes -ge 1GB) { return "{0:N2} GB" -f ($Bytes / 1GB) }
    if ($Bytes -ge 1MB) { return "{0:N2} MB" -f ($Bytes / 1MB) }
    if ($Bytes -ge 1KB) { return "{0:N1} KB" -f ($Bytes / 1KB) }
    return "$Bytes B"
}

# Größe eines Pfads (Datei oder Ordner rekursiv)
function Get-PathSize {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return 0 }
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    if ($null -eq $item) { return 0 }
    if ($item.PSIsContainer) {
        $sum = (Get-ChildItem -LiteralPath $Path -Recurse -Force -File -ErrorAction SilentlyContinue |
                Measure-Object -Property Length -Sum).Sum
        if ($null -eq $sum) { return 0 }
        return [long]$sum
    } else {
        return [long]$item.Length
    }
}

# Sammelt Kandidaten OHNE was zu löschen
function Get-CleanupCandidates {
    param([string]$Root)

    $venv = Join-Path $Root '.venv'
    $venvFull = if (Test-Path -LiteralPath $venv) { (Resolve-Path $venv).Path } else { $null }

    $candidates = [System.Collections.Generic.List[psobject]]::new()

    # 1. Konkrete Dateien im Root
    foreach ($name in $FilesToRemove) {
        $path = Join-Path $Root $name
        if (Test-Path -LiteralPath $path -PathType Leaf) {
            $candidates.Add([pscustomobject]@{
                Path     = $path
                Type     = 'file'
                Reason   = 'veraltet/Backup'
                Size     = Get-PathSize $path
            })
        }
    }

    # 2. Konkrete Verzeichnisse im Root
    foreach ($name in $DirsToRemove) {
        $path = Join-Path $Root $name
        if (Test-Path -LiteralPath $path -PathType Container) {
            $reason = if ($name -eq 'build') { 'Flet-Build-Cache' } else { 'veraltet/Backup' }
            $candidates.Add([pscustomobject]@{
                Path     = $path
                Type     = 'dir'
                Reason   = $reason
                Size     = Get-PathSize $path
            })
        }
    }

    # 3. Rekursive Datei-Patterns (außerhalb .venv)
    foreach ($pattern in $FilePatternsRecursive) {
        Get-ChildItem -LiteralPath $Root -Recurse -File -Force -Filter $pattern -ErrorAction SilentlyContinue |
            Where-Object { -not ($venvFull -and $_.FullName.StartsWith($venvFull, [StringComparison]::OrdinalIgnoreCase)) } |
            ForEach-Object {
                $candidates.Add([pscustomobject]@{
                    Path     = $_.FullName
                    Type     = 'file'
                    Reason   = "Pattern $pattern"
                    Size     = $_.Length
                })
            }
    }

    # 4. Rekursive Ordner-Patterns (außerhalb .venv)
    foreach ($pattern in $DirPatternsRecursive) {
        Get-ChildItem -LiteralPath $Root -Recurse -Directory -Force -Filter $pattern -ErrorAction SilentlyContinue |
            Where-Object { -not ($venvFull -and $_.FullName.StartsWith($venvFull, [StringComparison]::OrdinalIgnoreCase)) } |
            ForEach-Object {
                $candidates.Add([pscustomobject]@{
                    Path     = $_.FullName
                    Type     = 'dir'
                    Reason   = "Pattern $pattern"
                    Size     = Get-PathSize $_.FullName
                })
            }
    }

    return $candidates
}

# ───────────────────────────────────────────────────────────────────────
# Run
# ───────────────────────────────────────────────────────────────────────

$Root = (Resolve-Path $Root).Path
Write-Host ""
Write-Host "Goa'uld Translator Mobile — Cleanup" -ForegroundColor Cyan
Write-Host "Root: $Root"
if ($Force) {
    Write-Host "Modus: LIVE (löscht tatsächlich)" -ForegroundColor Yellow
} else {
    Write-Host "Modus: DRY-RUN (nichts wird gelöscht — Plan anzeigen)" -ForegroundColor Green
}
if ($IncludeBuild) {
    Write-Host "Build-Cache: WIRD MIT GELÖSCHT" -ForegroundColor Yellow
} else {
    Write-Host "Build-Cache: behalten (-IncludeBuild zum Löschen)" -ForegroundColor Gray
}
Write-Host ""

$candidates = Get-CleanupCandidates -Root $Root

if ($candidates.Count -eq 0) {
    Write-Host "Nichts zu tun — Projekt ist schon sauber." -ForegroundColor Green
    return
}

# Gruppiert ausgeben: Top-Level zuerst, dann die rekursiven Patterns kompakt
$topLevel = $candidates | Where-Object { $_.Reason -notlike 'Pattern*' }
$recursive = $candidates | Where-Object { $_.Reason -like 'Pattern*' }

if ($topLevel.Count -gt 0) {
    Write-Host "Top-Level:" -ForegroundColor Cyan
    foreach ($c in $topLevel | Sort-Object Path) {
        $rel = $c.Path.Substring($Root.Length).TrimStart('\','/')
        $marker = if ($c.Type -eq 'dir') { '[D]' } else { '[F]' }
        $size = Format-Size $c.Size
        Write-Host ("  {0} {1,-40} {2,12}  ({3})" -f $marker, $rel, $size, $c.Reason)
    }
    Write-Host ""
}

if ($recursive.Count -gt 0) {
    # Pro Pattern aggregieren
    Write-Host "Rekursiv:" -ForegroundColor Cyan
    $recursive | Group-Object Reason | ForEach-Object {
        $count = $_.Count
        $totalBytes = ($_.Group | Measure-Object Size -Sum).Sum
        Write-Host ("  {0,-22} {1,4} Stk.  {2,12}" -f $_.Name, $count, (Format-Size $totalBytes))
    }
    Write-Host ""

    # Bei -Verbose alle einzeln zeigen
    if ($VerbosePreference -eq 'Continue') {
        Write-Verbose "Detail-Liste rekursiver Funde:"
        foreach ($c in $recursive | Sort-Object Path) {
            $rel = $c.Path.Substring($Root.Length).TrimStart('\','/')
            Write-Verbose "  $rel"
        }
    }
}

$totalSize = ($candidates | Measure-Object Size -Sum).Sum
Write-Host ("Summe: {0} Einträge, {1}" -f $candidates.Count, (Format-Size $totalSize)) -ForegroundColor Cyan
Write-Host ""

if (-not $Force) {
    Write-Host "Das war Dry-Run. Wenn die Liste passt:" -ForegroundColor Green
    Write-Host "  .\cleanup.ps1 -Force" -ForegroundColor Green
    if (-not $IncludeBuild) {
        Write-Host "  .\cleanup.ps1 -Force -IncludeBuild   # auch build/ wegmachen" -ForegroundColor Gray
    }
    return
}

# Letzte Bestätigung bevor wir wirklich löschen
$reply = Read-Host "Wirklich löschen? [j/N]"
if ($reply -notmatch '^[jJyY]') {
    Write-Host "Abgebrochen." -ForegroundColor Yellow
    return
}

Write-Host ""
Write-Host "Lösche..." -ForegroundColor Yellow
$ok = 0
$fail = 0
foreach ($c in $candidates) {
    try {
        if ($c.Type -eq 'dir') {
            Remove-Item -LiteralPath $c.Path -Recurse -Force -ErrorAction Stop
        } else {
            Remove-Item -LiteralPath $c.Path -Force -ErrorAction Stop
        }
        $ok++
        Write-Verbose "  OK: $($c.Path)"
    } catch {
        $fail++
        Write-Warning "  FAIL: $($c.Path) — $($_.Exception.Message)"
    }
}

Write-Host ""
Write-Host ("Fertig: {0} gelöscht, {1} fehlgeschlagen, {2} freigegeben." -f $ok, $fail, (Format-Size $totalSize)) -ForegroundColor Green
