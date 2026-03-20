@echo off
echo ========================================
echo Installing PM2.5 Project Dependencies
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11 from https://www.python.org/
    pause
    exit /b 1
)

echo Python found!
echo.

REM Create virtual environment if not exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    echo Virtual environment created!
) else (
    echo Virtual environment already exists.
)
echo.

REM Activate virtual environment and install dependencies
echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Installing dependencies from requirements.txt...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ========================================
echo Installation completed successfully!
echo ========================================
echo.
echo To run the server, use: run_server.bat
echo.
pause
