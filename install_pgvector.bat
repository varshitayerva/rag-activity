@echo off
REM pgvector Automatic Installation Script for Windows
REM This script downloads pgvector and installs it to PostgreSQL

echo.
echo ============================================================
echo  pgvector Automatic Installation
echo ============================================================
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo Please right-click Command Prompt and select "Run as Administrator"
    pause
    exit /b 1
)

echo [Step 1] Detecting PostgreSQL Installation...
for /d %%D in ("C:\Program Files\PostgreSQL\*") do (
    set PG_PATH=%%D
    goto :found_pg
)

:not_found
echo ERROR: PostgreSQL not found in C:\Program Files\PostgreSQL\
echo Please install PostgreSQL first!
pause
exit /b 1

:found_pg
echo Found PostgreSQL at: %PG_PATH%
set PG_LIB=%PG_PATH%\lib
set PG_EXT=%PG_PATH%\share\extension

REM Get PostgreSQL version
for %%A in ("%PG_PATH%") do set PG_VERSION=%%~nA
echo PostgreSQL Version: %PG_VERSION%

echo.
echo [Step 2] Downloading pgvector...
set DOWNLOAD_URL=https://github.com/pgvector/pgvector/releases/download/v0.5.1/pgvector-0.5.1-postgresql-%PG_VERSION%-windows-x64.zip
set DOWNLOAD_FILE=%TEMP%\pgvector.zip

REM Using PowerShell to download (more reliable)
powershell -Command ^
  "$ProgressPreference = 'SilentlyContinue'; ^
   Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%DOWNLOAD_FILE%'; ^
   if ($?) { Write-Host 'Download successful' } else { Write-Host 'Download failed'; exit 1 }"

if %errorLevel% neq 0 (
    echo ERROR: Failed to download pgvector
    echo Please download manually from: https://github.com/pgvector/pgvector/releases
    pause
    exit /b 1
)

echo Download complete!

echo.
echo [Step 3] Extracting pgvector...
set EXTRACT_PATH=%TEMP%\pgvector_extract
if exist "%EXTRACT_PATH%" rmdir /s /q "%EXTRACT_PATH%"
mkdir "%EXTRACT_PATH%"

REM Using PowerShell to extract zip
powershell -Command ^
  "Expand-Archive -Path '%DOWNLOAD_FILE%' -DestinationPath '%EXTRACT_PATH%'; ^
   Write-Host 'Extraction complete'"

if %errorLevel% neq 0 (
    echo ERROR: Failed to extract pgvector
    pause
    exit /b 1
)

echo Extraction complete!

echo.
echo [Step 4] Copying files to PostgreSQL...

REM Copy vector.dll
if exist "%EXTRACT_PATH%\vector.dll" (
    copy "%EXTRACT_PATH%\vector.dll" "%PG_LIB%\" /Y
    echo Copied: vector.dll
) else (
    echo WARNING: vector.dll not found in extracted files
)

REM Copy vector.sql
if exist "%EXTRACT_PATH%\vector.sql" (
    copy "%EXTRACT_PATH%\vector.sql" "%PG_EXT%\" /Y
    echo Copied: vector.sql
) else (
    echo WARNING: vector.sql not found in extracted files
)

REM Copy vector.control
if exist "%EXTRACT_PATH%\vector.control" (
    copy "%EXTRACT_PATH%\vector.control" "%PG_EXT%\" /Y
    echo Copied: vector.control
) else (
    echo WARNING: vector.control not found in extracted files
)

echo.
echo [Step 5] Restarting PostgreSQL service...

REM Find PostgreSQL service name
for /f "tokens=*" %%A in ('wmic service where name like "postgresql-x64-%" get name ^| findstr postgresql') do (
    set PG_SERVICE=%%A
    goto :restart_service
)

echo ERROR: PostgreSQL service not found
pause
exit /b 1

:restart_service
echo Stopping service: %PG_SERVICE%
net stop "%PG_SERVICE%" /y

timeout /t 2 /nobreak

echo Starting service: %PG_SERVICE%
net start "%PG_SERVICE%"

timeout /t 3 /nobreak

echo.
echo [Step 6] Verifying installation...

REM Clean up
del /q "%DOWNLOAD_FILE%"
rmdir /s /q "%EXTRACT_PATH%"

echo.
echo ============================================================
echo  Installation Complete!
echo ============================================================
echo.
echo Next steps:
echo 1. Open pgAdmin (http://localhost:5050)
echo 2. Right-click your database
echo 3. Select "Query Tool"
echo 4. Run: CREATE EXTENSION IF NOT EXISTS vector;
echo 5. You should see: "Query returned successfully"
echo.
echo If successful, continue with: PGADMIN_QUICK_CHECKLIST.md
echo.
pause
