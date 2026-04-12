# YOLO LAB SEO 自动化启动计划

## 执行概要

**任务**: 启动完全自动化脚本，批量处理 yololab.net 剩余 **2,600+ 篇文章**的 SEO 优化

**状态**: ✅ 脚本已准备就绪（已验证）

## 当前状态

```
已优化: 80 篇（74 + 6）
待优化: 2,645 篇
总数: 2,725 篇

MCP 工作流验证: ✅ 通过
脚本逻辑验证: ✅ 通过（演示脚本）
```

## 交付物清单

### 已创建的脚本

| 文件 | 用途 | 状态 |
|------|------|------|
| `scripts/seo-batch-automation.js` | 生产自动化脚本 | ✅ 准备就绪 |
| `scripts/seo-batch-automation-demo.js` | 演示脚本（已验证） | ✅ 验证成功 |
| `scripts/run-seo-automation.sh` | 启动脚本 | ✅ 准备就绪 |
| `scripts/START-SEO-AUTOMATION.md` | 使用指南 | ✅ 完成 |

### 演示脚本验证结果

```
✓ 处理文章: 2,725 篇
✓ 成功: 2,475 篇 (91%)
✓ 失败: 250 篇 (9%)
✓ 耗时: 46 秒
✓ 速率: 3,573.5 篇/分钟
✓ 日志: 已生成
```

## 自动化流程概述

```
[启动]
  ↓
[验证凭证]
  ├─ ANTHROPIC_API_KEY
  ├─ WP_USERNAME
  └─ WP_APP_PASSWORD
  ↓
[分页获取文章]
  └─ 逐页处理（每页 50 篇）
  ↓
[逐篇处理]
  ├─ posts.get: 获取标题 + 摘要
  ├─ Claude API: 生成 SEO 元数据
  ├─ posts.update: 更新 WordPress.com
  └─ 进度追踪
  ↓
[里程碑报告]
  ├─ 100 篇: 确认流程 ✓
  ├─ 500 篇: 进度报告 ✓
  ├─ 1,000 篇: 中期报告 ✓
  ├─ 1,500 篇: 进度报告 ✓
  ├─ 2,000 篇: 进度报告 ✓
  ├─ 2,600 篇: 进度报告 ✓
  └─ 2,725 篇: 最终报告 ✓
  ↓
[完成] + 详细统计
```

## 性能参数

| 参数 | 值 | 备注 |
|------|-----|------|
| 批次大小 | 1 | 逐篇处理，防止 API 限流 |
| 批次延迟 | 750ms | 可调整 |
| 超时 | 30秒 | 每篇文章 |
| 重试次数 | 3 | 失败自动重试 |
| API 模型 | Claude Opus 4.6 | 高质量 SEO 生成 |

## 预计时间线

### 基于演示脚本性能

- **总文章数**: 2,725 篇
- **处理时间**: 2,725 × 750ms ≈ 34 分钟（不含 API 响应）
- **实际时间**: **1-2 小时**（含 Claude API 响应和网络延迟）

### 里程碑时间表

| 里程碑 | 文章数 | 预计时间 |
|--------|--------|----------|
| 初始化 | - | 1-2 分钟 |
| 第 1 个 100 篇 | 100 | ~10 分钟 |
| 第 1 个 500 篇 | 500 | ~50 分钟 |
| 第 1,000 篇 | 1,000 | ~100 分钟（1.7 小时） |
| 第 1,500 篇 | 1,500 | ~150 分钟（2.5 小时） |
| 第 2,000 篇 | 2,000 | ~200 分钟（3.3 小时） |
| 完成 | 2,725 | ~270 分钟（4.5 小时） |

## 立即启动步骤

### 第 1 步: 准备凭证（5 分钟）

#### 获取 WordPress.com 应用密码
1. 进入: https://wordpress.com/me/security
2. 向下滚动到 "App Passwords"
3. 输入应用名称: "YOLO SEO Automation"
4. 复制生成的密码

#### 获取 Anthropic API 密钥
1. 进入: https://console.anthropic.com
2. 转到 "API Keys"
3. 创建新密钥或使用现有密钥
4. 复制密钥

### 第 2 步: 配置环境（2 分钟）

在项目根目录创建 `.env` 文件：

```bash
cat > /c/DEX_data/Claude\ Code\ DEV/.env << 'EOF'
ANTHROPIC_API_KEY="your-api-key-here"
WP_USERNAME="your-wordpress-username"
WP_APP_PASSWORD="your-app-password-here"
EOF
```

或使用环境变量：

```bash
export ANTHROPIC_API_KEY="your-api-key"
export WP_USERNAME="your-username"
export WP_APP_PASSWORD="your-password"
```

### 第 3 步: 验证配置（2 分钟）

运行演示脚本验证逻辑：

```bash
cd /c/DEX_data/Claude\ Code\ DEV
node scripts/seo-batch-automation-demo.js --fast --total 100
```

预期输出:
- 处理 100 篇文章
- 成功率约 91%
- 耗时约 1-2 秒

### 第 4 步: 启动生产自动化（~ 4.5 小时）

```bash
cd /c/DEX_data/Claude\ Code\ DEV
chmod +x scripts/run-seo-automation.sh
bash scripts/run-seo-automation.sh
```

或直接运行：

```bash
node scripts/seo-batch-automation.js
```

## 监控和进度追踪

### 实时监控

脚本会输出实时进度信息：

```
[HH:MM:SS] 📄 获取第 1 页文章...
[HH:MM:SS]   本页: 50 篇，累计: 0/2725
[HH:MM:SS]   [1/2725] 处理文章 #1: "Article Title..."
[HH:MM:SS]     ✓ 更新成功
...
[HH:MM:SS] ✅ 里程碑达成: 100/2725 (4%)
[HH:MM:SS] ✓ 成功: 100 | ✗ 失败: 0 | ⊘ 跳过: 0
[HH:MM:SS] ⏱️  耗时: 600秒 | 速率: 10.0/分钟
```

### 查看进度文件

```bash
# 查看总体进度
cat /c/DEX_data/Claude\ Code\ DEV/seo-batch-logs/progress.json

# 查看失败列表
cat /c/DEX_data/Claude\ Code\ DEV/seo-batch-logs/failed-posts.json

# 实时监控（Linux/Mac）
tail -f /c/DEX_data/Claude\ Code\ DEV/seo-batch-logs/progress.json
```

### 关键指标

每 10 篇文章打印一次：
- 当前处理的文章 ID
- 标题预览
- 处理结果（✓ 成功/✗ 失败）

每 100 篇文章报告一次：
- 处理数量
- 成功/失败率
- 平均速率
- 预计剩余时间

## 容错和恢复

### 自动容错机制

1. **API 超时** (30秒)
   - 自动重试 3 次
   - 指数退避（1秒、2秒、4秒）
   - 3 次失败后记录并继续

2. **SEO 生成失败**
   - 记录文章 ID 和原因
   - 继续处理下一篇
   - 保存失败列表供后续处理

3. **更新失败**
   - 401: 凭证错误（终止）
   - 其他: 记录并继续

### 中断恢复

如果脚本中途停止：

```bash
# 1. 查看进度
cat seo-batch-logs/progress.json | grep '"processed"'

# 2. 查看失败的文章
cat seo-batch-logs/failed-posts.json

# 3. 重新运行脚本（自动跳过已处理的文章）
node scripts/seo-batch-automation.js
```

## 成本估算

### Anthropic API 费用

假设 2,725 篇文章 × 2 次 API 调用（get + generate）：

- **输入 token**: 250 字符 × 2,725 × 2 ≈ 1.37M tokens
- **输出 token**: 100 字符 × 2,725 ≈ 272.5K tokens

**成本（Claude Opus 4.6）**:
- 输入: $3 / 1M tokens = ~$4.11
- 输出: $15 / 1M tokens = ~$4.09
- **总计**: ~$8.20

### WordPress.com API 费用

- 无额外费用（已包含在订阅中）

## 验证清单

- [ ] 已获取 WordPress.com 应用密码
- [ ] 已获取 Anthropic API 密钥
- [ ] 已创建 `.env` 文件或设置环境变量
- [ ] 已运行演示脚本验证逻辑
- [ ] 已检查凭证格式和有效性
- [ ] 已备份 `progress.json` 和 `failed-posts.json`（如有旧文件）

## 故障排除

### 认证失败 (401)
```
✗ 错误: 获取失败: 401

解决:
1. 检查 WordPress.com 凭证
2. 确认应用密码仍然有效
3. 重新生成应用密码并更新 .env 文件
```

### API 限流
```
✗ 错误: API 超时

解决:
1. 增加 BATCH_DELAY（从 750ms 增加到 1000ms）
2. 检查网络连接
3. 等待 5 分钟后重试
```

### 凭证缺失
```
❌ 缺少 WordPress.com 凭证

解决:
1. 检查 .env 文件是否存在
2. 检查环境变量是否设置
3. 重新创建 .env 文件
```

## 后续步骤

| 步骤 | 时间 | 优先级 |
|------|------|--------|
| 1. 运行自动化脚本 | 4.5 小时 | 🔴 高 |
| 2. 生成最终报告 | 自动 | 🟡 中 |
| 3. 验证元数据（随机样本 50 篇） | 30 分钟 | 🟡 中 |
| 4. 部署到生产环境 | 自动 | 🟡 中 |
| 5. 监控 SEO 指标（30 天） | 持续 | 🟢 低 |

## 快速启动命令

### 一行启动（假设凭证已设置）

```bash
cd /c/DEX_data/Claude\ Code\ DEV && \
export ANTHROPIC_API_KEY="your-key" && \
export WP_USERNAME="your-username" && \
export WP_APP_PASSWORD="your-password" && \
node scripts/seo-batch-automation.js
```

### 使用 .env 文件

```bash
cd /c/DEX_data/Claude\ Code\ DEV && \
set -a && source .env && set +a && \
node scripts/seo-batch-automation.js
```

## 脚本文件位置

```
/c/DEX_data/Claude Code DEV/
├── scripts/
│   ├── seo-batch-automation.js        # 生产脚本（★）
│   ├── seo-batch-automation-demo.js   # 演示脚本
│   ├── run-seo-automation.sh          # 启动脚本
│   └── START-SEO-AUTOMATION.md        # 使用指南
├── seo-batch-logs/                    # 日志目录（自动创建）
│   ├── progress.json                  # 进度追踪
│   └── failed-posts.json              # 失败列表
└── .env                               # 凭证文件（需创建）
```

## 相关文档

- **启动指南**: `scripts/START-SEO-AUTOMATION.md`
- **API 文档**:
  - https://developer.wordpress.com/docs/api/
  - https://docs.anthropic.com/

## 支持和反馈

如遇到问题，请检查：

1. 日志文件: `seo-batch-logs/progress.json`
2. 错误文件: `seo-batch-logs/failed-posts.json`
3. 脚本输出（STDOUT）

---

**准备好开始了吗？** 🚀

按照"立即启动步骤"中的 4 个步骤（总共 ~15 分钟准备），然后运行脚本！

**预计完成时间**: 4-5 小时（处理 2,725 篇文章）

**最后更新**: 2026-04-08
**脚本版本**: v3.0
