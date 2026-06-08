param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectRoot,

    [Parameter(Mandatory = $true)]
    [string]$Log
)

$ErrorActionPreference = "Stop"

function Write-BuildLog {
    param([string]$Message)
    Add-Content -LiteralPath $Log -Value $Message
}

$project = (Resolve-Path -LiteralPath $ProjectRoot).Path
$rustDir = Join-Path $project "src-rust\HW2Packager"
$manifest = Join-Path $rustDir "Cargo.toml"
$sourceExe = Join-Path $rustDir "target\release\hw2pkg.exe"
$publishDir = Join-Path $project "tools\HW2Packager"
$publishExe = Join-Path $publishDir "hw2pkg.exe"

Write-BuildLog "[INFO] Rust project root: `"$project`""
Write-BuildLog "[INFO] Cargo manifest: `"$manifest`""
Write-BuildLog "[INFO] Rust packager source exe: `"$sourceExe`""
Write-BuildLog "[INFO] Rust packager publish exe: `"$publishExe`""

$cargo = Get-Command cargo -ErrorAction SilentlyContinue
if (-not $cargo) {
    if (Test-Path -LiteralPath $publishExe) {
        Write-BuildLog "[WARN] Cargo not found; using existing fast packager."
        exit 0
    }

    Write-BuildLog "[ERROR] Cargo is not installed and no existing fast packager was found:"
    Write-BuildLog "[ERROR] $publishExe"
    exit 1
}

if (-not (Test-Path -LiteralPath $manifest)) {
    Write-BuildLog "[ERROR] Cargo manifest vanished before build: `"$manifest`""
    exit 1
}

$cargoStdout = Join-Path ([System.IO.Path]::GetTempPath()) "hw2pkg-cargo-$PID.out"
$cargoStderr = Join-Path ([System.IO.Path]::GetTempPath()) "hw2pkg-cargo-$PID.err"
$cargoProcess = Start-Process `
    -FilePath $cargo.Source `
    -ArgumentList @("build", "--release", "--manifest-path", $manifest) `
    -WorkingDirectory $rustDir `
    -NoNewWindow `
    -Wait `
    -PassThru `
    -RedirectStandardOutput $cargoStdout `
    -RedirectStandardError $cargoStderr

if (Test-Path -LiteralPath $cargoStdout) {
    Get-Content -LiteralPath $cargoStdout | ForEach-Object { Write-BuildLog $_ }
    Remove-Item -LiteralPath $cargoStdout -Force -ErrorAction SilentlyContinue
}
if (Test-Path -LiteralPath $cargoStderr) {
    Get-Content -LiteralPath $cargoStderr | ForEach-Object { Write-BuildLog $_ }
    Remove-Item -LiteralPath $cargoStderr -Force -ErrorAction SilentlyContinue
}

$cargoExitCode = $cargoProcess.ExitCode
if ($cargoExitCode -ne 0) {
    exit $cargoExitCode
}

if (-not (Test-Path -LiteralPath $sourceExe)) {
    Write-BuildLog "[ERROR] Rust packager output missing: `"$sourceExe`""
    exit 1
}

New-Item -ItemType Directory -Force -Path $publishDir | Out-Null
Copy-Item -LiteralPath $sourceExe -Destination $publishExe -Force

if (-not (Test-Path -LiteralPath $publishExe)) {
    Write-BuildLog "[ERROR] Failed to publish Rust packager: `"$publishExe`""
    exit 1
}

Write-BuildLog "[INFO] Rust packager ready."
exit 0
