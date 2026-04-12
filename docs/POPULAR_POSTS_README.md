# YOLO LAB 首页不分区热门文章 - 完整实现指南

## 📌 项目概述

本项目实现了 YOLO LAB 首页"不分區熱門文章"区块的完整系统，包括：

- **自动数据获取**：通过 Jetpack Stats API 或 WordPress.com REST API 获取最新浏览量数据
- **智能降级方案**：API 故障时自动降级到缓存或模拟数据
- **首页集成**：自动生成并部署 WordPress Query 块到首页最顶部
- **定时更新**：每周自动获取新数据，保持首页内容新鲜
- **完整监控**：详细日志和验证，确保系统稳定运行

## 🎯 项目状态

**✅ 第1周完成**：基础架构搭建
- 数据获取脚本
- 配置存储和管理
- 首页部署集成

**✅ 第2周完成**：API 集成与实时数据
- Jetpack Stats API 集成
- WordPress.com REST API 备选方案
- 完整的错误处理和重试逻辑

**✅ 第3周完成**：自动化部署
- 定时更新脚本（Shell + Batch）
- Windows Task Scheduler 配置
- Linux/macOS Cron 配置

**⏳ 第4周**：验证和监控
- 系统验证脚本
- 完整文档和指南
- 故障排除和支持

---

## 📁 项目文件结构

```
C:\DEX_data\Claude Code DEV/
├── scripts/
│   ├── fetch-popular-posts.js              ← 核心脚本：获取热门文章数据
│   ├── update-popular-posts.sh            ← Shell 脚本：定时更新（Unix/Linux/macOS）
│   ├── update-popular-posts.bat           ← Batch 脚本：定时更新（Windows）
│   ├── deploy-yolo-homepage.js            ← 首页部署脚本（已集成）
│   ├── verify-popular-posts.js            ← 验证脚本：系统检查
│   └── ...其他脚本
│
├── data/
│   ├── popular-posts.json                 ← 配置文件：热门文章列表
│   ├── tier1-articles.json                ← 备用数据：降级方案
│   └── ...其他数据文件
│
├── docs/
│   ├── POPULAR_POSTS_README.md            ← 本文件：项目概述
│   ├── FETCH_POPULAR_POSTS_GUIDE.md       ← 使用指南：fetch 脚本
│   └── SCHEDULED_UPDATES_GUIDE.md         ← 配置指南：定时任务
│
├── logs/
│   └── popular-posts-update.log           ← 执行日志：定时任务记录
│
└── .env.popular-posts.example             ← 环境变量示例配置

```

---

## 🚀 快速开始

### 1️⃣ 验证系统

```bash
cd C:\DEX_data\Claude Code DEV
node scripts/verify-popular-posts.js

# 预期输出：
# ✓ All checks passed! System is ready for use.
```

### 2️⃣ 测试数据获取

```bash
# 使用缓存或降级方案（推荐首次测试）
node scripts/fetch-popular-posts.js --sample

# 或测试真实 API 连接
node scripts/fetch-popular-posts.js --test-api
```

### 3️⃣ 预览首页（干运行）

```bash
node scripts/deploy-yolo-homepage.js --dry-run --show-content

# 预期输出：
# ✓ Dry-run test completed successfully
# ✓ Popular posts block included with 8 articles
```

### 4️⃣ 部署到生产（可选）

```bash
# 部署首页（包含热门文章块）
node scripts/deploy-yolo-homepage.js

# 预期输出：
# ✓ Page created successfully
# ✓ Edit URL: https://yololab.net/wp-admin/post.php?post=...
```

### 5️⃣ 配置自动更新

**Windows**：
```bash
# 在命令提示符（管理员）中运行：
cd C:\DEX_data\Claude Code DEV
scripts\update-popular-posts.bat
```

**Linux/macOS**：
```bash
# 添加到 crontab
crontab -e

# 添加行：
0 2 * * 1 cd /path/to/project && bash scripts/update-popular-posts.sh
```

---

## 📊 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│ WordPress.com / Jetpack                                         │
│ (数据源：文章 + 浏览量统计)                                      │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│ fetch-popular-posts.js (数据获取层)                             │
│                                                                 │
│  ┌─ Jetpack Stats API ─┐                                       │
│  │ (首选，实时数据)      │                                       │
│  └─────┬───────────────┘                                        │
│        │ (failed)                                               │
│        ↓                                                         │
│  ┌─ WordPress.com REST API ─┐ (备选，多重试)                  │
│  │ (可靠，但views可能缺失)  │                                   │
│  └─────┬──────────────────┘                                     │
│        │ (failed)                                               │
│        ↓                                                         │
│  ┌─ Cached Config ─┐ (fallback 1，最多7天旧)                   │
│  │ (popular-posts.json) │                                       │
│  └─────┬───────────┘                                            │
│        │ (no cache)                                              │
│        ↓                                                         │
│  ┌─ Mock Data ─┐ (fallback 2，开发模式)                        │
│  └─────────────┘                                                │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│ popular-posts.json (配置文件)                                    │
│ {                                                               │
│   include_ids: [27155, 28183, ...],    ← 用于首页部署          │
│   meta: { source, generated_at }                               │
│ }                                                               │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│ deploy-yolo-homepage.js (首页部署层)                            │
│ - 读取 popular-posts.json                                      │
│ - 生成 WordPress Query 块                                       │
│ - 将块插入首页最顶部                                            │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│ https://yololab.net (首页展示)                                  │
│                                                                 │
│ ┌─ 不分區熱門文章 ─────────────────────────────────────────┐   │
│ │  [文章1]  [文章2]  [文章3]  [文章4]                      │   │
│ │  [文章5]  [文章6]  [文章7]  [文章8]                      │   │
│ └────────────────────────────────────────────────────────┘   │
│                                                                 │
│ ┌─ 熱議話題 ─────────────────────────────────────────────┐   │
│ │ (按评论数排序)                                         │   │
│ └────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 工作流程

### 自动化工作流（每周一凌晨2点）

```
1. update-popular-posts.sh/bat 被触发
   ↓
2. fetch-popular-posts.js 执行
   - 尝试 Jetpack Stats API
   - 失败则尝试 WordPress.com API
   - 仍失败则使用缓存或 Mock 数据
   ↓
3. 生成 popular-posts.json
   ↓
4. 自动提交 Git（可选）
   ↓
5. 记录日志 → logs/popular-posts-update.log
   ↓
6. 任务完成
```

### 手动部署工作流

```
1. 运行 fetch-popular-posts.js
   $ node scripts/fetch-popular-posts.js
   ↓
2. 验证输出 popular-posts.json
   $ cat data/popular-posts.json | jq '.'
   ↓
3. 部署首页
   $ node scripts/deploy-yolo-homepage.js
   ↓
4. 访问首页验证
   https://yololab.net
```

---

## 📖 完整文档

### 脚本使用指南

- **[fetch-popular-posts.js 使用指南](./FETCH_POPULAR_POSTS_GUIDE.md)**
  - API 集成细节
  - 降级方案说明
  - 环境变量配置
  - 故障排除

### 定时任务配置

- **[定时更新配置指南](./SCHEDULED_UPDATES_GUIDE.md)**
  - Windows Task Scheduler 设置
  - Linux/macOS Cron 配置
  - PowerShell 自动化脚本
  - 日志监控

---

## ⚙️ 配置参考

### 环境变量

```bash
# .env.popular-posts 或通过命令行设置
WORDPRESS_DOT_COM_TOKEN=your_oauth2_token_here
YOLO_LAB_SITE_ID=133512998
CACHE_MAX_AGE_DAYS=7
```

### popular-posts.json 格式

```json
{
  "generated_at": "2026-04-08T14:36:04.103Z",
  "period": "30_days",
  "version": "1.0",
  "popular_posts": [
    { "id": 27155, "title": "Article Title", "views": 350, "rank": 1 },
    { "id": 28183, "title": "Article Title", "views": 298, "rank": 2 },
    ...
  ],
  "include_ids": [27155, 28183, ...],
  "meta": {
    "source": "jetpack_stats",
    "total_count": 8,
    "last_updated": "2026-04-08T14:36:04.105Z"
  }
}
```

---

## 🔍 监控和维护

### 日常检查

```bash
# 验证系统状态
node scripts/verify-popular-posts.js

# 查看最近的更新
cat logs/popular-posts-update.log | tail -20

# 查看配置年龄
jq '.meta.last_updated, .meta.source' data/popular-posts.json
```

### 日志监控

```bash
# 实时监听日志
tail -f logs/popular-posts-update.log

# 查看特定时间的更新
grep "2026-04-08" logs/popular-posts-update.log
```

### Git 变更追踪

```bash
# 查看最近的配置更新
git log -1 --stat data/popular-posts.json

# 对比配置变更
git diff HEAD~1 data/popular-posts.json
```

---

## 🐛 常见问题

### Q: 热门文章多久更新一次？
**A**: 每周一凌晨 02:00 UTC+8 自动更新。可在 Task Scheduler 或 Crontab 中修改频率。

### Q: 如何立即更新？
**A**:
```bash
node scripts/fetch-popular-posts.js
# 或
bash scripts/update-popular-posts.sh --no-commit
```

### Q: API 失败时会发生什么？
**A**: 系统会自动降级到：
1. 缓存数据（最多 7 天旧）
2. 模拟数据（开发模式）

首页会继续显示最后一次成功获取的热门文章，不会中断。

### Q: 能否自定义热门文章数量？
**A**: 可以。修改 `fetch-popular-posts.js` 中的 `.slice(0, 8)` 为其他数字。

### Q: 是否支持多语言？
**A**: 系统语言跟随 YOLO LAB 设置（繁體中文）。文章标题从 WordPress.com API 自动获取。

---

## 📋 维护清单

**首次设置**：
- [ ] 运行 `verify-popular-posts.js` 确认所有组件就绪
- [ ] 运行 `fetch-popular-posts.js --sample` 测试数据获取
- [ ] 运行 `deploy-yolo-homepage.js --dry-run` 预览首页
- [ ] 配置定时任务（Windows Task Scheduler 或 Cron）

**定期维护**（每周）：
- [ ] 检查 `logs/popular-posts-update.log` 中是否有错误
- [ ] 验证 `data/popular-posts.json` 的更新时间
- [ ] 访问首页 https://yololab.net 确认热门文章显示正常

**月度审查**：
- [ ] 检查热门文章是否符合网站内容策略
- [ ] 对比浏览量数据与 Google Analytics
- [ ] 审查缓存使用频率（表示 API 故障）
- [ ] 检查日志文件大小（定期清理）

**季度优化**：
- [ ] 分析热门文章的流量趋势
- [ ] 调整热门文章数量或更新频率
- [ ] 评估是否需要多语言支持
- [ ] 考虑集成其他数据源（评分、评论等）

---

## 🔗 相关资源

- [YOLO LAB 官网](https://yololab.net)
- [WordPress.com API 文档](https://developer.wordpress.com/docs/api/)
- [Jetpack API 文档](https://jetpack.com/support/jetpack-api/)
- [首页部署脚本](./scripts/deploy-yolo-homepage.js)

---

## 📞 支持

**遇到问题？**

1. 查看 [FETCH_POPULAR_POSTS_GUIDE.md](./FETCH_POPULAR_POSTS_GUIDE.md) 的故障排除部分
2. 查看 [SCHEDULED_UPDATES_GUIDE.md](./SCHEDULED_UPDATES_GUIDE.md) 的常见问题
3. 运行 `verify-popular-posts.js` 诊断系统状态
4. 检查 `logs/popular-posts-update.log` 中的错误信息

---

**项目完成日期**：2026-04-08
**最后更新**：2026-04-08
**版本**：1.0
**状态**：✅ 生产就绪
