# Clausidian Vault Task Scheduler Setup
# Run as Administrator

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "ERROR: This script requires Administrator privileges." -ForegroundColor Red
    exit 1
}

Write-Host "Setting up Clausidian Vault automated maintenance tasks..." -ForegroundColor Cyan
Write-Host ""

$scriptPath = "C:\DEX_data\Claude Code DEV\scripts\vault-maintenance.bat"
$userName = $env:USERNAME

# Verify script exists
if (-not (Test-Path $scriptPath)) {
    Write-Host "ERROR: Script not found at $scriptPath" -ForegroundColor Red
    exit 1
}

# Daily Task (08:00)
Write-Host "Creating Daily Maintenance task (08:00)..." -ForegroundColor Yellow
$taskName = "Clausidian-Daily-Maintenance"
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false | Out-Null
}

$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$scriptPath daily`""
$trigger = New-ScheduledTaskTrigger -Daily -At 08:00AM
$principal = New-ScheduledTaskPrincipal -UserId "$env:COMPUTERNAME\$userName" -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "Daily vault maintenance" -Force | Out-Null
Write-Host "  OK: Daily task created (08:00 every day)" -ForegroundColor Green

# Weekly Task (Monday 10:00)
Write-Host "Creating Weekly Maintenance task (Monday 10:00)..." -ForegroundColor Yellow
$taskName = "Clausidian-Weekly-Maintenance"
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false | Out-Null
}

$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$scriptPath weekly`""
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 10:00AM
$principal = New-ScheduledTaskPrincipal -UserId "$env:COMPUTERNAME\$userName" -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "Weekly vault maintenance" -Force | Out-Null
Write-Host "  OK: Weekly task created (Monday 10:00)" -ForegroundColor Green

# Monthly Task (1st at 09:00)
Write-Host "Creating Monthly Maintenance task (1st of month 09:00)..." -ForegroundColor Yellow
$taskName = "Clausidian-Monthly-Maintenance"
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false | Out-Null
}

$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$scriptPath monthly`""
$trigger = New-ScheduledTaskTrigger -Daily -At 09:00AM
$principal = New-ScheduledTaskPrincipal -UserId "$env:COMPUTERNAME\$userName" -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "Monthly vault maintenance" -Force | Out-Null
Write-Host "  OK: Monthly task created (09:00 daily, manual monthly trigger)" -ForegroundColor Green

# Verify
Write-Host ""
Write-Host "Verifying scheduled tasks..." -ForegroundColor Cyan
$tasks = @("Clausidian-Daily-Maintenance", "Clausidian-Weekly-Maintenance", "Clausidian-Monthly-Maintenance")
foreach ($task in $tasks) {
    $t = Get-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue
    if ($t) {
        $nextRun = ($t | Get-ScheduledTaskInfo).NextRunTime
        Write-Host "  OK: $task (next run: $nextRun)" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "SUCCESS: All tasks configured!" -ForegroundColor Green
Write-Host ""
Write-Host "Scheduled tasks:"
Write-Host "  1. Clausidian-Daily-Maintenance      [08:00 daily]"
Write-Host "  2. Clausidian-Weekly-Maintenance     [Monday 10:00]"
Write-Host "  3. Clausidian-Monthly-Maintenance    [09:00 daily]"
Write-Host ""
Write-Host "Logs location: C:\DEX_data\Claude Code DEV\logs\"
Write-Host "Metrics file: C:\DEX_data\Claude Code DEV\VAULT_METRICS.md"
Write-Host ""
