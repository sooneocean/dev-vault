# Register Vault Maintenance Tasks in Windows Task Scheduler
# Run as Administrator: powershell -ExecutionPolicy Bypass -File register-vault-tasks.ps1

$VaultPath = "C:\DEX_data\Claude Code DEV"
$ScriptPath = "$VaultPath\scripts\vault-maintenance.sh"
$BashPath = "C:\Program Files\Git\bin\bash.exe"  # Git Bash
$TaskUser = "SYSTEM"
$TaskFolder = "\Vault Maintenance\"

# Verify script exists
if (-not (Test-Path $ScriptPath)) {
    Write-Host "❌ Error: vault-maintenance.sh not found at $ScriptPath"
    exit 1
}

Write-Host "🔧 Setting up Vault Maintenance scheduled tasks..."
Write-Host ""

# Create task folder
try {
    $RootTask = Get-ScheduledTask -TaskPath "\" -TaskName "Vault Maintenance" -ErrorAction SilentlyContinue
    if ($null -eq $RootTask) {
        New-Item -Path "HKLM:\Software\Microsoft\Windows NT\CurrentVersion\Schedule\TaskCache\Tree" -Name "Vault Maintenance" -Force | Out-Null
        Write-Host "✅ Created task folder: \Vault Maintenance\"
    }
} catch {
    Write-Host "⚠️  Task folder may already exist, continuing..."
}

# ==================== Daily Task ====================
Write-Host ""
Write-Host "📋 Registering DAILY task (9:00 AM every day)..."

$DailyTrigger = New-ScheduledTaskTrigger -Daily -At "09:00"
$DailyAction = New-ScheduledTaskAction -Execute $BashPath -Argument "-c 'cd $VaultPath && ./scripts/vault-maintenance.sh daily'"
$DailySettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable
$DailyTask = New-ScheduledTask -Action $DailyAction -Trigger $DailyTrigger -Settings $DailySettings -Description "Daily vault maintenance: journal sync, index rebuild"

try {
    Register-ScheduledTask -TaskPath "\Vault Maintenance\" -TaskName "Daily-Maintenance" -InputObject $DailyTask -Force | Out-Null
    Write-Host "✅ Daily task registered"
} catch {
    Write-Host "❌ Failed to register daily task: $_"
}

# ==================== Weekly Task ====================
Write-Host ""
Write-Host "📅 Registering WEEKLY task (Monday 10:00 AM)..."

$WeeklyTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "10:00"
$WeeklyAction = New-ScheduledTaskAction -Execute $BashPath -Argument "-c 'cd $VaultPath && ./scripts/vault-maintenance.sh weekly'"
$WeeklySettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable
$WeeklyTask = New-ScheduledTask -Action $WeeklyAction -Trigger $WeeklyTrigger -Settings $WeeklySettings -Description "Weekly vault maintenance: auto-linking, orphan analysis, review generation"

try {
    Register-ScheduledTask -TaskPath "\Vault Maintenance\" -TaskName "Weekly-Maintenance" -InputObject $WeeklyTask -Force | Out-Null
    Write-Host "✅ Weekly task registered"
} catch {
    Write-Host "❌ Failed to register weekly task: $_"
}

# ==================== Monthly Task ====================
Write-Host ""
Write-Host "📆 Registering MONTHLY task (1st day of month, 09:00 AM)..."

# Note: PowerShell doesn't have native "first Monday" trigger, so we use monthly on day 1
# Alternative: Use Task Scheduler GUI for more complex schedules
$MonthlytTrigger = New-ScheduledTaskTrigger -Monthly -At "09:00" -DaysOfMonth 1
$MonthlyAction = New-ScheduledTaskAction -Execute $BashPath -Argument "-c 'cd $VaultPath && ./scripts/vault-maintenance.sh monthly && git add -A && git commit -m \"chore(vault): Monthly maintenance $(date +%Y-%m-%d)\" || true'"
$MonthlySettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable
$MonthlyTask = New-ScheduledTask -Action $MonthlyAction -Trigger $MonthlytTrigger -Settings $MonthlySettings -Description "Monthly vault maintenance: full health check, backup, review, git commit"

try {
    Register-ScheduledTask -TaskPath "\Vault Maintenance\" -TaskName "Monthly-Maintenance" -InputObject $MonthlyTask -Force | Out-Null
    Write-Host "✅ Monthly task registered (runs on 1st of each month)"
} catch {
    Write-Host "❌ Failed to register monthly task: $_"
}

# ==================== Verification ====================
Write-Host ""
Write-Host "🔍 Verifying registered tasks..."
Write-Host ""

try {
    $Tasks = Get-ScheduledTask -TaskPath "\Vault Maintenance\" -ErrorAction SilentlyContinue
    if ($Tasks) {
        $Tasks | Format-Table -Property TaskName, State, LastRunTime -AutoSize
        Write-Host ""
        Write-Host "✅ All tasks registered successfully!"
        Write-Host ""
        Write-Host "📝 Next scheduled runs:"
        $Tasks | ForEach-Object {
            $NextRun = $_.Triggers[0].NextRunTime
            Write-Host "  • $($_.TaskName): $NextRun"
        }
    }
} catch {
    Write-Host "⚠️  Could not verify tasks (may require admin privileges)"
}

Write-Host ""
Write-Host "✅ Task Scheduler setup complete!"
Write-Host ""
Write-Host "💡 To manually run a task:"
Write-Host "   Get-ScheduledTask -TaskPath '\Vault Maintenance\' -TaskName 'Monthly-Maintenance' | Start-ScheduledTask"
Write-Host ""
Write-Host "💡 To remove tasks:"
Write-Host "   Unregister-ScheduledTask -TaskPath '\Vault Maintenance\' -TaskName 'Daily-Maintenance' -Confirm:`$false"
