param(
    [string]$Python,
    [string]$Project,
    [string]$BuildRoot,
    [switch]$IncludeIntro,
    [switch]$SelfTest
)

$ErrorActionPreference = "Stop"

$requiredPaths = @{
    Python = $Python
    Project = $Project
}
foreach ($item in $requiredPaths.GetEnumerator()) {
    if ([string]::IsNullOrWhiteSpace($item.Value)) {
        Write-Host "[ERROR] build_progress.ps1 received an empty value for $($item.Key)."
        exit 2
    }
}

if ([string]::IsNullOrWhiteSpace($BuildRoot)) {
    $BuildRoot = Join-Path $Project "build\pyinstaller"
}

$WorkPath = Join-Path $BuildRoot "work"
$SpecPath = Join-Path $BuildRoot "spec"
$DistPath = Join-Path $BuildRoot "dist"
$LogPath = Join-Path $BuildRoot "build.log"
$LastSecondsPath = Join-Path $BuildRoot "last_build_seconds.txt"

New-Item -ItemType Directory -Path $BuildRoot, $WorkPath, $SpecPath, $DistPath -Force | Out-Null

if ($SelfTest) {
    Write-Host "BuildRoot=$BuildRoot"
    Write-Host "WorkPath=$WorkPath"
    Write-Host "SpecPath=$SpecPath"
    Write-Host "DistPath=$DistPath"
    Write-Host "LogPath=$LogPath"
    Write-Host "LastSecondsPath=$LastSecondsPath"
    exit 0
}

function Format-Duration([double]$seconds) {
    if ($seconds -lt 0 -or [double]::IsNaN($seconds) -or [double]::IsInfinity($seconds)) {
        return "--:--"
    }
    $span = [TimeSpan]::FromSeconds([Math]::Max(0, [Math]::Round($seconds)))
    if ($span.TotalHours -ge 1) {
        return "{0:00}:{1:00}:{2:00}" -f [int]$span.TotalHours, $span.Minutes, $span.Seconds
    }
    return "{0:00}:{1:00}" -f [int]$span.TotalMinutes, $span.Seconds
}

function Write-BuildProgress([double]$percent, [double]$elapsed, [double]$eta, [string]$phase) {
    $width = 28
    $filled = [Math]::Min($width, [Math]::Max(0, [Math]::Floor(($percent / 100.0) * $width)))
    $empty = $width - $filled
    $bar = ("#" * $filled) + ("." * $empty)
    $line = "[{0}] {1,5:0.0}%  elapsed {2}  eta {3}  {4}" -f $bar, $percent, (Format-Duration $elapsed), (Format-Duration $eta), $phase
    Write-Host ("`r" + $line.PadRight(110)) -NoNewline
}

function Quote-ProcessArgument([string]$arg) {
    if ($null -eq $arg) {
        return '""'
    }
    if ($arg.Length -eq 0) {
        return '""'
    }
    if ($arg -notmatch '[\s"]') {
        return $arg
    }

    $builder = [System.Text.StringBuilder]::new()
    [void]$builder.Append('"')
    $backslashes = 0
    foreach ($char in $arg.ToCharArray()) {
        if ($char -eq '\') {
            $backslashes++
            continue
        }
        if ($char -eq '"') {
            [void]$builder.Append('\' * (($backslashes * 2) + 1))
            [void]$builder.Append('"')
            $backslashes = 0
            continue
        }
        if ($backslashes -gt 0) {
            [void]$builder.Append('\' * $backslashes)
            $backslashes = 0
        }
        [void]$builder.Append($char)
    }
    if ($backslashes -gt 0) {
        [void]$builder.Append('\' * ($backslashes * 2))
    }
    [void]$builder.Append('"')
    return $builder.ToString()
}

$root = Split-Path -Parent $LogPath
$stdoutLog = Join-Path $root "pyinstaller.stdout.log"
$stderrLog = Join-Path $root "pyinstaller.stderr.log"
Remove-Item -LiteralPath $stdoutLog, $stderrLog -Force -ErrorAction SilentlyContinue

$expectedSeconds = 240.0
if (Test-Path -LiteralPath $LastSecondsPath) {
    $last = Get-Content -LiteralPath $LastSecondsPath -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($last -as [double]) {
        $expectedSeconds = [Math]::Max(30.0, [double]$last)
    }
}

$args = @(
    "-m", "PyInstaller",
    (Join-Path $Project "src\mod_tool.py"),
    "--onefile",
    "--noconsole",
    "--noconfirm",
    "--noupx",
    "--name", "Halo Wars 2 Modding Suite",
    "--icon", (Join-Path $Project "assets\icon.ico"),
    "--version-file", (Join-Path $Project "build\version_info.txt"),
    "--paths", (Join-Path $Project "src"),
    "--add-data=$((Join-Path $Project "assets\background.png")):assets",
    "--add-data=$((Join-Path $Project "assets\icon.ico")):assets",
    "--add-data=$((Join-Path $Project "src\Modules\Library")):Modules\Library",
    "--add-data=$((Join-Path $Project "tools")):tools",
    "--add-data=$((Join-Path $Project "src\Modules")):Modules",
    "--add-data=$((Join-Path $Project "src\pfx_editor_pyside.py")):.",
    "--add-data=$((Join-Path $Project "src\player_colors_pyside.py")):.",
    "--add-data=$((Join-Path $Project "src\triggerscript_editor.py")):.",
    "--add-data=$((Join-Path $Project "src\triggerscript_parser.py")):.",
    "--add-data=$((Join-Path $Project "src\triggerscript_help.py")):.",
    "--add-data=$((Join-Path $Project "src\triggerscript_graph.py")):.",
    "--hidden-import", "flet_desktop",
    "--hidden-import", "pfx_editor_pyside",
    "--hidden-import", "player_colors_pyside",
    "--hidden-import", "triggerscript_editor",
    "--hidden-import", "triggerscript_parser",
    "--hidden-import", "triggerscript_help",
    "--hidden-import", "triggerscript_graph",
    "--hidden-import", "hw2_ai_editor.main",
    "--collect-submodules", "hw2_ai_editor",
    "--hidden-import", "PySide6.QtCore",
    "--hidden-import", "PySide6.QtGui",
    "--hidden-import", "PySide6.QtWidgets",
    "--exclude-module", "PySide6.QtQml",
    "--exclude-module", "PySide6.QtQuick",
    "--exclude-module", "PySide6.QtWebEngineCore",
    "--exclude-module", "PySide6.QtWebEngineWidgets",
    "--exclude-module", "PySide6.QtNetwork",
    "--exclude-module", "PySide6.QtSql",
    "--exclude-module", "PySide6.QtTest",
    "--exclude-module", "PySide6.QtDesigner",
    "--collect-all", "flet_desktop",
    "--collect-all", "flet",
    "--workpath", $WorkPath,
    "--specpath", $SpecPath,
    "--distpath", $DistPath
)

if ($IncludeIntro) {
    $args += "--add-data=$((Join-Path $Project "assets\intro.mp4")):assets"
}

$distExe = Join-Path $DistPath "Halo Wars 2 Modding Suite.exe"

function Get-LatestInputWriteTimeUtc([string[]]$paths) {
    $latest = [DateTime]::MinValue
    foreach ($path in $paths) {
        if (-not (Test-Path -LiteralPath $path)) {
            continue
        }
        $item = Get-Item -LiteralPath $path -Force
        if ($item.PSIsContainer) {
            foreach ($child in Get-ChildItem -LiteralPath $path -File -Recurse -Force -ErrorAction SilentlyContinue) {
                if ($child.FullName -like "*\__pycache__\*") { continue }
                if ($child.FullName -like "*\.pytest_cache\*") { continue }
                if ($child.LastWriteTimeUtc -gt $latest) {
                    $latest = $child.LastWriteTimeUtc
                }
            }
        } elseif ($item.LastWriteTimeUtc -gt $latest) {
            $latest = $item.LastWriteTimeUtc
        }
    }
    return $latest
}

$buildInputs = @(
    (Join-Path $Project "src"),
    (Join-Path $Project "tools"),
    (Join-Path $Project "assets\background.png"),
    (Join-Path $Project "assets\icon.ico"),
    (Join-Path $Project "build\version_info.txt"),
    $PSCommandPath
)
if ($IncludeIntro) {
    $buildInputs += (Join-Path $Project "assets\intro.mp4")
}

if ((Test-Path -LiteralPath $distExe) -and ($env:HW2_FORCE_REBUILD -ne "1")) {
    $exeTime = (Get-Item -LiteralPath $distExe).LastWriteTimeUtc
    $latestInput = Get-LatestInputWriteTimeUtc $buildInputs
    if ($latestInput -ne [DateTime]::MinValue -and $exeTime -ge $latestInput) {
        Write-BuildProgress 100.0 0.0 0.0 "cached executable current"
        Write-Host ""
        exit 0
    }
}

$started = Get-Date
$startInfo = [System.Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $Python
$startInfo.UseShellExecute = $false
$startInfo.RedirectStandardOutput = $true
$startInfo.RedirectStandardError = $true
$startInfo.CreateNoWindow = $true
if ($null -ne $startInfo.ArgumentList) {
    foreach ($arg in $args) {
        [void]$startInfo.ArgumentList.Add($arg)
    }
} else {
    $startInfo.Arguments = ($args | ForEach-Object { Quote-ProcessArgument $_ }) -join " "
}

$process = [System.Diagnostics.Process]::new()
$process.StartInfo = $startInfo
[void]$process.Start()
$stdoutTask = $process.StandardOutput.ReadToEndAsync()
$stderrTask = $process.StandardError.ReadToEndAsync()
$phases = @("analyzing imports", "collecting assets", "packing binaries", "compressing onefile", "finalizing executable")
$tick = 0

while (-not $process.HasExited) {
    $elapsed = ((Get-Date) - $started).TotalSeconds
    $percent = [Math]::Min(96.0, [Math]::Max(7.0, ($elapsed / $expectedSeconds) * 92.0))
    $eta = [Math]::Max(0.0, $expectedSeconds - $elapsed)
    $phase = $phases[[Math]::Min($phases.Count - 1, [Math]::Floor(($percent / 100.0) * $phases.Count))]
    $spark = @("|", "/", "-", "\")[$tick % 4]
    Write-BuildProgress $percent $elapsed $eta "$phase $spark"
    Start-Sleep -Milliseconds 600
    $tick++
    $process.Refresh()
}
$process.WaitForExit()
$stdoutText = $stdoutTask.GetAwaiter().GetResult()
$stderrText = $stderrTask.GetAwaiter().GetResult()
if ($stdoutText) {
    $stdoutText | Set-Content -LiteralPath $stdoutLog
}
if ($stderrText) {
    $stderrText | Set-Content -LiteralPath $stderrLog
}

$elapsedFinal = ((Get-Date) - $started).TotalSeconds
Write-BuildProgress 100.0 $elapsedFinal 0.0 "complete"
Write-Host ""

if (Test-Path -LiteralPath $stdoutLog) {
    Get-Content -LiteralPath $stdoutLog | Add-Content -LiteralPath $LogPath
}
if (Test-Path -LiteralPath $stderrLog) {
    Get-Content -LiteralPath $stderrLog | Add-Content -LiteralPath $LogPath
}

if ($process.ExitCode -eq 0) {
    [Math]::Max(1, [Math]::Round($elapsedFinal)) | Set-Content -LiteralPath $LastSecondsPath
}

exit $process.ExitCode
