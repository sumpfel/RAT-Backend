@echo off
REM ============================================================================
REM  RAT-Backend launcher (Windows, cmd)
REM    - creates a Python virtual environment (.venv) if missing
REM    - installs/updates dependencies from src\requirements.txt
REM    - starts the FastAPI server with uvicorn
REM
REM  Usage:
REM    run.bat                       ->  http://127.0.0.1:8000
REM    set HOST=0.0.0.0 & set PORT=8080 & run.bat
REM    set RELOAD=1 & run.bat        ->  auto-reload (development)
REM ============================================================================
setlocal

REM always run relative to this script's folder
cd /d "%~dp0"

set "VENV_DIR=.venv"
set "REQ=src\requirements.txt"
if "%HOST%"=="" set "HOST=127.0.0.1"
if "%PORT%"=="" set "PORT=8000"

REM pick a python launcher: prefer the py launcher, fall back to python
where py >nul 2>nul && (set "PY=py -3") || (set "PY=python")
%PY% --version >nul 2>nul || (
    echo ERROR: Python 3 is not installed or not on PATH.
    exit /b 1
)

REM 1) virtual environment
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo ^>^> Creating virtual environment in %VENV_DIR% ...
    %PY% -m venv "%VENV_DIR%" || exit /b 1
)

REM 2) dependencies
echo ^>^> Installing dependencies from %REQ% ...
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip >nul
"%VENV_DIR%\Scripts\python.exe" -m pip install -r "%REQ%" || exit /b 1

REM 3) run
set "RELOAD_FLAG="
if "%RELOAD%"=="1" set "RELOAD_FLAG=--reload"

echo ^>^> Starting RAT-Backend on http://%HOST%:%PORT%  (Swagger UI at /docs)
cd src
"..\%VENV_DIR%\Scripts\python.exe" -m uvicorn main:app --host %HOST% --port %PORT% %RELOAD_FLAG%

endlocal
