param(
    [Parameter(Mandatory = $true)]
    [string]$AppExe
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $AppExe)) {
    throw "Publisher executable not found: $AppExe"
}

$taskbar = Join-Path $env:APPDATA "Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar"
if (-not (Test-Path -LiteralPath $taskbar)) {
    Write-Host "Taskbar pin folder not found; skipping pin repair."
    exit 0
}

$shell = New-Object -ComObject WScript.Shell
$appDir = Split-Path -Parent $AppExe
$fixed = 0

foreach ($file in Get-ChildItem -LiteralPath $taskbar -Filter "*.lnk" -ErrorAction SilentlyContinue) {
    $shortcut = $shell.CreateShortcut($file.FullName)
    $target = [string]$shortcut.TargetPath
    $nameMatches = $file.BaseName -eq "Nuphillion Publisher"
    $targetMatches = $target -like "*NuphillionPublisher*" -or $target -like "*Nuphillion Publisher*flet*.exe"

    if (-not ($nameMatches -or $targetMatches)) {
        continue
    }

    $shortcut.TargetPath = $AppExe
    $shortcut.Arguments = ""
    $shortcut.WorkingDirectory = $appDir
    $shortcut.IconLocation = "$AppExe,0"
    $shortcut.Description = "Nuphillion Publisher"
    $shortcut.Save()
    $fixed++
}

if ($fixed -gt 0) {
    Write-Host "Repaired $fixed Nuphillion Publisher taskbar pin(s)."
} else {
    Write-Host "No existing Nuphillion Publisher taskbar pin needed repair."
}
