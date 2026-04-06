@echo off
REM Run this file as Administrator to set up vault maintenance scheduled tasks
REM Right-click → Run as administrator

echo.
echo ============================================
echo  Vault Maintenance - Windows Task Scheduler
echo ============================================
echo.

REM Check if running as admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ ERROR: This script must run as Administrator
    echo.
    echo Please right-click this file and select "Run as administrator"
    pause
    exit /b 1
)

echo ✅ Running as Administrator
echo.
echo Registering scheduled tasks...
echo.

REM Get script directory
set SCRIPT_DIR=%~dp0

REM Run PowerShell script
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%register-vault-tasks.ps1"

if %errorLevel% equ 0 (
    echo.
    echo ============================================
    echo  ✅ Setup complete!
    echo ============================================
    echo.
    echo Scheduled tasks are now active:
    echo  • Daily maintenance: 9:00 AM
    echo  • Weekly maintenance: Monday 10:00 AM
    echo  • Monthly maintenance: 1st of month 9:00 AM
    echo.
    echo Press any key to exit...
) else (
    echo.
    echo ❌ Setup failed. Check errors above.
    echo.
    echo Press any key to exit...
)

pause >nul
