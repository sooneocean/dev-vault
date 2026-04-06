@echo off
REM Clausidian Vault 維護批處理包裝
REM Usage: vault-maintenance.bat [daily|weekly|monthly|all]

setlocal enabledelayedexpansion

cd /d "C:\DEX_data\Claude Code DEV"

REM 調用 bash 腳本
bash scripts/vault-maintenance.sh %1

if errorlevel 1 (
    echo.
    echo ❌ 維護任務失敗
    exit /b 1
) else (
    echo.
    echo ✅ 維護任務完成
    exit /b 0
)
