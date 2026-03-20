@echo off
echo ========================================
echo Testing Database Connection
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
echo Testing Supabase connection...
echo.

REM Run the test script
python test_database.py

echo.
pause
