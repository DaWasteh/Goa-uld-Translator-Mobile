# gettree.ps1 — Erzeugt einen kompakten Projekt-Tree für Diagnose.
# Schließt venv, Build-Caches, __pycache__, .git etc. aus.
# Nutzung:
#   .\gettree.ps1                  # nach tree.md schreiben
#   .\gettree.ps1 -OutFile foo.md  # eigener Pfad
#   .\gettree.ps1 -MaxDepth 4      # Tiefe begrenzen

[CmdletBinding()]
param(
    [string]$Root = (Get-Location).Path,
    [string]$OutFile = "tree.md",
    [int]$MaxDepth = 6
)

# Ordner, die komplett ignoriert werden (Name-Match, beliebige Tiefe)
$IgnoreDirs = @(
    '.venv', 'venv', 'env',
    '.git', '.idea', '.vscode',
    '.mypy_cache', '.pytest_cache', '.ruff_cache',
    '__pycache__',
    'Lib', 'Scripts', 'Include',           # Venv-Reste am Root
    'build', 'dist',                       # Flet-Build-Output
    'build_old_*',                         # alte Build-Backups
    '_backup_*',                           # manuelle Backups
    'node_modules'
)

# Datei-Patterns die ignoriert werden
$IgnoreFiles = @(
    '*.pyc', '*.pyo', '*.pyd',
    '*.log',
    '*.dll', '*.so', '*.dylib',
    '*.tar.gz', '*.zip', '*.whl',
    '.DS_Store', 'Thumbs.db'
)

function Test-IgnoreDir {
    param([string]$Name)
    foreach ($pattern in $IgnoreDirs) {
        if ($Name -like $pattern) { return $true }
    }
    return $false
}

function Test-IgnoreFile {
    param([string]$Name)
    foreach ($pattern in $IgnoreFiles) {
        if ($Name -like $pattern) { return $true }
    }
    return $false
}

function Write-TreeNode {
    param(
        [string]$Path,
        [string]$Prefix = '',
        [int]$Depth = 0,
        [System.Collections.Generic.List[string]]$Lines
    )

    if ($Depth -ge $MaxDepth) {
        $Lines.Add("$Prefix... (max-depth)")
        return
    }

    $items = Get-ChildItem -LiteralPath $Path -Force -ErrorAction SilentlyContinue |
        Where-Object {
            if ($_.PSIsContainer) {
                -not (Test-IgnoreDir $_.Name)
            } else {
                -not (Test-IgnoreFile $_.Name)
            }
        } |
        Sort-Object @{Expression = { -not $_.PSIsContainer }}, Name
    # Ordner zuerst, dann Dateien — alphabetisch innerhalb

    $count = $items.Count
    for ($i = 0; $i -lt $count; $i++) {
        $item = $items[$i]
        $isLast = ($i -eq $count - 1)
        $connector = if ($isLast) { '└── ' } else { '├── ' }
        $childPrefix = if ($isLast) { '    ' } else { '│   ' }

        if ($item.PSIsContainer) {
            $Lines.Add("$Prefix$connector$($item.Name)/")
            Write-TreeNode -Path $item.FullName `
                           -Prefix "$Prefix$childPrefix" `
                           -Depth ($Depth + 1) `
                           -Lines $Lines
        } else {
            $size = if ($item.Length -gt 1024) {
                "  ({0:N0} KB)" -f ($item.Length / 1024)
            } else { '' }
            $Lines.Add("$Prefix$connector$($item.Name)$size")
        }
    }
}

# --- Run ---
$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add("# Projekt-Tree (gefiltert)")
$lines.Add("")
$lines.Add("Root: ``$Root``")
$lines.Add("Erzeugt: $(Get-Date -Format 'yyyy-MM-dd HH:mm')")
$lines.Add("Max-Depth: $MaxDepth")
$lines.Add("")
$lines.Add('```')
$lines.Add((Split-Path -Leaf $Root) + '/')

Write-TreeNode -Path $Root -Lines $lines

$lines.Add('```')

$lines | Out-File -FilePath $OutFile -Encoding utf8
Write-Host "Tree geschrieben nach: $OutFile  ($($lines.Count) Zeilen)" -ForegroundColor Green
