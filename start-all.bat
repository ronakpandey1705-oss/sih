@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "PORT=8000"
set "HOST=0.0.0.0"
set "VENV_DIR="

if exist "%~dp0backend\.venv\Scripts\python.exe" set "VENV_DIR=%~dp0backend\.venv"
if not defined VENV_DIR if exist "%~dp0.venv\Scripts\python.exe" set "VENV_DIR=%~dp0.venv"
if not defined VENV_DIR if exist "%~dp0venv\Scripts\python.exe" set "VENV_DIR=%~dp0venv"
if not defined VENV_DIR if exist "%~dp0backend\venv\Scripts\python.exe" set "VENV_DIR=%~dp0backend\venv"

if not defined VENV_DIR (
  echo [PackSure] No virtual environment found. Creating backend\.venv ...
  set "PY_CMD="
  where py >nul 2>&1
  if not errorlevel 1 set "PY_CMD=py -3"
  if not defined PY_CMD (
    where python >nul 2>&1
    if not errorlevel 1 set "PY_CMD=python"
  )
  if not defined PY_CMD (
    echo [PackSure] Python was not found. Install Python 3 and try again.
    pause
    exit /b 1
  )
  !PY_CMD! -m venv "%~dp0backend\.venv"
  if errorlevel 1 (
    echo [PackSure] Failed to create the virtual environment.
    pause
    exit /b 1
  )
  set "VENV_DIR=%~dp0backend\.venv"
)

echo [PackSure] Using venv: !VENV_DIR!
call "!VENV_DIR!\Scripts\activate.bat"
if errorlevel 1 (
  echo [PackSure] Failed to activate the virtual environment.
  pause
  exit /b 1
)

cd /d "%~dp0backend"

"!VENV_DIR!\Scripts\python.exe" -c "import uvicorn" >nul 2>&1
if errorlevel 1 (
  echo [PackSure] Installing backend dependencies...
  "!VENV_DIR!\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo [PackSure] pip install failed.
    pause
    exit /b 1
  )
)

echo.
echo [PackSure] Starting API + frontend at http://localhost:%PORT%
echo [PackSure] API docs: http://localhost:%PORT%/docs
echo [PackSure] Press Ctrl+C to stop.
echo.

start "" "http://localhost:%PORT%"
"!VENV_DIR!\Scripts\python.exe" -m uvicorn app.main:app --reload --host %HOST% --port %PORT%

endlocal
