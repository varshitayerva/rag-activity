# pgvector Automatic Installation Script (PowerShell)
# Run as Administrator: Right-click PowerShell → Run as Administrator
# Then: Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
# Then: .\install_pgvector.ps1

param(
    [string]$PgVersion = $null
)

Write-Host "========================================================" -ForegroundColor Green
Write-Host "  pgvector Automatic Installation (PowerShell)" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Please right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Step 1: Detect PostgreSQL Installation
Write-Host "[Step 1] Detecting PostgreSQL Installation..." -ForegroundColor Cyan

$pgPaths = Get-ChildItem "C:\Program Files\PostgreSQL\" -Directory -ErrorAction SilentlyContinue
if (-not $pgPaths) {
    Write-Host "ERROR: PostgreSQL not found in C:\Program Files\PostgreSQL\" -ForegroundColor Red
    Write-Host "Please install PostgreSQL first!" -ForegroundColor Yellow
    exit 1
}

# If multiple versions, use the latest
$pgPath = ($pgPaths | Sort-Object Name -Descending | Select-Object -First 1).FullName
$pgVersion = Split-Path -Leaf $pgPath
Write-Host "Found PostgreSQL at: $pgPath" -ForegroundColor Green
Write-Host "PostgreSQL Version: $pgVersion" -ForegroundColor Green

$pgLib = Join-Path $pgPath "lib"
$pgExt = Join-Path $pgPath "share\extension"

# Step 2: Download pgvector
Write-Host ""
Write-Host "[Step 2] Downloading pgvector..." -ForegroundColor Cyan

$downloadUrl = "https://github.com/pgvector/pgvector/releases/download/v0.5.1/pgvector-0.5.1-postgresql-$pgVersion-windows-x64.zip"
$downloadFile = Join-Path $env:TEMP "pgvector.zip"

try {
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $downloadUrl -OutFile $downloadFile -UseBasicParsing
    Write-Host "Download successful!" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to download pgvector" -ForegroundColor Red
    Write-Host "URL: $downloadUrl" -ForegroundColor Yellow
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host "Please download manually from: https://github.com/pgvector/pgvector/releases" -ForegroundColor Yellow
    exit 1
}

# Step 3: Extract pgvector
Write-Host ""
Write-Host "[Step 3] Extracting pgvector..." -ForegroundColor Cyan

$extractPath = Join-Path $env:TEMP "pgvector_extract"
if (Test-Path $extractPath) {
    Remove-Item $extractPath -Recurse -Force
}
New-Item -ItemType Directory -Path $extractPath | Out-Null

try {
    Expand-Archive -Path $downloadFile -DestinationPath $extractPath -Force
    Write-Host "Extraction successful!" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to extract pgvector" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# Step 4: Copy files to PostgreSQL
Write-Host ""
Write-Host "[Step 4] Copying files to PostgreSQL..." -ForegroundColor Cyan

$filesToCopy = @(
    @{ src = "vector.dll"; dest = $pgLib },
    @{ src = "vector.sql"; dest = $pgExt },
    @{ src = "vector.control"; dest = $pgExt }
)

foreach ($file in $filesToCopy) {
    $srcPath = Join-Path $extractPath $file.src
    if (Test-Path $srcPath) {
        Copy-Item -Path $srcPath -Destination $file.dest -Force
        Write-Host "Copied: $($file.src)" -ForegroundColor Green
    } else {
        Write-Host "WARNING: $($file.src) not found in extracted files" -ForegroundColor Yellow
    }
}

# Step 5: Restart PostgreSQL Service
Write-Host ""
Write-Host "[Step 5] Restarting PostgreSQL service..." -ForegroundColor Cyan

# Find PostgreSQL service
$pgService = Get-Service | Where-Object { $_.Name -like "postgresql-x64-*" } | Select-Object -First 1

if ($pgService) {
    Write-Host "Found service: $($pgService.Name)" -ForegroundColor Green

    try {
        Write-Host "Stopping service..."
        Stop-Service -Name $pgService.Name -Force
        Start-Sleep -Seconds 2

        Write-Host "Starting service..."
        Start-Service -Name $pgService.Name
        Start-Sleep -Seconds 3

        Write-Host "PostgreSQL restarted successfully!" -ForegroundColor Green
    } catch {
        Write-Host "ERROR: Failed to restart PostgreSQL service" -ForegroundColor Red
        Write-Host "Error: $_" -ForegroundColor Red
        Write-Host "You may need to restart PostgreSQL manually" -ForegroundColor Yellow
    }
} else {
    Write-Host "WARNING: PostgreSQL service not found" -ForegroundColor Yellow
    Write-Host "You may need to restart PostgreSQL manually" -ForegroundColor Yellow
}

# Step 6: Cleanup
Write-Host ""
Write-Host "[Step 6] Cleaning up..." -ForegroundColor Cyan

Remove-Item $downloadFile -Force -ErrorAction SilentlyContinue
Remove-Item $extractPath -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Cleanup complete!" -ForegroundColor Green

# Summary
Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Open pgAdmin (http://localhost:5050)" -ForegroundColor White
Write-Host "2. Right-click your database" -ForegroundColor White
Write-Host "3. Select 'Query Tool'" -ForegroundColor White
Write-Host "4. Run: CREATE EXTENSION IF NOT EXISTS vector;" -ForegroundColor White
Write-Host "5. You should see: 'Query returned successfully'" -ForegroundColor White
Write-Host ""
Write-Host "If successful, continue with: PGADMIN_QUICK_CHECKLIST.md" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
