@echo off
echo ========================================
echo Running Daily PM2.5 Data Update
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
call .venv\Scripts\activate.bat

echo.
echo Fetching latest PM2.5 data from WAQI API...
echo.

REM Run the daily update script
python scripts/daily_update.py

echo.
echo ========================================
echo Update completed!
echo ========================================
echo.
pause
