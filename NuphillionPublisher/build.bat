@echo off
setlocal EnableExtensions

cd /d "%~dp0"

set "PY=C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\python.exe"
set "APP=Nuphillion Publisher"
set "ROOT=%~dp0build"
set "DIST=%~dp0dist"
set "LOG=%ROOT%\build.log"
set "ICON=%~dp0..\assets\iconNuph.ico"

if not exist "%ROOT%" mkdir "%ROOT%" >nul 2>nul
if not exist "%DIST%" mkdir "%DIST%" >nul 2>nul
type nul > "%LOG%"

echo [1/4] Checking Python
if not exist "%PY%" (
  echo [ERROR] Python not found: %PY%
  pause
  exit /b 1
)
"%PY%" --version >>"%LOG%" 2>&1
if errorlevel 1 goto :failed

echo [2/4] Checking dependencies
"%PY%" -c "import PyInstaller, flet" >>"%LOG%" 2>&1
if errorlevel 1 (
  "%PY%" -m pip install --user --disable-pip-version-check pyinstaller flet flet-desktop >>"%LOG%" 2>&1
  if errorlevel 1 goto :failed
)

echo [3/4] Building executable
set "ICON_ARG="
if exist "%ICON%" set "ICON_ARG=--icon=%ICON%"
"%PY%" -m PyInstaller --noconfirm --clean --windowed --name "%APP%" %ICON_ARG% --distpath "%DIST%" --workpath "%ROOT%\pyinstaller" --specpath "%ROOT%" "%~dp0main.py" >>"%LOG%" 2>&1
if errorlevel 1 goto :failed

echo [4/4] Done
echo [OK] Built: "%DIST%\%APP%.exe"
echo [OK] Log: "%LOG%"
pause
exit /b 0

:failed
echo [ERROR] Build failed.
echo.
powershell -NoProfile -Command "Get-Content -Path '%LOG%' -Tail 120" 2>nul
echo.
echo Full log: "%LOG%"
pause
exit /b 1
