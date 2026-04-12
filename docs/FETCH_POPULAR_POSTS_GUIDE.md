# YOLO LAB Popular Posts Fetcher Guide

## Overview

`scripts/fetch-popular-posts.js` 是一个自动化脚本，用于获取 YOLO LAB 网站最热门的文章（按浏览量排序），并生成 `data/popular-posts.json` 配置文件供首页部署使用。

## Features

### 智能级联策略（Cascade Strategy）

脚本采用分层降级方案，确保即使 API 故障也能继续工作：

```
┌─────────────────────────────────┐
│ Strategy 1: Jetpack Stats API   │ ← 首选（Jetpack 原生）
│ (Real-time views data)          │
└──────────────┬──────────────────┘
               │ (failed)
               ↓
┌─────────────────────────────────┐
│ Strategy 2: WordPress.com REST  │ ← 备选（WordPress官方API）
│ (Multiple parameter variants)   │
└──────────────┬──────────────────┘
               │ (failed)
               ↓
┌─────────────────────────────────┐
│ Fallback 1: Cached Config       │ ← 缓存（最多7天旧）
│ (Last successful fetch)         │
└──────────────┬──────────────────┘
               │ (no cache)
               ↓
┌─────────────────────────────────┐
│ Fallback 2: Mock Data           │ ← 开发模式（最终降级）
│ (Built-in test data)            │
└─────────────────────────────────┘
```

### 自动重试

- 每个 API 调用支持最多 2-3 次重试
- 使用指数退避（exponential backoff）
- 失败后自动尝试下一个策略

### 详细日志

- 清晰的执行流程显示
- 错误原因说明（认证失败、网络超时等）
- 性能指标（响应时间、数据量等）

## Installation

```bash
cd /c/DEX_data/Claude\ Code\ DEV

# 配置环境变量（可选）
cp .env.popular-posts.example .env.popular-posts
# 编辑 .env.popular-posts，设置有效的 WORDPRESS_DOT_COM_TOKEN

# 或通过命令行设置
export WORDPRESS_DOT_COM_TOKEN="your_valid_token_here"
```

## Usage

### 基本用法

```bash
# 获取实时数据（或使用缓存/降级方案）
node scripts/fetch-popular-posts.js

# 输出示例：
# ✓ EXECUTION SUMMARY
# Source: wordpress_rest_api
# Articles: 8/8
# IDs: [27155, 28183, 30591, 27412, 34221, 30369, 26788, 27744]
```

### 测试 API 连接

```bash
# 检查 Jetpack Stats API 和 WordPress.com API 是否可用
node scripts/fetch-popular-posts.js --test-api

# 输出：
# ✓ Jetpack endpoint: 404
# ⚠ Jetpack API requires authentication. Status: 403
# ✓ WordPress.com API: 200
# Found 898 posts
```

### 开发模式

```bash
# 使用 Mock 数据（不调用真实API）
node scripts/fetch-popular-posts.js --mock

# 使用 Sample Tier1 文章（来自 tier1-articles.json）
node scripts/fetch-popular-posts.js --sample
```

### 完整示例流程

```bash
# 1. 测试 API 连接
node scripts/fetch-popular-posts.js --test-api

# 2. 生成配置（使用开发模式）
node scripts/fetch-popular-posts.js --sample

# 3. 查看生成的配置
cat data/popular-posts.json | jq '.'

# 4. 部署到首页
node scripts/deploy-yolo-homepage.js --dry-run
```

## Configuration

### 环境变量

| 变量 | 默认值 | 说明 |
|-----|--------|------|
| `WORDPRESS_DOT_COM_TOKEN` | (hardcoded) | WordPress.com OAuth2 Token |
| `WP_COM_TOKEN` | - | 备选 token 变量名 |
| `YOLO_LAB_SITE_ID` | `133512998` | YOLO LAB 网站 ID |
| `CACHE_MAX_AGE_DAYS` | `7` | 缓存有效期（天） |

### 设置环境变量

**Windows (PowerShell)**:
```powershell
$env:WORDPRESS_DOT_COM_TOKEN = "your_token_here"
node scripts/fetch-popular-posts.js
```

**Windows (CMD)**:
```cmd
set WORDPRESS_DOT_COM_TOKEN=your_token_here
node scripts/fetch-popular-posts.js
```

**Unix/Linux/macOS**:
```bash
export WORDPRESS_DOT_COM_TOKEN="your_token_here"
node scripts/fetch-popular-posts.js
```

**.env 文件**:
```bash
# 创建 .env.popular-posts
echo 'WORDPRESS_DOT_COM_TOKEN=your_token_here' > .env.popular-posts

# 加载并执行
source .env.popular-posts && node scripts/fetch-popular-posts.js
```

## Output

脚本生成 `data/popular-posts.json`：

```json
{
  "generated_at": "2026-04-08T14:36:04.103Z",
  "period": "30_days",
  "version": "1.0",
  "popular_posts": [
    {
      "id": 27155,
      "title": "ARTICLE_TITLE_1",
      "views": 350,
      "rank": 1
    },
    ...
  ],
  "include_ids": [27155, 28183, 30591, ...],
  "exclude_ids": [],
  "meta": {
    "source": "jetpack_stats",
    "total_count": 8,
    "last_updated": "2026-04-08T14:36:04.105Z"
  }
}
```

### 字段说明

- `generated_at` — 生成时间
- `period` — 统计周期（30天）
- `version` — 配置版本
- `popular_posts` — 热门文章详细列表
  - `id` — WordPress 文章 ID
  - `title` — 文章标题
  - `views` — 浏览量
  - `rank` — 排名（1-8）
- `include_ids` — 用于 Query 块的 ID 数组
- `meta.source` — 数据来源
  - `jetpack_stats` — Jetpack Stats API
  - `wordpress_rest_api` — WordPress.com REST API
  - `cached_config` — 缓存数据
  - `mock_data` — Mock 数据（开发模式）

## Troubleshooting

### Issue: "The OAuth2 token is invalid"

**原因**：WordPress.com OAuth2 token 已过期或无效

**解决**：
1. 获取新的有效 token：https://wordpress.com/me/account/security
2. 设置环境变量：`export WORDPRESS_DOT_COM_TOKEN="new_token"`
3. 或在 `.env.popular-posts` 中更新 token
4. 重新运行脚本

**临时方案**：脚本会自动降级到缓存数据（如果存在）

### Issue: "Request timeout (10s)"

**原因**：网络连接缓慢或 API 服务超载

**解决**：
1. 检查网络连接
2. 等待几分钟后重试
3. 脚本会自动使用缓存数据

### Issue: "All API variants exhausted"

**原因**：所有 API 调用均失败

**解决**：
1. 检查 token 有效性
2. 检查网络连接
3. 检查 YOLO LAB 网站是否在线
4. 脚本会自动使用缓存数据作为后备

### Issue: 想强制使用特定来源

使用 `--test-api`、`--mock` 或 `--sample` 选项：

```bash
# 强制使用 Mock 数据
node scripts/fetch-popular-posts.js --mock

# 强制使用 Tier1 Sample
node scripts/fetch-popular-posts.js --sample

# 只测试 API，不生成配置
node scripts/fetch-popular-posts.js --test-api
```

## Integration with Deploy Script

`scripts/deploy-yolo-homepage.js` 会自动：

1. 读取 `data/popular-posts.json`
2. 提取 `include_ids`
3. 生成 Query 块 HTML
4. 将热门文章块插入首页最上方

**自动流程**：
```bash
# 1. 生成 popular-posts.json
node scripts/fetch-popular-posts.js

# 2. 部署首页（自动包含热门文章块）
node scripts/deploy-yolo-homepage.js --dry-run
```

## Automation (Scheduled Tasks)

配置定时任务每周自动更新热门文章：

### Windows Task Scheduler

```batch
# create-popular-posts-task.bat
schtasks /create /tn "YOLO_Update_Popular_Posts" /tr "node C:\DEX_data\Claude Code DEV\scripts\fetch-popular-posts.js" /sc weekly /d MON /st 02:00
```

### Linux/macOS (Cron)

```bash
# 编辑 crontab
crontab -e

# 添加行（每周一凌晨2点运行）
0 2 * * 1 cd /c/DEX_data/Claude\ Code\ DEV && node scripts/fetch-popular-posts.js
```

## Performance

- API 调用超时：10 秒
- 重试延迟：1-5 秒（指数退避）
- 总执行时间：
  - 成功 API：2-3 秒
  - 缓存 Fallback：< 100ms
  - Mock 模式：< 50ms

## API Details

### Jetpack Stats API

**Endpoints**:
- `/wp-json/jetpack/v4/stats/posts` — 文章统计
- `/wp-json/jetpack/v4/stats/top-posts` — 热门文章

**认证**：Bearer Token

**限制**：
- 需要 Jetpack Pro 或特定权限
- 可能返回 403（权限不足）

### WordPress.com REST API v1.1

**Endpoint**:
- `/rest/v1.1/sites/{SITE_ID}/posts`

**参数**：
- `number` — 获取数量（max 100）
- `status` — 文章状态（publish）
- `fields` — 返回字段

**认证**：Bearer OAuth2 Token

**注意**：`views` 字段可能不在所有响应中

## Future Enhancements

- [ ] 支持 Google Analytics API 作为数据来源
- [ ] 计算综合热门度指数（views + comments + shares）
- [ ] 按分类获取热门文章
- [ ] 本地缓存数据库（而非 JSON 文件）
- [ ] 自动更新检查和通知
- [ ] Web UI 管理界面
- [ ] 实时数据可视化仪表板

## Support

遇到问题？

1. 查看日志输出
2. 尝试 `--test-api` 诊断
3. 检查环境变量配置
4. 查看 `data/popular-posts.json` 的缓存数据

---

**Last Updated**: 2026-04-08
**Version**: 2.0
**Maintainer**: Claude Code Team
