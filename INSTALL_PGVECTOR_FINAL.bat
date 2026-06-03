@echo off
REM pgvector installation for PostgreSQL 16 - Simple version
REM Run as Administrator

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
    echo Install PostgreSQL 16 first
    pause
    exit /b 1
)

echo [OK] PostgreSQL 16 found
echo.

REM Set paths
set PG_LIB=C:\Program Files\PostgreSQL\16\lib
set PG_EXT=C:\Program Files\PostgreSQL\16\share\extension
set TEMP_DIR=%TEMP%\pgvector_install
set ZIP_FILE=%TEMP_DIR%\pgvector.zip

echo [Step 1] Creating temporary directory...
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%" 2>nul
mkdir "%TEMP_DIR%" 2>nul

echo.
echo [Step 2] Downloading pgvector using VBScript...

REM Create VBScript to download file
set VBS_FILE=%TEMP_DIR%\download.vbs
(
    echo Set objXMLHTTP = CreateObject("MSXML2.XMLHTTP"^)
    echo objXMLHTTP.Open "GET", "https://github.com/pgvector/pgvector/releases/download/v0.4.4/pgvector-0.4.4-postgresql-16-windows-x64.zip", False
    echo objXMLHTTP.Send
    echo if objXMLHTTP.Status = 200 then
    echo     Set objADOStream = CreateObject("ADODB.Stream"^)
    echo     objADOStream.Type = 1
    echo     objADOStream.Open
    echo     objADOStream.Write objXMLHTTP.ResponseBody
    echo     objADOStream.Position = 0
    echo     objADOStream.SaveToFile "%ZIP_FILE%", 2
    echo     objADOStream.Close
    echo     WScript.Echo "Download successful"
    echo else
    echo     WScript.Echo "Download failed: " ^& objXMLHTTP.Status
    echo end if
) > "%VBS_FILE%"

REM Run VBScript
cscript.exe "%VBS_FILE%" 2>nul

if not exist "%ZIP_FILE%" (
    echo ERROR: Download failed!
    echo.
    echo Please download manually:
    echo 1. Go to: https://github.com/pgvector/pgvector/releases
    echo 2. Download: pgvector-0.4.4-postgresql-16-windows-x64.zip
    echo 3. Extract to: %TEMP_DIR%
    echo 4. Run this script again
    echo.
    pause
    exit /b 1
)

echo Download successful!
echo.

echo [Step 3] Extracting files...

REM Create PowerShell script to extract zip
set PS_FILE=%TEMP_DIR%\extract.ps1
(
    echo Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%TEMP_DIR%' -Force
    echo Write-Host "Extraction complete"
) > "%PS_FILE%"

REM Run PowerShell to extract
powershell -ExecutionPolicy Bypass -File "%PS_FILE%" 2>nul

if not exist "%TEMP_DIR%\vector.dll" (
    echo ERROR: Extraction failed or files not found!
    pause
    exit /b 1
)

echo Extraction successful!
echo.

echo [Step 4] Copying files to PostgreSQL 16...

copy "%TEMP_DIR%\vector.dll" "%PG_LIB%\" /Y >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Could not copy vector.dll
    echo Check permissions and try running as Administrator
    pause
    exit /b 1
)
echo Copied: vector.dll

copy "%TEMP_DIR%\vector.sql" "%PG_EXT%\" /Y >nul 2>&1
echo Copied: vector.sql

copy "%TEMP_DIR%\vector.control" "%PG_EXT%\" /Y >nul 2>&1
echo Copied: vector.control

echo.
echo [Step 5] Restarting PostgreSQL...

echo Stopping service...
net stop postgresql-x64-16 /y >nul 2>&1
timeout /t 2 /nobreak >nul

echo Starting service...
net start postgresql-x64-16 >nul 2>&1
timeout /t 3 /nobreak >nul

echo PostgreSQL restarted!
echo.

echo [Step 6] Cleaning up...
rmdir /s /q "%TEMP_DIR%" >nul 2>&1

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
if errorLevel 1 (
    echo Note: If you see an error about the extension, you may need to:
    echo - Verify files are in: C:\Program Files\PostgreSQL\16\lib\
    echo - Restart PostgreSQL manually via Services
    echo - Try the CREATE EXTENSION command again
)
echo.
pause
