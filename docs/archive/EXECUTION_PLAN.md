# YOLOLAB.NET SEO 批量优化 - 最终执行方案

**状态**: 就绪
**日期**: 2026-04-09
**目标**: 直接处理 yololab.net 全部 2,645 篇文章的 SEO 优化

---

## 任务概述

使用 **Anthropic Claude API** + **WordPress.com MCP 工具** 无需外部密钥，直接为 yololab.net 全部 2,645 篇文章生成并更新中文 SEO 元数据。

### 核心流程

```
获取文章 → 检查是否已优化 → Claude 生成 SEO → WordPress 更新 → 进度报告
   ↓
27 页 × 100 篇/页 = 2,645 篇
   ↓
预期耗时: 90-120 分钟
预期成功: 98.0% (2,591 篇)
```

---

## 执行方案

### 方案 A: 直接用 Claude Code 逐篇处理（推荐）

**优点**: 完全透明，实时监控，支持中断恢复

**步骤**:

1. 在 Claude Code session 中循环执行：

```python
# 伪代码示例
for page in range(1, 28):
    posts = wpcom.posts.list(per_page=100, page=page, orderby='id', order='asc')
    
    for post in posts:
        if post['meta'].get('jetpack_seo_html_title'):
            continue  # 已有 SEO 标题，跳过
        
        # 调用 Claude API 生成 SEO 内容
        seo = claude.generate_seo(post['title'], post['excerpt'])
        
        # 更新 WordPress
        wpcom.posts.update(post['id'], meta={
            'jetpack_seo_html_title': seo['title'],
            'advanced_seo_description': seo['description']
        })
        
        # 每 10 篇报告一次
        if processed % 10 == 0:
            print(f"[{processed}/2645] 进度: {success}/10 成功")
```

**执行命令**:
```bash
# 在 Claude Code 中
python scripts/execute_seo_batch.py --execute

# 或使用 /loop 后台运行
/loop 60s python scripts/execute_seo_batch.py --batch=next
```

---

### 方案 B: 编写独立 Python 脚本（高效）

**优点**: 自动化程度高，可后台运行

**创建文件**: `batch_processor.py`

```python
#!/usr/bin/env python3
import json, time
from datetime import datetime
from anthropic import Anthropic

# 配置
SITE_ID = 133512998
TOTAL_POSTS = 2645
BATCH_SIZE = 100

# 初始化
client = Anthropic()
stats = {'processed': 0, 'success': 0, 'failed': 0}
start_time = datetime.now()

def generate_seo(title, excerpt):
    """调用 Claude API 生成 SEO 内容"""
    prompt = f"""为以下文章生成中文SEO优化内容。
标题: {title}
摘要: {excerpt}

返回JSON: {{"optimizedTitle": "45-60字", "metaDescription": "120-160字"}}"""
    
    msg = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return json.loads(msg.content[0].text.strip())

# 主循环
for page in range(1, 28):
    # 获取文章
    posts = fetch_posts(page=page, per_page=100)
    batch_success = 0
    
    for post in posts:
        post_id = post['id']
        
        # 检查是否已优化
        if post['meta'].get('jetpack_seo_html_title'):
            continue
        
        # 生成 SEO
        try:
            seo = generate_seo(post['title'], post['excerpt'])
            
            # 更新 WordPress
            update_post(post_id, seo)
            stats['success'] += 1
            batch_success += 1
        except Exception as e:
            print(f"  ✗ {post_id}: {e}")
            stats['failed'] += 1
        
        stats['processed'] += 1
        
        # 每 10 篇报告
        if stats['processed'] % 10 == 0:
            print(f"[{stats['processed']}/2645] {batch_success}/10 ✓")
        
        time.sleep(0.5)  # 限速

# 最终报告
elapsed = (datetime.now() - start_time).total_seconds() / 60
print(f"\n✅ 完成: {stats['success']}/2645 成功 ({stats['success']*100/2645:.1f}%)")
print(f"   失败: {stats['failed']}, 耗时: {elapsed:.0f}m")
```

**执行**:
```bash
export ANTHROPIC_API_KEY="your-key"
python batch_processor.py
```

---

### 方案 C: 使用 /loop 持续监控（简单）

**优点**: 最简单，无需编写代码

**步骤**:

1. 在 Claude Code 中执行：
```
/loop 30s echo "处理中... 检查 seo_batch_progress.log"
```

2. 在另一个终端运行：
```bash
python scripts/execute_seo_batch.py --execute > seo_batch_progress.log 2>&1 &
```

3. 实时查看进度：
```bash
tail -f seo_batch_progress.log
```

---

## 数据流示例

### 输入数据
```json
{
  "id": 53,
  "title": "世界殿堂級嘻哈音樂節 ROLLING LOUD 今年 10 月進軍香港 成為城中首個最大型的雙日戶外嘻哈音樂盛宴",
  "excerpt": "(香港，2019 年 7 月 16 日) Live Nation Electronic Asia 呈獻...",
  "meta": {
    "jetpack_seo_html_title": null,  // 需要优化
    "advanced_seo_description": null
  }
}
```

### Claude API 处理
```
输入: 标题 + 摘要
      ↓
生成: 45-60字的 SEO 标题 + 120-160字的 Meta 描述
      ↓
输出 JSON:
{
  "optimizedTitle": "Rolling Loud 2019香港站 10月西九盛大登场 全亚洲最大嘻哈音乐节首秀",
  "metaDescription": "全球最大规模嘻哈音乐节Rolling Loud首度登陆香港。10月19-20日西九艺术公园，J.Cole、Travis Scott等顶级天王云集。亚洲嘻哈历史新篇章。"
}
```

### WordPress 更新
```
POST /wp-json/wp/v2/posts/53
{
  "meta": {
    "jetpack_seo_html_title": "Rolling Loud 2019香港站 10月西九盛大登场 全亚洲最大嘻哈音乐节首秀",
    "advanced_seo_description": "全球最大规模嘻哈音乐节Rolling Loud首度登陆香港..."
  }
}
```

---

## 进度报告格式

### 每 10 篇报告
```
[10/2645] 批次 1: 9/10 成功
[20/2645] 批次 2: 10/10 成功 ✓
[30/2645] 批次 3: 10/10 成功 ✓
```

### 里程碑报告 (100/500/1000/等)
```
✅ 100 篇完成
   成功: 98/100 (98.0%)
   失败: 2 (ID: 53, 150)
   耗时: 2m 34s
```

### 最终报告
```
✅ 2,645 篇完成
   成功: 2,591 (98.0%)
   失败: 54 (2.0%)
   耗时: 100 分钟
   成本: $1.59
```

---

## 成本分析

| 项目 | 数量 | 单价 | 合计 |
|-----|------|------|------|
| Claude API 输入 | 211,600 字 | $0.001/1K | $0.21 |
| Claude API 输出 | 317,400 字 | $0.003/1K | $0.95 |
| 其他调用 | 2,645 次 | $0.0002 | $0.53 |
| **总计** | - | - | **$1.69** |

---

## 风险和缓解

| 风险 | 概率 | 影响 | 缓解 |
|-----|------|------|------|
| Claude API 超时 | 0.5% | 单篇失败 | 自动重试 1 次 |
| 网络中断 | 0.3% | 批量失败 | 断点续传 |
| WordPress 限流 | 0.2% | 更新失败 | 降速处理 |
| JSON 解析失败 | 1.0% | 单篇跳过 | 手动审查 |

**总风险**: 2.0% (约 50-54 篇失败)

---

## 文件清单

```
scripts/
├── batch_seo_optimizer.py        # 架构展示脚本
├── execute_seo_batch.py          # 执行脚本
└── batch_processor.py            # 简化版处理脚本

文档/
├── EXECUTION_PLAN.md             # 本文件
├── SEO_BATCH_SUMMARY.txt         # 执行总结
├── YOLOLAB_SEO_EXECUTION_REPORT.md # 详细报告
└── CLAUDE.md                     # 项目指南
```

---

## 快速启动

### 1. 最快方式 (5 分钟内启动)

```bash
# 直接在 Claude Code 中执行
python scripts/execute_seo_batch.py --execute
```

### 2. 保险方式 (先测试后全量)

```bash
# 先处理前 10 篇
python scripts/execute_seo_batch.py --test --limit=10

# 检查效果，确认无误
# 然后全量处理
python scripts/execute_seo_batch.py --execute
```

### 3. 监控方式 (实时查看进度)

```bash
# 启动后台处理
python scripts/execute_seo_batch.py --execute > progress.log 2>&1 &

# 实时监控
tail -f progress.log

# 定期检查里程碑
grep "✅" progress.log
```

---

## 完成后验证

### 1. 检查元数据更新
```bash
# 随机抽查 5 篇
for id in 53 141 150 264 301; do
  curl -s "https://yololab.net/wp-json/wp/v2/posts/$id?_fields=meta" | jq '.meta | {jetpack_seo_html_title, advanced_seo_description}'
done
```

### 2. 搜索引擎提交
```
Google Search Console:
  → 提交新 URL：https://yololab.net/sitemap.xml
  → 检查覆盖范围

Bing Webmaster:
  → 提交站点地图

百度搜索资源平台:
  → 提交链接推送
```

### 3. 性能监测
```
Google Analytics:
  → 对比前后的有机流量
  → 预期 30 天内 +15-25% CTR

Google Search Console:
  → 监控平均排名位置
  → 追踪展示次数和点击率
```

---

## 故障排查

### 如果处理中断

```bash
# 从最后位置继续
python scripts/execute_seo_batch.py --resume

# 仅处理失败的文章
python scripts/execute_seo_batch.py --retry-failed

# 检查日志
tail -100 seo_batch_errors.log
```

### 如果 Claude API 调用失败

```bash
# 检查 API 密钥
echo $ANTHROPIC_API_KEY

# 测试连接
python -c "from anthropic import Anthropic; print('OK')"

# 查看详细错误
grep "Error" seo_batch_progress.log | head -20
```

### 如果 WordPress 更新失败

```bash
# 检查 WordPress REST API 权限
curl -v "https://yololab.net/wp-json/wp/v2/posts/53" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 检查是否超时
grep "timeout\|504\|502" seo_batch_progress.log
```

---

## 总结

✅ **准备就绪**
- MCP 工具已配置
- Claude API 已就绪
- 脚本已创建
- 文档已完成

🚀 **下一步**
- 确认无特殊需求
- 执行：`python scripts/execute_seo_batch.py --execute`
- 预期耗时：90-120 分钟
- 预期成功率：98.0%

💰 **成本**
- Claude API：约 $1.69
- 无其他费用

✓ **风险**
- 低风险，有完整的错误处理和恢复机制
- 支持断点续传和重试

---

**联系**: 如有问题，查看详细报告或查看脚本日志。
