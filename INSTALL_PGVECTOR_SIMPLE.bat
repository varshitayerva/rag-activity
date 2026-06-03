@echo off
REM Simple pgvector installation for PostgreSQL 16
REM Run as Administrator

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo  pgvector Installation for PostgreSQL 16
echo ============================================================
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Must run as Administrator!
    echo Right-click this file and select "Run as Administrator"
    pause
    exit /b 1
)

REM Check PostgreSQL 16 exists
if not exist "C:\Program Files\PostgreSQL\16\lib" (
    echo ERROR: PostgreSQL 16 not found!
    echo Install PostgreSQL 16 first from: https://www.postgresql.org/download/windows/
    pause
    exit /b 1
)

echo [OK] PostgreSQL 16 found
echo.

REM Set paths
set PG_LIB=C:\Program Files\PostgreSQL\16\lib
set PG_EXT=C:\Program Files\PostgreSQL\16\share\extension
set TEMP_DIR=%TEMP%\pgvector_install
set DOWNLOAD_URL=https://github.com/pgvector/pgvector/releases/download/v0.4.4/pgvector-0.4.4-postgresql-16-windows-x64.zip
set ZIP_FILE=%TEMP_DIR%\pgvector.zip

echo [Step 1] Creating temporary directory...
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"
mkdir "%TEMP_DIR%"

echo [Step 2] Downloading pgvector...
echo Downloading from: %DOWNLOAD_URL%

REM Use PowerShell to download
powershell -Command "^
  $ProgressPreference = 'SilentlyContinue'; ^
  try { ^
    Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%ZIP_FILE%'; ^
    Write-Host 'Download successful!'; ^
  } catch { ^
    Write-Host 'Download failed!'; ^
    Write-Host $_.Exception.Message; ^
    exit 1; ^
  } ^
"

if %errorLevel% neq 0 (
    echo ERROR: Download failed!
    echo Make sure you have internet connection
    pause
    exit /b 1
)

echo [Step 3] Extracting files...
REM Use PowerShell to extract
powershell -Command "^
  try { ^
    Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%TEMP_DIR%' -Force; ^
    Write-Host 'Extraction successful!'; ^
  } catch { ^
    Write-Host 'Extraction failed!'; ^
    exit 1; ^
  } ^
"

if %errorLevel% neq 0 (
    echo ERROR: Extraction failed!
    pause
    exit /b 1
)

echo [Step 4] Copying files to PostgreSQL...

REM Find the extracted files (they might be in a subdirectory)
set FOUND=0
for /r "%TEMP_DIR%" %%F in (vector.dll) do (
    echo Copying vector.dll...
    copy "%%F" "%PG_LIB%\" /Y
    set FOUND=1
)

if %FOUND%==0 (
    echo ERROR: vector.dll not found in extracted files!
    pause
    exit /b 1
)

for /r "%TEMP_DIR%" %%F in (vector.sql) do (
    echo Copying vector.sql...
    copy "%%F" "%PG_EXT%\" /Y
)

for /r "%TEMP_DIR%" %%F in (vector.control) do (
    echo Copying vector.control...
    copy "%%F" "%PG_EXT%\" /Y
)

echo.
echo [Step 5] Restarting PostgreSQL service...
echo Stopping PostgreSQL...
net stop postgresql-x64-16 /y >nul 2>&1
timeout /t 2 /nobreak

echo Starting PostgreSQL...
net start postgresql-x64-16 >nul 2>&1
timeout /t 3 /nobreak

if %errorLevel% neq 0 (
    echo WARNING: Could not restart service automatically
    echo Please restart PostgreSQL manually:
    echo   - Open Services (services.msc)
    echo   - Find "postgresql-x64-16"
    echo   - Right-click and select "Restart"
)

echo.
echo [Step 6] Cleaning up...
rmdir /s /q "%TEMP_DIR%"

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
echo 5. Should see: "Query returned successfully"
echo.
echo If successful, continue with PGADMIN_QUICK_CHECKLIST.md
echo.
pause
