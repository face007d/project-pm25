@echo off
echo ========================================
echo Git Push to GitHub
echo ========================================
echo.

REM Check git status
echo Checking git status...
git status

echo.
set /p message="Enter commit message: "

if "%message%"=="" (
    echo ERROR: Commit message cannot be empty!
    pause
    exit /b 1
)

echo.
echo Adding all changes...
git add .

echo.
echo Committing changes...
git commit -m "%message%"

echo.
echo Pushing to GitHub...
git push origin main

echo.
echo ========================================
echo Push completed!
echo ========================================
echo.
pause
