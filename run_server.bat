@echo off
echo ========================================
echo Starting PM2.5 Web Server
echo ========================================
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo ERROR: Virtual environment not found!
    echo Please run install.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Check if .env file exists
if not exist ".env" (
    echo WARNING: .env file not found!
    echo Please create .env file with your configuration.
    echo You can copy from .env.example
    echo.
    pause
)

echo.
echo Starting Flask server...
echo Server will be available at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
echo ========================================
echo.

REM Run the Flask server
python backend/server.py

pause
