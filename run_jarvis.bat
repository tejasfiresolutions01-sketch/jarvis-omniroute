@echo off
title J.A.R.V.I.S. // STARK INDUSTRIES TACTICAL HUD
color 0b
echo ========================================================
echo   Initializing J.A.R.V.I.S. Butler & Autonomy Matrix...
echo ========================================================
cd /d "%~dp0"

:: ── OmniRoute Local Gateway Autostart ──────────────────────────────────────
echo [OmniRoute] Checking local AI router status...
curl -s --max-time 1 http://localhost:20128/v1/models -H "Authorization: Bearer %OMNIROUTE_API_KEY%" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [OmniRoute] Launching local AI router daemon on port 20128...
    set "PATH=%APPDATA%\npm;C:\Program Files\nodejs;%PATH%"
    start /B "" "%APPDATA%\npm\omniroute.cmd" serve --port 20128 --daemon --no-open --no-tray >nul 2>&1
) else (
    echo [OmniRoute] Local AI router is active on port 20128.
)
echo.

:: ── Launch J.A.R.V.I.S. Core ────────────────────────────────────────────────
if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" (
    "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" main.py %*
) else (
    python main.py %*
)
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [Notice]: J.A.R.V.I.S. session closed.
    pause
)
