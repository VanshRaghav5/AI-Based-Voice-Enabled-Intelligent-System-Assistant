@echo off
setlocal EnableExtensions

cd /d "%~dp0"

echo [OMINI] Starting launcher...

set "PYTHON_CMD="

if exist "venv\Scripts\python.exe" (
    set "PYTHON_CMD=venv\Scripts\python.exe"
) else (
    where py >nul 2>&1
    if %errorlevel%==0 (
        set "PYTHON_CMD=py -3"
    ) else (
        where python >nul 2>&1
        if %errorlevel%==0 (
            set "PYTHON_CMD=python"
        )
    )
)

if not defined PYTHON_CMD (
    echo [OMINI] Python not found.
    echo Install Python 3 and try again.
    pause
    exit /b 1
)

REM Install requirements if not already installed
echo [OMINI] Checking dependencies...
%PYTHON_CMD% -c "import sounddevice" 2>nul
if %errorlevel% neq 0 (
    echo [OMINI] Installing requirements...
    %PYTHON_CMD% -m pip install -r requirements.txt --quiet --no-warn-script-location --disable-pip-version-check
    REM Continue even if pip reports warnings
)

REM Check if main.py exists
if not exist "main.py" (
    echo [OMINI] main.py not found in this folder.
    pause
    exit /b 1
)

if not exist "config\api_keys.json" (
    echo [OMINI] Warning: config\api_keys.json not found.
    echo The app will ask for setup on first run.
)

echo [OMINI] Running main.py...
%PYTHON_CMD% main.py
set "EXIT_CODE=%errorlevel%"

if not "%EXIT_CODE%"=="0" (
    echo [OMINI] Exited with code %EXIT_CODE%.
    pause
)

exit /b %EXIT_CODE%
