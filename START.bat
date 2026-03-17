@echo off
REM ======================================================
REM OmniAssist AI - Simple One-Click Start
REM ======================================================

cd /d "%~dp0"
title OmniAssist AI

cls
echo.
echo ===============================================
echo   OmniAssist AI - Starting...
echo ===============================================
echo.

REM Detect venv location
set "PYTHON_EXE="

if exist "venv\Scripts\python.exe" (
    set "PYTHON_EXE=venv\Scripts\python.exe"
) else if exist "backend\venv\Scripts\python.exe" (
    set "PYTHON_EXE=backend\venv\Scripts\python.exe"
)

if "%PYTHON_EXE%"=="" (
    echo ERROR: Python venv not found!
    echo.
    echo Run this first:
    echo   python -m venv backend\venv
    echo   .\backend\venv\Scripts\pip install -r backend\requirements.txt
    echo   .\backend\venv\Scripts\pip install -r desktop_1\requirements.txt
    echo.
    pause
    exit /b 1
)

REM Create logs folder if needed
if not exist "logs" mkdir logs

REM Check required security env vars (dev-friendly: warn only)
if "%OMNIASSIST_FLASK_SECRET_KEY%"=="" (
    echo [WARN] OMNIASSIST_FLASK_SECRET_KEY is not set.
    echo        Backend will generate an ephemeral dev secret.
    echo        For persistence, copy .env.example to .env and fill values.
    echo.
)

if "%OMNIASSIST_JWT_SECRET%"=="" (
    echo [WARN] OMNIASSIST_JWT_SECRET is not set.
    echo        Backend will generate an ephemeral dev secret; sessions reset on restart.
    echo        For persistence, copy .env.example to .env and fill values.
    echo.
)

REM Start backend in background (cmd /c so stdout/stderr are captured in the log)
echo Starting backend...
start "Backend" /B cmd /c ".\%PYTHON_EXE% backend\api_service.py > logs\backend.log 2>&1"

REM Wait for backend to initialise (Whisper model load ~4 s, plus small margin)
echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

REM Quick check if backend crashed early (e.g. missing modules)
findstr /i /c:"ModuleNotFoundError" "logs\backend.log" >nul
if %errorlevel%==0 (
    echo.
    echo ==============================================================
    echo ERROR: Backend failed to start due to missing Python modules!
    echo Please install requirements by running:
    echo   .\%PYTHON_EXE% -m pip install -r backend\requirements.txt
    echo   .\%PYTHON_EXE% -m pip install -r desktop_1\requirements.txt
    echo ==============================================================
    echo.
    echo Press any key to view the backend error log...
    pause >nul
    type "logs\backend.log"
    echo.
    pause
    exit /b 1
)

REM Start frontend
echo Starting desktop app...
start "OmniAssist" .\%PYTHON_EXE% desktop_1\main.py

echo.
echo ===============================================
echo   App started! Close this window when done.
echo ===============================================
echo.
pause
