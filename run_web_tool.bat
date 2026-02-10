@echo off
REM Ensure we are in the script's directory
cd /d "%~dp0"

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found. Please run installation steps first.
    pause
    exit /b
)

REM Activate venv and run script
call venv\Scripts\activate.bat
start "" pythonw web_tool_win.py
exit
