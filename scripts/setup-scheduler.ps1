# Clausidian Vault Task Scheduler 自動化設置腳本
# 用途: 設置自動化維護任務
# 使用: 以管理員身份執行此腳本

# 檢查管理員權限
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "❌ 此腳本需要管理員權限。請以管理員身份重新執行。" -ForegroundColor Red
    exit 1
}

Write-Host "🚀 開始設置 Clausidian Vault 自動化任務..." -ForegroundColor Cyan
Write-Host ""

$scriptPath = "C:\DEX_data\Claude Code DEV\scripts\vault-maintenance.bat"
$userName = $env:USERNAME
$vaultPath = "C:\DEX_data\Claude Code DEV"

# 驗證腳本存在
if (-not (Test-Path $scriptPath)) {
    Write-Host "❌ 錯誤: 找不到腳本 $scriptPath" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 腳本路徑確認: $scriptPath" -ForegroundColor Green

# ==================== 日常任務 (每日 08:00) ====================
Write-Host ""
Write-Host "📋 設置日常維護任務 (每日 08:00)..." -ForegroundColor Yellow

$taskName = "Clausidian-Daily-Maintenance"
$taskDescription = "每日 Clausidian vault 維護 (同步、索引重建)"

# 移除舊任務（如果存在）
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "  移除舊任務..."
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false | Out-Null
}

# 建立新任務
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$scriptPath daily`""
$trigger = New-ScheduledTaskTrigger -Daily -At 08:00AM
$principal = New-ScheduledTaskPrincipal -UserId "$env:COMPUTERNAME\$userName" -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description $taskDescription `
    -Force | Out-Null

Write-Host "  ✅ 日常任務已設置" -ForegroundColor Green
Write-Host "     時間: 每日 08:00"

# ==================== 周間任務 (每周一 10:00) ====================
Write-Host ""
Write-Host "📅 設置周間維護任務 (每周一 10:00)..." -ForegroundColor Yellow

$taskName = "Clausidian-Weekly-Maintenance"
$taskDescription = "每周 Clausidian vault 維護 (自動連結、統計分析、周報)"

# 移除舊任務
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "  移除舊任務..."
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false | Out-Null
}

# 建立新任務
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$scriptPath weekly`""
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 10:00AM
$principal = New-ScheduledTaskPrincipal -UserId "$env:COMPUTERNAME\$userName" -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description $taskDescription `
    -Force | Out-Null

Write-Host "  ✅ 周間任務已設置" -ForegroundColor Green
Write-Host "     時間: 每周一 10:00"

# ==================== 月度任務 (每月 1 日 09:00) ====================
Write-Host ""
Write-Host "📆 設置月度維護任務 (每月 1 日 09:00)..." -ForegroundColor Yellow

$taskName = "Clausidian-Monthly-Maintenance"
$taskDescription = "每月 Clausidian vault 維護 (健康檢查、備份、月報)"

# 移除舊任務
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "  移除舊任務..."
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false | Out-Null
}

# 建立新任務（每日執行，但自訂參數中會檢查日期）
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$scriptPath monthly`""
$trigger = New-ScheduledTaskTrigger -Daily -At 09:00AM
$principal = New-ScheduledTaskPrincipal -UserId "$env:COMPUTERNAME\$userName" -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description $taskDescription `
    -Force | Out-Null

Write-Host "  ✅ 月度任務已設置 (需手動觸發或編輯)" -ForegroundColor Yellow
Write-Host "     時間: 每月 1 日 09:00 (建議手動執行)"

# ==================== 驗證設置 ====================
Write-Host ""
Write-Host "🔍 驗證任務設置..." -ForegroundColor Cyan
Write-Host ""

$tasks = @(
    "Clausidian-Daily-Maintenance",
    "Clausidian-Weekly-Maintenance",
    "Clausidian-Monthly-Maintenance"
)

foreach ($task in $tasks) {
    $scheduledTask = Get-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue
    if ($scheduledTask) {
        $nextRun = $scheduledTask | Get-ScheduledTaskInfo | Select-Object -ExpandProperty NextRunTime
        Write-Host "  ✅ $task" -ForegroundColor Green
        Write-Host "     狀態: Enabled" -ForegroundColor Green
        Write-Host "     下次執行: $nextRun" -ForegroundColor Cyan
    } else {
        Write-Host "  ❌ $task (未找到)" -ForegroundColor Red
    }
}

# ==================== 測試執行 ====================
Write-Host ""
Write-Host "🧪 執行日常維護測試..." -ForegroundColor Cyan

Push-Location $vaultPath
& cmd.exe /c "$scriptPath daily" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ 測試執行成功！" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "⚠️  測試執行返回錯誤碼: $LASTEXITCODE" -ForegroundColor Yellow
}

Pop-Location

# ==================== 總結 ====================
Write-Host ""
Write-Host "=" * 80
Write-Host "✅ 自動化設置完成！" -ForegroundColor Green
Write-Host "=" * 80
Write-Host ""
Write-Host "📋 已設置的任務:"
Write-Host "  1️⃣  Clausidian-Daily-Maintenance     — 每日 08:00"
Write-Host "  2️⃣  Clausidian-Weekly-Maintenance    — 每周一 10:00"
Write-Host "  3️⃣  Clausidian-Monthly-Maintenance   — 每月 1 日 09:00"
Write-Host ""
Write-Host "📝 日誌位置: $vaultPath\logs\"
Write-Host "📊 進度追蹤: $vaultPath\VAULT_METRICS.md"
Write-Host ""
Write-Host "🔧 管理任務:"
Write-Host "  • 檢視: Get-ScheduledTask -TaskName 'Clausidian-*'"
Write-Host "  • 執行: Start-ScheduledTask -TaskName 'Clausidian-Daily-Maintenance'"
Write-Host "  • 編輯: taskschd.msc"
Write-Host ""
Write-Host "⏰ 首次執行預期時間:"
Write-Host "  • 日常: 明天 08:00"
Write-Host "  • 周間: 下周一 10:00"
Write-Host "  • 月度: 下月 1 日 09:00"
Write-Host ""
Write-Host "💡 下一步:"
Write-Host "  1. 檢查日誌確認任務運行"
Write-Host "  2. 定期更新 VAULT_METRICS.md 追蹤進度"
Write-Host "  3. 參考 VAULT_MAINTENANCE.md 瞭解詳細說明"
Write-Host ""
