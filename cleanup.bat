@echo off
echo ========================================
echo Cleanup PM2.5 Project
echo ========================================
echo.
echo This will remove:
echo - Virtual environment (.venv)
echo - Python cache files (__pycache__)
echo - Temporary files
echo.
set /p confirm="Are you sure? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo Cleanup cancelled.
    pause
    exit /b 0
)

echo.
echo Cleaning up...

REM Remove virtual environment
if exist ".venv" (
    echo Removing virtual environment...
    rmdir /s /q .venv
    echo Virtual environment removed.
)

REM Remove Python cache
echo Removing Python cache files...
for /d /r %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc 2>nul

REM Remove .pytest_cache if exists
if exist ".pytest_cache" (
    rmdir /s /q .pytest_cache
)

echo.
echo ========================================
echo Cleanup completed!
echo ========================================
echo.
echo To reinstall, run: install.bat
echo.
pause
