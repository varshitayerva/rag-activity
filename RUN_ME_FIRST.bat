@echo off
REM Simple batch script to run pgvector installation
REM Right-click this file and select "Run as Administrator"

echo.
echo ============================================================
echo  pgvector Installation Helper
echo ============================================================
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo.
    echo Please right-click this file and select:
    echo "Run as Administrator"
    echo.
    pause
    exit /b 1
)

echo Launching PowerShell with pgvector installation...
echo.

REM Launch PowerShell and run the installation script
cd /d "%~dp0"
powershell -Command "Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process; .\install_pgvector.ps1"

pause
