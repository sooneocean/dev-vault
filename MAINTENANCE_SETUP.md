---
title: Vault 維護自動化設置指南
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-03
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

# Vault 維護自動化設置指南

本文檔說明如何設置自動化 Vault 維護任務。

## 方案 1: Windows Task Scheduler (推薦)

### 步驟 1: 建立批處理包裝腳本

在 `scripts/` 目錄中建立 `vault-maintenance.bat`:

```batch
@echo off
REM Clausidian Vault 維護批處理包裝
cd /d "C:\DEX_data\Claude Code DEV"
bash scripts/vault-maintenance.sh %1
```

### 步驟 2: 建立 Task Scheduler 任務

#### 日常任務 (每日 08:00)

```powershell
# 以管理員身份執行 PowerShell

$taskName = "Clausidian-Daily-Maintenance"
$scriptPath = "C:\DEX_data\Claude Code DEV\scripts\vault-maintenance.bat"
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$scriptPath daily`""
$trigger = New-ScheduledTaskTrigger -Daily -At 08:00AM
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
  -Principal $principal -Settings $settings -Description "Daily Clausidian vault maintenance"
```

#### 周間任務 (每周一 10:00)

```powershell
$taskName = "Clausidian-Weekly-Maintenance"
$scriptPath = "C:\DEX_data\Claude Code DEV\scripts\vault-maintenance.bat"
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$scriptPath weekly`""
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 10:00AM
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
  -Principal $principal -Settings $settings -Description "Weekly Clausidian vault maintenance"
```

#### 月度任務 (每月 1 日 09:00)

```powershell
$taskName = "Clausidian-Monthly-Maintenance"
$scriptPath = "C:\DEX_data\Claude Code DEV\scripts\vault-maintenance.bat"
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$scriptPath monthly`""
$trigger = New-ScheduledTaskTrigger -Daily -At 09:00AM | Where-Object { $_.DayOfMonth -eq 1 }
# 注: PowerShell 內建不支持直接按月設置，改用每日 + cron
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

# 月度任務更簡單的替代方案
Start-ScheduledTask -TaskName "Clausidian-Monthly-Maintenance" # 手動觸發
```

### 步驟 3: 驗證任務

```powershell
# 列出所有 Clausidian 相關任務
Get-ScheduledTask -TaskName "Clausidian-*" | Select-Object TaskName, State, LastRunTime

# 測試執行
Start-ScheduledTask -TaskName "Clausidian-Daily-Maintenance"

# 檢查日誌
Get-Content "C:\DEX_data\Claude Code DEV\logs\maintenance-*.log" -Tail 20
```

---

## 方案 2: Claude Code 原生鉤子 (替代)

### 設置 .claude/hooks 自動同步

編輯 `.claude/settings.json`:

```json
{
  "hooks": {
    "session-stop": {
      "command": "bash scripts/vault-maintenance.sh daily",
      "description": "Daily vault sync on session exit"
    },
    "session-start": {
      "command": "bash scripts/vault-maintenance.sh daily",
      "description": "Daily vault check on session start"
    }
  }
}
```

每次 Claude Code 會話開始/結束時，自動執行日常維護。

---

## 方案 3: 手動執行

### 快速命令參考

```bash
# 進入 vault 目錄
cd /c/DEX_data/Claude Code\ Dev

# 日常維護
bash scripts/vault-maintenance.sh daily

# 周間維護
bash scripts/vault-maintenance.sh weekly

# 月度維護
bash scripts/vault-maintenance.sh monthly

# 執行所有
bash scripts/vault-maintenance.sh all
```

### 在 Claude Code 中設置快速命令

編輯 `.claude/commands/vault-sync.md`:

```markdown
# Vault Maintenance

$VAULT_PATH = "C:\DEX_data\Claude Code DEV"

## Quick Commands

- **Daily:** `cd $VAULT_PATH && bash scripts/vault-maintenance.sh daily`
- **Weekly:** `cd $VAULT_PATH && bash scripts/vault-maintenance.sh weekly`
- **Monthly:** `cd $VAULT_PATH && bash scripts/vault-maintenance.sh monthly`

## Status

Run `clausidian health` to check current vault status.
```

---

## 📊 監控維護

### 檢查日誌

```bash
# 最近的維護日誌
tail -50 logs/maintenance-*.log

# 搜索錯誤
grep "❌" logs/maintenance-*.log

# 統計執行次數
ls logs/maintenance-*.log | wc -l
```

### 追蹤指標

定期檢查 `VAULT_METRICS.md` 記錄健康評分進度。

### 定期審查計劃

| 時間表 | 內容 | 所有者 |
|--------|------|--------|
| 每周一 | 檢查周報、孤立笔記審查 | sooneocean |
| 每月 1 日 | 檢查月度回顧、更新指標 | sooneocean |
| 每季度 | 評估整體進度、調整策略 | sooneocean |

---

## 🆘 故障排除

### 任務不執行

1. 檢查 Task Scheduler 是否啟用
2. 驗證路徑是否正確
3. 檢查權限設置 (應為 "Run with highest privileges")

### 腳本錯誤

```bash
# 手動執行並查看錯誤
bash scripts/vault-maintenance.sh daily 2>&1

# 檢查 Clausidian 是否在 PATH
which clausidian
```

### Clausidian 命令失敗

```bash
# 驗證 vault 配置
echo $OA_VAULT

# 測試 clausidian 連接
clausidian stats
```

---

**Last Updated:** 2026-04-03
**Status:** Ready for Implementation
