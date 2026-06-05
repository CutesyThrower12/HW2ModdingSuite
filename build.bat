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
set "DEPS_STAMP=%ROOT%\deps.ok"
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
set "CHECK_DEPS=1"
if exist "%DEPS_STAMP%" (
  if not "%HW2_FORCE_DEPS%"=="1" (
    "%PY%" -c "import PyInstaller, flet, flet_video, flet_desktop, PySide6" >>"%LOG%" 2>&1
    if errorlevel 1 (
      echo [WARN] Cached dependency stamp is stale; reinstalling dependencies. >>"%LOG%"
      del "%DEPS_STAMP%" >nul 2>nul
    ) else (
      call :progress 3 "Dependencies cached" 0
      set "CHECK_DEPS=0"
    )
  )
)
if "%CHECK_DEPS%"=="1" (
  "%PY%" -c "import PyInstaller, flet, flet_video, flet_desktop, PySide6" >>"%LOG%" 2>&1
  if errorlevel 1 (
    call :progress 3 "Installing missing dependencies" 0
    "%PY%" -m pip install --user --disable-pip-version-check pyinstaller flet flet-video flet-desktop PySide6 >>"%LOG%" 2>&1
    if errorlevel 1 goto :pip_failed
    "%PY%" -c "import PyInstaller, flet, flet_video, flet_desktop, PySide6" >>"%LOG%" 2>&1
    if errorlevel 1 goto :pip_failed
  )
  type nul > "%DEPS_STAMP%"
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
set "PLAYER_COLORS_EDITOR=%SRC%\player_colors_pyside.py"
set "RUST_PACKAGER_SRC=%PROJ%src-rust\HW2Packager"
set "RUST_PACKAGER_EXE=%TOOLS_DIR%\HW2Packager\hw2pkg.exe"

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
if not exist "%PLAYER_COLORS_EDITOR%" (
  echo [ERROR] Missing: %PLAYER_COLORS_EDITOR%
  pause
  exit /b 1
)
if not exist "%RUST_PACKAGER_SRC%\Cargo.toml" (
  echo [ERROR] Missing: %RUST_PACKAGER_SRC%\Cargo.toml
  pause
  exit /b 1
)
if not exist "%BUILD_PROGRESS%" (
  echo [ERROR] Missing: %BUILD_PROGRESS%
  pause
  exit /b 1
)

call :progress 5 "Building fast PKG packager" 0
where cargo >nul 2>nul
if errorlevel 1 (
  if not exist "%RUST_PACKAGER_EXE%" (
    echo [ERROR] Cargo is not installed and no existing fast packager was found:
    echo   %RUST_PACKAGER_EXE%
    pause
    exit /b 1
  )
  echo [WARN] Cargo not found; using existing fast packager.
) else (
  pushd "%RUST_PACKAGER_SRC%"
  cargo build --release >>"%LOG%" 2>&1
  if errorlevel 1 (
    popd
    goto :rust_failed
  )
  popd
  if not exist "%TOOLS_DIR%\HW2Packager" mkdir "%TOOLS_DIR%\HW2Packager" >nul 2>nul
  copy /y "%RUST_PACKAGER_SRC%\target\release\hw2pkg.exe" "%RUST_PACKAGER_EXE%" >>"%LOG%" 2>&1
  if errorlevel 1 goto :rust_failed
)

call :progress 6 "Building executable" 1
if defined MP4 (
  set "INCLUDE_INTRO=-IncludeIntro"
) else (
  set "INCLUDE_INTRO="
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%BUILD_PROGRESS%" -Python "%PY%" -Project "%PROJ_ARG%" -BuildRoot "%ROOT%" %INCLUDE_INTRO%
if errorlevel 1 goto :build_failed

call :progress 7 "Publishing final exe" 0
robocopy "%DIST_DIR%" "%OUTPUT_DIR%" "Halo Wars 2 Modding Suite.exe" /XO /NFL /NDL /NJH /NJS /NP >>"%LOG%" 2>&1
if %ERRORLEVEL% LEQ 3 (
  verify >nul
) else (
  goto :copy_failed
)
if errorlevel 1 goto :copy_failed

call :progress 8 "Done" 0
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
if "%~1"=="7" set "BAR=[############################....]"
if "%~1"=="8" set "BAR=[##############################]"
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

:rust_failed
echo [ERROR] Fast PKG packager build failed.
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
