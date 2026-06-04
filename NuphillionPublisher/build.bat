@echo off
setlocal EnableExtensions

cd /d "%~dp0"

set "PY=C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\python.exe"
set "APP=Nuphillion Publisher"
set "ROOT=%~dp0build"
set "DIST=%~dp0dist"
set "BUILD_DIST=%ROOT%\dist"
set "LOG=%ROOT%\build.log"
set "ICON=%~dp0..\assets\iconNuph.ico"

if not exist "%ROOT%" mkdir "%ROOT%" >nul 2>nul
if not exist "%DIST%" mkdir "%DIST%" >nul 2>nul
if not exist "%BUILD_DIST%" mkdir "%BUILD_DIST%" >nul 2>nul
type nul > "%LOG%"

echo [1/5] Checking Python
if not exist "%PY%" (
  echo [ERROR] Python not found: %PY%
  pause
  exit /b 1
)
"%PY%" --version >>"%LOG%" 2>&1
if errorlevel 1 goto :failed

echo [2/5] Checking dependencies
"%PY%" -c "import PyInstaller, flet" >>"%LOG%" 2>&1
if errorlevel 1 (
  "%PY%" -m pip install --user --disable-pip-version-check pyinstaller flet flet-desktop >>"%LOG%" 2>&1
  if errorlevel 1 goto :failed
)

echo [3/5] Closing old Publisher if it is running
taskkill /IM "%APP%.exe" /F >>"%LOG%" 2>&1
timeout /t 1 /nobreak >nul

echo [4/5] Building executable
set "ICON_ARG="
if exist "%ICON%" set "ICON_ARG=--icon=%ICON%"
"%PY%" -m PyInstaller --noconfirm --clean --windowed --name "%APP%" %ICON_ARG% --distpath "%BUILD_DIST%" --workpath "%ROOT%\pyinstaller" --specpath "%ROOT%" "%~dp0main.py" >>"%LOG%" 2>&1
if errorlevel 1 goto :failed

echo [5/5] Publishing final build
if exist "%DIST%\%APP%" rmdir /s /q "%DIST%\%APP%" >>"%LOG%" 2>&1
if exist "%DIST%\%APP%.exe" del /f /q "%DIST%\%APP%.exe" >>"%LOG%" 2>&1
robocopy "%BUILD_DIST%" "%DIST%" /MIR /NFL /NDL /NJH /NJS /NP >>"%LOG%" 2>&1
if %ERRORLEVEL% GTR 3 goto :failed

echo [OK] Built: "%DIST%\%APP%\%APP%.exe"
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
