# YOLO LAB Popular Posts - Scheduled Updates Guide

本指南说明如何设置自动更新热门文章配置，使首页热门文章始终保持最新。

## Overview

**目标**：每周自动获取最新的热门文章数据，无需手动干预

**频率**：每周一凌晨 02:00 UTC+8

**流程**：
```
定时任务触发 → 获取最新数据 → 生成配置 → 提交Git → 日志记录
```

---

## Windows 配置（Windows 11/10）

### 方法 1：图形界面（推荐）

#### Step 1: 打开 Task Scheduler

1. 按 `Win + R` 打开运行对话框
2. 输入 `taskschd.msc` 并按 Enter
3. 点击"Task Scheduler"打开

或者：
- 右键"此电脑" → 选择"任务计划程序"
- 开始菜单 → 搜索"任务计划程序"

#### Step 2: 创建基本任务

1. 在右侧操作窗格中，点击 **"创建基本任务..."**
2. 填写以下信息：
   - **名称**：`YOLO LAB - Update Popular Posts`
   - **描述**：`Automatically fetches latest popular posts data for homepage`
   - **点击 "下一步 >"`

#### Step 3: 设置触发器

1. 选择 **"按计划"** 单选框
2. 点击 **"下一步 >"**
3. 选择 **"每周"**
4. 设置：
   - **开始**：选择今天或明天
   - **频率**：每 `1` 周
   - **选择星期**：勾选 **"星期一"**
   - **时间**：设置为 `02:00:00`（凌晨2点）
5. 点击 **"下一步 >"**

![Task Scheduler Trigger Screenshot]

#### Step 4: 设置操作

1. 选择 **"启动程序"** 单选框
2. 点击 **"下一步 >"**
3. 填写以下信息：
   - **程序或脚本**：`node`
   - **添加参数**：`C:\DEX_data\Claude Code DEV\scripts\fetch-popular-posts.js`
   - **开始于**：`C:\DEX_data\Claude Code DEV`

4. 点击 **"下一步 >"**

**或者，使用批处理脚本**：
   - **程序或脚本**：`C:\DEX_data\Claude Code DEV\scripts\update-popular-posts.bat`
   - **开始于**：`C:\DEX_data\Claude Code DEV`

#### Step 5: 设置条件和设置

**条件标签页**（可选）：
- ☐ 仅在计算机接入电源时启动任务
- ☐ 仅在 Internet 连接可用时启动
- ✓ 在必要时唤醒计算机以运行此任务

**设置标签页**（可选）：
- ✓ 允许按需运行任务
- ✓ 如果任务已在运行，不启动新实例
- ✓ 如果任务失败，自动重启任务
- 重试间隔：`5 分钟`
- 尝试次数：`3` 次

#### Step 6: 完成

1. 检查 **"打开此任务的属性对话框"** 复选框
2. 点击 **"完成"**

---

### 方法 2：PowerShell 脚本（高级）

创建文件 `create-popular-posts-task.ps1`：

```powershell
# YOLO LAB Popular Posts - Task Scheduler Setup Script
# Usage: .\create-popular-posts-task.ps1

$TaskName = "YOLO LAB - Update Popular Posts"
$TaskPath = "\YOLO LAB\"
$ScriptPath = "C:\DEX_data\Claude Code DEV\scripts\fetch-popular-posts.js"
$ProjectDir = "C:\DEX_data\Claude Code DEV"

# Verify paths
if (-not (Test-Path $ScriptPath)) {
    Write-Error "Script not found: $ScriptPath"
    exit 1
}

Write-Host "Creating scheduled task..."
Write-Host "  Task: $TaskName"
Write-Host "  Path: $TaskPath"
Write-Host "  Trigger: Every Monday at 02:00"
Write-Host ""

# Create trigger (every Monday at 02:00)
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 02:00am

# Create action (run Node.js script)
$Action = New-ScheduledTaskAction -Execute "node" `
                                   -Argument "`"$ScriptPath`"" `
                                   -WorkingDirectory $ProjectDir

# Create settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
                                          -StartWhenAvailable `
                                          -DontStopIfGoingOnBatteries `
                                          -RestartCount 3 `
                                          -RestartInterval (New-TimeSpan -Minutes 5)

# Register task (requires admin)
try {
    Register-ScheduledTask -TaskName $TaskName `
                          -TaskPath $TaskPath `
                          -Trigger $Trigger `
                          -Action $Action `
                          -Settings $Settings `
                          -Description "Automatically fetches latest popular posts data for homepage" `
                          -Force
    Write-Host "✓ Task created successfully!"
} catch {
    Write-Error "Failed to create task: $_"
    exit 1
}

# Verify
$Task = Get-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -ErrorAction SilentlyContinue
if ($Task) {
    Write-Host ""
    Write-Host "Task Details:"
    Write-Host "  Name: $($Task.TaskName)"
    Write-Host "  Path: $($Task.TaskPath)"
    Write-Host "  State: $($Task.State)"
    Write-Host ""
    Write-Host "Next Run: $(($Task | Get-ScheduledTaskInfo).NextRunTime)"
}
```

**运行脚本**：
```powershell
# 以管理员身份打开 PowerShell，运行：
cd C:\DEX_data\Claude Code DEV
.\create-popular-posts-task.ps1
```

---

### 方法 3：命令行（CMD）

在 **命令提示符（管理员）** 中运行：

```batch
REM 创建任务
schtasks /create /tn "YOLO LAB - Update Popular Posts" ^
                  /sc weekly /d MON /st 02:00 ^
                  /tr "node C:\DEX_data\Claude Code DEV\scripts\fetch-popular-posts.js" ^
                  /f

REM 验证任务创建
schtasks /query /tn "YOLO LAB - Update Popular Posts"
```

---

## Linux/macOS 配置

### Cron Job 设置

编辑 crontab：
```bash
crontab -e
```

添加以下行：
```bash
# YOLO LAB - Update popular posts every Monday at 02:00
0 2 * * 1 cd /c/DEX_data/Claude\ Code\ DEV && bash scripts/update-popular-posts.sh
```

**Cron 字段说明**：
- `0` — 分钟（0-59）
- `2` — 小时（0-23，UTC）
- `*` — 日期（1-31）
- `*` — 月份（1-12）
- `1` — 星期（0-7，0和7为周日）

**其他示例**：
```bash
# 每天凌晨2点
0 2 * * * cd /path && bash scripts/update-popular-posts.sh

# 每周五下午3点
0 15 * * 5 cd /path && bash scripts/update-popular-posts.sh

# 每小时运行一次（测试用）
0 * * * * cd /path && bash scripts/update-popular-posts.sh
```

### 验证 Cron Job

```bash
# 列出当前用户的 cron 任务
crontab -l

# 查看系统日志中的 cron 执行
grep CRON /var/log/syslog  # Linux
log stream --predicate 'process == "cron"'  # macOS
```

---

## 日志监控

### 查看执行日志

```bash
# Windows
type C:\DEX_data\Claude Code DEV\logs\popular-posts-update.log

# Linux/macOS
tail -f /c/DEX_data/Claude Code DEV/logs/popular-posts-update.log
```

### 日志文件位置

- **Windows**：`C:\DEX_data\Claude Code DEV\logs\popular-posts-update.log`
- **Linux/macOS**：`/c/DEX_data/Claude Code DEV/logs/popular-posts-update.log`

### 日志内容示例

```
[2026-04-08 02:00:05] ====================================================================
[2026-04-08 02:00:05] YOLO LAB Popular Posts Update Script
[2026-04-08 02:00:05] ====================================================================
[2026-04-08 02:00:05]
[2026-04-08 02:00:05] OK Found fetch script: /c/DEX_data/Claude Code DEV/scripts/fetch-popular-posts.js
[2026-04-08 02:00:05] OK Config file: /c/DEX_data/Claude Code DEV/data/popular-posts.json
[2026-04-08 02:00:05]
[2026-04-08 02:00:05] Fetching latest popular posts data...
[2026-04-08 02:00:05] Running: node /c/DEX_data/Claude Code DEV/scripts/fetch-popular-posts.js
[2026-04-08 02:00:08] OK Popular posts data fetched successfully
[2026-04-08 02:00:09] OK Config file verified
[2026-04-08 02:00:09]
[2026-04-08 02:00:09] Update Summary:
[2026-04-08 02:00:09]   Source: wordpress_rest_api
[2026-04-08 02:00:09]   Articles: 8
[2026-04-08 02:00:09]   Generated: 2026-04-08T02:00:08.105Z
[2026-04-08 02:00:10]
[2026-04-08 02:00:10] Git Operations:
[2026-04-08 02:00:10] OK Staged: /c/DEX_data/Claude Code DEV/data/popular-posts.json
[2026-04-08 02:00:10] OK Committed: chore: update popular posts configuration
[2026-04-08 02:00:10] ====================================================================
[2026-04-08 02:00:10] OK Update completed successfully
```

---

## 故障排除

### 问题 1：任务未运行

**症状**：计划时间已过，但任务未执行

**排查步骤**：
1. 打开 Task Scheduler → 找到"YOLO LAB - Update Popular Posts"
2. 右键 → "属性"
3. 检查：
   - [ ] "状态"是否为"已启用"
   - [ ] "历史记录"标签页中的最后结果
   - [ ] "安全选项"中是否允许运行

4. 手动运行测试：
   ```bash
   # Windows
   cd C:\DEX_data\Claude Code DEV
   scripts\update-popular-posts.bat --test

   # Linux/macOS
   bash scripts/update-popular-posts.sh --test
   ```

### 问题 2：任务启动但失败

**症状**：任务列表中显示"出错"或"上次任务未成功"

**排查步骤**：
1. 检查日志：`cat logs/popular-posts-update.log`
2. 查看最后几行的错误信息
3. 常见错误：
   - `✗ Failed to fetch popular posts data` — API故障，脚本会自动降级到缓存
   - `X Error: Script not found` — 检查脚本路径是否正确
   - 权限问题 — 确保任务运行用户有权访问目录

### 问题 3：无法找到 Node.js

**症状**：错误 `'node' is not recognized` 或 `node: command not found`

**解决方案**：
在任务中使用 Node.js 的完整路径：

**Windows**：
```
程序或脚本：C:\Program Files\nodejs\node.exe
参数：C:\DEX_data\Claude Code DEV\scripts\fetch-popular-posts.js
```

**查找 Node.js 路径**：
```bash
# Windows
where node

# Linux/macOS
which node
```

### 问题 4：权限错误

**症状**：错误 `Access Denied` 或 `Permission denied`

**解决方案**：
- **Windows**：以管理员身份创建任务
- **Linux/macOS**：确保脚本有执行权限：
  ```bash
  chmod +x scripts/update-popular-posts.sh
  chmod +x scripts/fetch-popular-posts.js
  ```

### 问题 5：Git 提交失败

**症状**：日志显示 `! Not a git repository`

**解决方案**：
- 初始化 Git 仓库：
  ```bash
  cd C:\DEX_data\Claude Code DEV
  git init
  ```
- 或运行脚本时禁用 Git 提交：
  ```bash
  # Windows
  scripts\update-popular-posts.bat --no-commit

  # Linux/macOS
  bash scripts/update-popular-posts.sh --no-commit
  ```

---

## 高级配置

### 仅测试（不提交）

```bash
# Windows
scripts\update-popular-posts.bat --no-commit

# Linux/macOS
bash scripts/update-popular-posts.sh --no-commit
```

### 自动部署（运行更新 + 部署）

```bash
# Windows
scripts\update-popular-posts.bat --deploy

# Linux/macOS
bash scripts/update-popular-posts.sh --deploy
```

### 自定义频率

**改为每周三和周日**（Windows）：

在 Task Scheduler 中：
- 编辑任务 → "触发器"
- 修改"选择星期"为：周三、周日

**改为每月月初**（Windows）：

在 Task Scheduler 中：
- 编辑任务 → "触发器"
- 从"每周"改为"月一次"
- 设置日期为 1 日

---

## 性能和资源

### 任务执行时间

- 成功更新：2-5 秒
- 使用缓存：< 1 秒
- 失败重试：5-15 秒

### 资源消耗

- CPU：< 5% 峰值
- 内存：< 50 MB
- 磁盘写入：< 10 KB（配置文件）

### 网络流量

- API 请求：2-3 个 HTTPS 连接
- 数据传输：< 50 KB
- 典型响应时间：500-2000 ms

---

## 监控和告警

### 监控配置变更

启用 Git 钩子以监控 popular-posts.json 的变更：

```bash
cd C:\DEX_data\Claude Code DEV

# 查看最近的变更
git log -1 --oneline data/popular-posts.json

# 查看变更详情
git diff HEAD~1 data/popular-posts.json
```

### 监控任务执行

**Windows 事件查看器**：
1. 按 `Win + R` → `eventvwr.msc`
2. 导航至：Windows 日志 → 系统
3. 搜索"TaskScheduler"

---

## 禁用和删除任务

### Windows

```bash
# 禁用任务（不删除）
schtasks /change /tn "YOLO LAB - Update Popular Posts" /disable

# 启用任务
schtasks /change /tn "YOLO LAB - Update Popular Posts" /enable

# 删除任务
schtasks /delete /tn "YOLO LAB - Update Popular Posts" /f
```

### Linux/macOS

```bash
# 编辑并删除 crontab 中的行
crontab -e

# 或完全删除 crontab
crontab -r
```

---

## 通知和报告

### 邮件通知（可选）

在脚本中添加邮件发送（需要 `curl` 或 `mail` 命令）：

```bash
# 添加到 update-popular-posts.sh 的末尾
if [ -n "$NOTIFY_EMAIL" ]; then
  echo "Popular posts updated at $(date)" | mail -s "YOLO LAB: Update Completed" "$NOTIFY_EMAIL"
fi
```

### Slack 通知（可选）

```bash
# 添加到脚本
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  -d '{"text":"Popular posts updated successfully"}'
```

---

## 常见问题（FAQ）

**Q: 多久更新一次最好？**
A: 建议每周一次（每周一凌晨）。太频繁会浪费资源；太不频繁会导致数据陈旧。

**Q: 能否立即运行任务？**
A: 可以。在 Task Scheduler 中右键任务 → "运行"

**Q: 如何验证任务正在工作？**
A: 检查：
   1. 日志文件 `logs/popular-posts-update.log`
   2. 配置文件时间戳 `data/popular-posts.json` 的 `generated_at`
   3. Git 提交历史

**Q: 任务失败时如何处理？**
A: 脚本已配置为：
   1. 自动重试 3 次
   2. 降级到缓存数据
   3. 记录详细日志

---

**Last Updated**: 2026-04-08
**Version**: 1.0
