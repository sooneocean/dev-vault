@echo off
REM
REM Update YOLO LAB Popular Posts Configuration (Windows)
REM
REM Automatically fetches latest popular posts data and optionally commits to git
REM Designed to run on a schedule (via Windows Task Scheduler)
REM
REM Usage:
REM   update-popular-posts.bat                 # Run update
REM   update-popular-posts.bat --no-commit     # Don't commit to git
REM   update-popular-posts.bat --test          # Test mode (dry-run)
REM

setlocal enabledelayedexpansion

REM Get project directory (script's parent directory)
for %%i in ("%~dp0..") do set PROJECT_DIR=%%~fi
set SCRIPT_PATH=%PROJECT_DIR%\scripts\fetch-popular-posts.js
set CONFIG_FILE=%PROJECT_DIR%\data\popular-posts.json
set LOG_DIR=%PROJECT_DIR%\logs
set LOG_FILE=%LOG_DIR%\popular-posts-update.log
set DEPLOY_SCRIPT=%PROJECT_DIR%\scripts\deploy-yolo-homepage.js

REM Options
set DO_COMMIT=1
set TEST_MODE=0
set DEPLOY=0

REM Parse arguments
:parse_args
if not "%1"=="" (
  if "%1"=="--no-commit" (
    set DO_COMMIT=0
  ) else if "%1"=="--test" (
    set TEST_MODE=1
  ) else if "%1"=="--deploy" (
    set DEPLOY=1
  )
  shift
  goto parse_args
)

REM Create logs directory if needed
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Helper function to log with timestamp
:log
  for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
  for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a:%%b)
  echo [!mydate! !mytime!] %~1 >> "%LOG_FILE%"
  echo [!mydate! !mytime!] %~1
exit /b

REM Script starts here
cls
echo.
call :log "===================================================================="
call :log "YOLO LAB Popular Posts Update Script (Windows)"
call :log "===================================================================="
call :log ""

REM Verify script exists
if not exist "%SCRIPT_PATH%" (
  call :log "X Error: Script not found at %SCRIPT_PATH%"
  exit /b 1
)
call :log "OK Found fetch script: %SCRIPT_PATH%"
call :log "OK Config file: %CONFIG_FILE%"

REM Run fetch script
call :log ""
call :log "Fetching latest popular posts data..."
call :log "--------------------------------------------------------------------"

call :log "Running: node %SCRIPT_PATH%"
node "%SCRIPT_PATH%"
if errorlevel 1 (
  call :log "X Failed to fetch popular posts data (exit code: %errorlevel%)"
  exit /b 1
)

call :log "OK Popular posts data fetched successfully"

REM Verify config was generated
if not exist "%CONFIG_FILE%" (
  call :log "X Error: Config file not generated at %CONFIG_FILE%"
  exit /b 1
)

call :log "OK Config file verified: %CONFIG_FILE%"
call :log "--------------------------------------------------------------------"

REM Show summary
call :log ""
call :log "Update Summary:"

REM Try to show config info (if jq available)
where jq >nul 2>&1
if %errorlevel% equ 0 (
  for /f "delims=" %%a in ('jq ".include_ids | length" "%CONFIG_FILE%"') do set ARTICLE_COUNT=%%a
  for /f "delims=" %%a in ('jq -r ".meta.source" "%CONFIG_FILE%"') do set SOURCE=%%a
  for /f "delims=" %%a in ('jq -r ".generated_at" "%CONFIG_FILE%"') do set GENERATED_AT=%%a

  call :log "  Source: !SOURCE!"
  call :log "  Articles: !ARTICLE_COUNT!"
  call :log "  Generated: !GENERATED_AT!"
) else (
  call :log "  (jq not available for detailed summary)"
)

REM Optional: Commit to git
if %DO_COMMIT% equ 1 (
  call :log ""
  call :log "Git Operations:"
  call :log "--------------------------------------------------------------------"

  cd /d "%PROJECT_DIR%"

  REM Check if git repo exists
  git rev-parse --git-dir >nul 2>&1
  if %errorlevel% equ 0 (
    call :log "OK Git repository detected"

    REM Stage changes
    git add "%CONFIG_FILE%"
    call :log "OK Staged: %CONFIG_FILE%"

    REM Create commit (only if there are changes)
    git diff --cached --quiet
    if errorlevel 1 (
      git commit -m "chore: update popular posts configuration"
      call :log "OK Committed: chore: update popular posts configuration"
    ) else (
      call :log "i No changes to commit"
    )
  ) else (
    call :log "! Not a git repository. Skipping commit."
  )
)

REM Optional: Deploy to production
if %DEPLOY% equ 1 (
  call :log ""
  call :log "Deploying to Production:"
  call :log "--------------------------------------------------------------------"

  if not exist "%DEPLOY_SCRIPT%" (
    call :log "X Error: Deploy script not found at %DEPLOY_SCRIPT%"
    exit /b 1
  )

  call :log "Running deployment..."
  node "%DEPLOY_SCRIPT%"
  if errorlevel 1 (
    call :log "X Deployment failed (exit code: %errorlevel%)"
    exit /b 1
  )

  call :log "OK Deployment completed successfully"
)

call :log ""
call :log "===================================================================="
call :log "OK Update completed successfully"
call :log "===================================================================="
call :log ""

exit /b 0
