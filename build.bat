@echo off
setlocal EnableExtensions

cd /d "%~dp0"

REM --- Path to Python (user-specified) ---
set "PY=C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\python.exe"

REM --- Organized project paths ---
set "SRC=%~dp0src"
set "ASSETS=%~dp0assets"
set "SCRIPTS=%~dp0scripts"
set "OUTPUT_DIR=%~dp0dist"
set "ROOT=%~dp0build\pyinstaller"
set "DIST_DIR=%ROOT%\dist"
set "LOG=%ROOT%\build.log"
set "BUILD_PROGRESS=%SCRIPTS%\build_progress.ps1"

if not exist "%ROOT%" mkdir "%ROOT%" >nul 2>nul
if not exist "%DIST_DIR%" mkdir "%DIST_DIR%" >nul 2>nul
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%" >nul 2>nul
type nul > "%LOG%"

call :progress 1 "Checking Python" 0
if not exist "%PY%" (
  echo [ERROR] Python not found at:
  echo   %PY%
  echo Edit build.bat and fix the PY path.
  pause
  exit /b 1
)
"%PY%" --version >>"%LOG%" 2>&1
if errorlevel 1 goto :python_failed

call :progress 2 "Checking dependencies" 0
"%PY%" -c "import PyInstaller, flet, flet_video, flet_desktop, PySide6" >>"%LOG%" 2>&1
if errorlevel 1 (
  call :progress 3 "Installing missing dependencies" 0
  "%PY%" -m pip install --user pyinstaller flet flet-video flet-desktop PySide6 >>"%LOG%" 2>&1
  if errorlevel 1 goto :pip_failed
) else (
  call :progress 3 "Dependencies ready" 0
)

call :progress 4 "Validating assets" 0
set "PROJ=%~dp0"
set "PROJ_ARG=%PROJ:~0,-1%"
set "BG=%ASSETS%\background.png"
set "MP4=%ASSETS%\intro.mp4"
set "ICON=%ASSETS%\icon.ico"
set "LIB=%SRC%\Modules\Library"
set "TOOLS_DIR=%PROJ%tools"
set "MODULES_DIR=%SRC%\Modules"
set "PFX_EDITOR=%SRC%\pfx_editor_pyside.py"

if not exist "%BG%" (
  echo [ERROR] Missing: %BG%
  pause
  exit /b 1
)
if not exist "%ICON%" (
  echo [ERROR] Missing: %ICON%
  pause
  exit /b 1
)
if not exist "%MP4%" (
  echo [WARN] Missing: %MP4%
  echo [WARN] Continuing without intro.mp4.
  set "MP4="
)
if not exist "%LIB%" (
  echo [ERROR] Missing: %LIB%
  pause
  exit /b 1
)
if not exist "%TOOLS_DIR%" (
  echo [WARN] Tools directory not found: %TOOLS_DIR%
  echo [WARN] Some tools may be unavailable in the packaged exe.
)
if not exist "%PFX_EDITOR%" (
  echo [ERROR] Missing: %PFX_EDITOR%
  pause
  exit /b 1
)
if not exist "%BUILD_PROGRESS%" (
  echo [ERROR] Missing: %BUILD_PROGRESS%
  pause
  exit /b 1
)

call :progress 5 "Building executable" 1
if defined MP4 (
  set "INCLUDE_INTRO=-IncludeIntro"
) else (
  set "INCLUDE_INTRO="
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%BUILD_PROGRESS%" -Python "%PY%" -Project "%PROJ_ARG%" -BuildRoot "%ROOT%" %INCLUDE_INTRO%
if errorlevel 1 goto :build_failed

call :progress 6 "Copying final exe" 0
copy /y "%DIST_DIR%\Halo Wars 2 Modding Suite.exe" "%OUTPUT_DIR%\Halo Wars 2 Modding Suite.exe" >>"%LOG%" 2>&1
if errorlevel 1 goto :copy_failed

call :progress 7 "Done" 0
echo.
echo [OK] Built: "%OUTPUT_DIR%\Halo Wars 2 Modding Suite.exe"
echo [OK] Build cache kept for faster future builds: "%ROOT%"
echo [OK] Full log: "%LOG%"
pause
exit /b 0

:progress
set "BAR=[                              ]"
if "%~1"=="1" set "BAR=[####..........................]"
if "%~1"=="2" set "BAR=[########......................]"
if "%~1"=="3" set "BAR=[############..................]"
if "%~1"=="4" set "BAR=[################..............]"
if "%~1"=="5" set "BAR=[####################..........]"
if "%~1"=="6" set "BAR=[##########################....]"
if "%~1"=="7" set "BAR=[##############################]"
if "%~3"=="1" (
  echo %BAR% %~2
) else (
  echo %BAR% %~2
)
exit /b 0

:python_failed
echo [ERROR] Python failed to run.
goto :show_log

:pip_failed
echo [ERROR] Dependency installation failed.
goto :show_log

:build_failed
echo [ERROR] Build failed.
goto :show_log

:copy_failed
echo [ERROR] Failed to copy final executable.
goto :show_log

:show_log
echo.
echo Last build log lines:
powershell -NoProfile -Command "Get-Content -Path '%LOG%' -Tail 140" 2>nul
if errorlevel 1 type "%LOG%"
echo.
echo Full log:
echo   %LOG%
pause
exit /b 1
