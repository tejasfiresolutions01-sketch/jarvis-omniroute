@echo off
title J.A.R.V.I.S. // STARK INDUSTRIES TACTICAL HUD
color 0b
echo ========================================================
echo   Initializing J.A.R.V.I.S. Butler ^& Autonomy Matrix...
echo ========================================================
cd /d "%~dp0"

set "PATH=C:\Program Files\nodejs;%APPDATA%\npm;%PATH%"
set "PYTHONUNBUFFERED=1"

REM Check OmniRoute local router status
curl -s --max-time 1 http://localhost:20128/v1/models >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [OmniRoute] Starting local AI gateway in background...
    start /min "OmniRoute Gateway" cmd /c omniroute serve
) else (
    echo [OmniRoute] Local AI router is active on port 20128.
)
echo.

REM Launch J.A.R.V.I.S. Core Tactical HUD
echo [J.A.R.V.I.S.] Deploying Holographic Tactical Interface...
if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" (
    "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" -u main.py %*
) else (
    python -u main.py %*
)
echo.
echo [Notice]: J.A.R.V.I.S. session closed.
pause
