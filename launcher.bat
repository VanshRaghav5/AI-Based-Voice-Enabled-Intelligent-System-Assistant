@echo off
REM ======================================================
REM OmniAssist AI - Debug Launcher (For Developers)
REM Shows detailed output and keeps console open
REM ======================================================

cd /d "%~dp0"
title OmniAssist AI - Debug Mode

cls
echo.
echo ===============================================
echo   OmniAssist AI - DEBUG MODE
echo ===============================================
echo.

REM Check Python venv
set "PYTHON_EXE="

if exist "venv\Scripts\python.exe" (
    set "PYTHON_EXE=venv\Scripts\python.exe"
) else if exist "backend\venv\Scripts\python.exe" (
    set "PYTHON_EXE=backend\venv\Scripts\python.exe"
)

if "%PYTHON_EXE%"=="" (
    echo [ERROR] Python venv not found!
    echo.
    echo Setup:
    echo   python -m venv backend\venv
    echo   .\backend\venv\Scripts\pip install -r backend\requirements.txt
    echo   .\backend\venv\Scripts\pip install -r desktop_1\requirements.txt
    echo.
    pause
    exit /b 1
)

REM Check Ollama
echo [1/3] Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [WARN] Ollama not running. Start it manually: ollama serve
) else (
    echo [OK] Ollama is running
)

REM Create logs folder
if not exist "logs" mkdir logs

REM Start backend
echo.
echo [2/3] Starting backend API...
echo Log: logs\backend.log
echo.
start "Backend API" /B cmd /c ".\%PYTHON_EXE% backend\api_service.py > logs\backend.log 2>&1"

REM Wait for backend
echo Waiting for backend to start...
timeout /t 10 /nobreak >nul

REM Check backend health
curl -s http://localhost:5000/api/health >nul 2>&1
if errorlevel 1 (
    echo [WARN] Backend may not be ready. Check logs\backend.log
) else (
    echo [OK] Backend is ready
)

REM Start frontend
echo.
echo [3/3] Starting desktop UI...
.\%PYTHON_EXE% desktop_1\main.py

echo.
echo ===============================================
echo   App stopped. Check logs/ for details.
echo ===============================================
pause
