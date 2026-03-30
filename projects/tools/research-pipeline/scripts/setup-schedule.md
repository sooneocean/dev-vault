# Setting Up Research Pipeline Scheduling

## Windows Task Scheduler Setup

### Daily Quick Scan (UTC 06:00)

1. Open Task Scheduler (`taskschd.msc`)
2. Create Task (not Basic Task):
   - Name: `Research Pipeline - Daily Quick Scan`
   - Run whether user is logged on or not
   - Run with highest privileges
3. Trigger:
   - Daily at 14:00 (UTC+8 = UTC 06:00)
   - Enabled
4. Action:
   - Program: `C:\Program Files\Git\bin\bash.exe`
   - Arguments: `/c/DEX_data/Claude Code DEV/projects/tools/research-pipeline/scripts/daily-scan.sh`
   - Start in: `C:\DEX_data\Claude Code DEV\projects\tools\research-pipeline`
5. Conditions:
   - Start only if AC power (laptop)
   - Wake computer to run (optional)
6. Settings:
   - Stop task if runs longer than 30 minutes
   - If the task fails, restart every 1 hour, up to 3 times

### Weekly Deep Scan (Sunday UTC 02:00)

1. Same as above but:
   - Name: `Research Pipeline - Weekly Deep Scan`
   - Trigger: Weekly, Sunday at 10:00 (UTC+8 = UTC 02:00)
   - Arguments: `/c/DEX_data/Claude Code DEV/projects/tools/research-pipeline/scripts/weekly-scan.sh`
   - Stop task if runs longer than 2 hours

## Verification

After setup:
```bash
schtasks /query /tn "Research Pipeline - Daily Quick Scan" /fo LIST
schtasks /query /tn "Research Pipeline - Weekly Deep Scan" /fo LIST
```

## Manual Trigger

```bash
# Quick scan
bash "/c/DEX_data/Claude Code DEV/projects/tools/research-pipeline/scripts/daily-scan.sh"

# Deep scan
bash "/c/DEX_data/Claude Code DEV/projects/tools/research-pipeline/scripts/weekly-scan.sh"
```
