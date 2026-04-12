---
title: "Vault Maintenance — Windows Task Scheduler Setup"
type: project
status: ready-for-activation
created: 2026-04-04
updated: 2026-04-04
domain: knowledge-management
tags: [automation, maintenance, setup, scheduler]
summary: "Windows Task Scheduler setup scripts for automatic vault maintenance (daily/weekly/monthly)"
---

# Vault Maintenance Scheduler Setup

**Status**: Ready for activation
**Setup Time**: ~5 minutes
**Required**: Administrator privileges

---

## Quick Start

### Step 1: Run the Setup Script (Windows)

1. **Open File Explorer** → Navigate to: `C:\DEX_data\Claude Code DEV\scripts\`
2. **Right-click** on `setup-vault-scheduler.bat`
3. **Select**: "Run as administrator"
4. **Click** "Yes" when prompted for privileges

The script will automatically register three scheduled tasks:
- ✅ **Daily**: 9:00 AM (journal sync, index rebuild)
- ✅ **Weekly**: Monday 10:00 AM (auto-linking, orphan analysis)
- ✅ **Monthly**: 1st of month 9:00 AM (full health check, backup, git commit)

---

## Manual Setup (PowerShell Alternative)

If the batch file doesn't work, run PowerShell directly:

```powershell
# 1. Open PowerShell as Administrator
# 2. Run:
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
cd "C:\DEX_data\Claude Code DEV\scripts"
.\register-vault-tasks.ps1

# 3. Verify tasks registered:
Get-ScheduledTask -TaskPath "\Vault Maintenance\" | Format-Table TaskName, State
```

---

## Verify Setup

After running the setup script, check Task Scheduler:

```powershell
# View all vault maintenance tasks
Get-ScheduledTask -TaskPath "\Vault Maintenance\"

# Run a task manually to test
Get-ScheduledTask -TaskPath "\Vault Maintenance\" -TaskName "Daily-Maintenance" | Start-ScheduledTask

# Check task history
Get-ScheduledTaskInfo -TaskPath "\Vault Maintenance\" -TaskName "Daily-Maintenance"
```

---

## Scheduled Tasks Details

### Daily Maintenance (9:00 AM)
```
Action: bash -c "cd C:\DEX_data\Claude Code DEV && ./scripts/vault-maintenance.sh daily"
Frequency: Every day at 9:00 AM
Tasks:
  • Create daily journal entry
  • Rebuild vault index
  • Count new notes
```

### Weekly Maintenance (Monday 10:00 AM)
```
Action: bash -c "cd C:\DEX_data\Claude Code DEV && ./scripts/vault-maintenance.sh weekly"
Frequency: Every Monday at 10:00 AM
Tasks:
  • Auto-link orphaned notes
  • Analyze orphan count
  • Generate weekly review
```

### Monthly Maintenance (1st of month, 9:00 AM)
```
Action: bash -c "cd C:\DEX_data\Claude Code DEV && ./scripts/vault-maintenance.sh monthly && git commit..."
Frequency: 1st of each month at 9:00 AM
Tasks:
  • Full health check
  • Export backup to JSON
  • Generate monthly review
  • Git commit changes
```

---

## Troubleshooting

### "Access Denied" Error
- **Cause**: Not running as Administrator
- **Fix**: Right-click `setup-vault-scheduler.bat` → "Run as administrator"

### "bash.exe not found"
- **Cause**: Git Bash not installed at expected path
- **Fix**: Verify Git installation: `where bash`
- **Edit**: Update `$BashPath` in `register-vault-tasks.ps1` to actual bash location

### "Clausidian not found"
- **Cause**: Clausidian CLI not in PATH
- **Fix**: Run `npm install -g clausidian` or update path in `vault-maintenance.sh`

### Tasks not running
- **Check**: Task Scheduler → Vault Maintenance folder → Right-click task → Properties
- **Verify**: "Enabled" checkbox is checked
- **Try**: Manually run task using `Start-ScheduledTask` command above
- **Check logs**: `C:\DEX_data\Claude Code DEV\logs\maintenance-*.log`

---

## Next Steps

1. **Run the setup script** (Step 1 above)
2. **Verify tasks appear** in Windows Task Scheduler
3. **First automatic run**: Tomorrow at 9:00 AM (daily) + Monday 10:00 AM (weekly)
4. **Next monthly run**: May 1st, 2026 at 9:00 AM

---

## Removing Tasks

If you need to remove tasks later:

```powershell
# Remove all vault maintenance tasks
Get-ScheduledTask -TaskPath "\Vault Maintenance\" | Unregister-ScheduledTask -Confirm:$false

# Or remove individual task
Unregister-ScheduledTask -TaskPath "\Vault Maintenance\" -TaskName "Monthly-Maintenance" -Confirm:$false
```

---

**Status**: READY FOR ACTIVATION
**Next**: Execute `setup-vault-scheduler.bat` as Administrator
