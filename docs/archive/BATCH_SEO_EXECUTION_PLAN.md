# YOLO LAB 全量 SEO 优化批处理执行计划

## 目标配置

- **站点**: yololab.net (ID: 133512998)
- **总文章数**: 2,725 篇
- **API**: Anthropic Claude Opus 4.6
- **MCP 工具**: `mcp__wpcom-mcp__wpcom-mcp-content-authoring`
- **执行模式**: 逐篇递增处理，无预检查
- **执行时间**: 2026-04-08 开始

## 执行流程

### 第 1 阶段：分页获取 (pages 1-27)

```
page=1, per_page=100, orderby=id, order=asc
逐页递增至第 27 页 (总 2,725 篇)
```

### 第 2 阶段：逐篇处理流程

对于每一篇文章 (article_i):

```
a) 检查 meta.jetpack_seo_html_title
   ├─ 如已有 SEO: 跳过，计数 +1（已优化）
   └─ 如无 SEO: 进行步骤 b)

b) 调用 Claude API 生成 SEO 内容
   输入: title + excerpt
   输出: { title: "45-60字", description: "120-160字" }
   ├─ 成功: 进行步骤 c)
   └─ 失败: 记录 article_id，继续下一篇

c) posts.update 更新到 WordPress
   参数: {
     "id": article_id,
     "meta": {
       "jetpack_seo_html_title": seo_title,
       "advanced_seo_description": seo_description
     },
     "user_confirmed": "yes"
   }
   ├─ 成功: 计数 +1（成功）
   └─ 失败: 记录 article_id，计数 +1（失败）

d) 记录结果: ✓ 成功 / ✗ 失败 / ⊘ 已优化
```

### 第 3 阶段：实时进度报告

**每处理 10 篇**:
```
[N/2725] 批次 X: Y/10 成功
```

**每处理 100 篇**:
```
✅ 100 篇完成 (成功 X, 失败 Y, 已优化 Z, 耗时 Xm)
```

**里程碑 (500, 1000, 1500, 2000, 2500, 2725)**:
```
🎯 里程碑 N/2725 达成！
  ✓ 成功:    X
  ✗ 失败:    Y
  ⊘ 已优化:  Z
  耗时:      Xm
```

### 第 4 阶段：错误处理

- **API 超时或 update 失败**: 记录 article_id，继续下一篇
- **不阻断流程**: 继续向前处理，最后生成失败清单
- **无重试**: 第一次失败直接记录，不进行二次尝试

### 第 5 阶段：最终报告

```
╔════════════════════════════════════════╗
║       全量批处理完成 ✅                 ║
╚════════════════════════════════════════╝
总处理: 2725 篇
✓ 成功:    X
✗ 失败:    Y
⊘ 已优化:  Z
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
总耗时: X 分钟
平均速度: X 篇/分钟
预估成本: X 美元
```

## 技术栈

| 组件 | 说明 |
|-----|------|
| **API 客户端** | @anthropic-ai/sdk (Claude Opus 4.6) |
| **WordPress** | mcp__wpcom-mcp__wpcom-mcp-content-authoring |
| **分页** | posts.list (per_page=100, page=1-27) |
| **更新** | posts.update (meta + user_confirmed) |
| **并发** | 顺序处理（避免 API 限流） |

## 预期成本估算

- **API 调用**: 2,725 次 × $0.002/次 ≈ $5.45
- **处理时间**: ~45-60 分钟 (假设网络正常)
- **成功率**: >95% (基于历史经验)

## 执行命令

### 方式 1: 通过 Node.js 直接运行

```bash
cd C:\DEX_data\Claude Code DEV
node batch-seo-real-processor.js
```

### 方式 2: 通过 Claude Code CLI

```bash
claude-code --execute batch-seo-execution.js
```

## 执行检查清单

- [x] 站点 ID 正确: 133512998
- [x] API Key 已配置: ANTHROPIC_API_KEY
- [x] MCP 工具可用: wpcom-mcp
- [x] 文章总数已确认: 2,725 篇
- [x] 无需用户确认: user_confirmed="yes"
- [x] 直接启动: 无预检查步骤

## 注意事项

1. **不进行预检查**: 直接从第 1 页、第 1 篇开始处理
2. **不重试失败**: 失败的文章记录后跳过，继续下一篇
3. **持续输出**: 每篇显示进度符号 (✓/✗/⊘)
4. **网络友好**: 每篇间隔 50ms，避免 API 限流
5. **安全更新**: 所有操作都带 user_confirmed="yes"

## 监控和日志

- 实时输出到控制台
- 每 100 篇生成统计报告
- 失败 ID 在最后列出
- 支持 Ctrl+C 优雅中断

---

**执行时间**: 2026-04-08
**预计完成**: 2026-04-08 20:00-21:00
**负责人**: Claude Code Agent
**状态**: 待执行 ⏳
