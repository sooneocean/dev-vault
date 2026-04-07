---
title: YOLO LAB SEO 批量優化工具架構
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-03
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

# YOLO LAB SEO 批量優化工具架構

## 目標
- 3 周內優化 2700+ 篇文章
- 自動化 Title/Meta/Schema
- 零手動介入 + 完全可回滾

---

## 1. 核心數據模型

### Post SEO Profile
```json
{
  "post_id": 34844,
  "title": "Kodaline 解散震撼彈！8/24 台北站告別巡演搶票全攻略",
  "current_meta": {
    "title_length": 73,
    "description": "...",
    "h1": "青春裡的那首救贖之歌...",
    "internal_links": 0,
    "faq_count": 0,
    "images_without_alt": 0,
    "has_schema": true
  },
  "category": "music",
  "views_30d": 44,
  "priority_tier": "tier_1"  // 根據流量分層
}
```

### SEO 優化規則集
```
RULE_TITLE_LENGTH: 55-60 字元
RULE_DESCRIPTION: 155-160 字元 + CTA
RULE_H1_MATCH: H1 必含主要 SEO 詞
RULE_INTERNAL_LINKS: ≥2 個相關文章連結
RULE_FAQ_EXPANSION: ≥5 個高意圖 Q&A
RULE_IMAGE_ALT: 100% 圖片有描述性 Alt
RULE_SCHEMA: BlogPosting + Event/Product Schema
```

---

## 2. 三層優化流程

### Phase 1: 數據掃描 & 評分（第 1-2 天）
```
批量拉取 2700 篇文章
├─ 解析現有 meta/title/content
├─ 計算 SEO score (0-100)
├─ 分類：
│  ├─ Tier 1 (流量 > 20): 優先優化 (200 篇)
│  ├─ Tier 2 (流量 5-20): 次級優化 (800 篇)
│  └─ Tier 3 (流量 < 5): 低優先度 (1700 篇)
└─ 輸出：seo_baseline.json (缺陷清單)
```

**輸出示例：**
```json
{
  "post_id": 34844,
  "current_score": 72,
  "issues": [
    {"type": "title_too_long", "value": 73, "target": 58},
    {"type": "no_internal_links", "count": 0},
    {"type": "h1_not_seo_friendly", "current": "青春裡的那首救贖之歌"},
    {"type": "faq_missing", "potential": 5}
  ],
  "projected_score": 92
}
```

### Phase 2: AI 優化生成（第 3-5 天）
```
FOR EACH post IN tier_1 + tier_2:
  1. 提取 content + excerpt
  2. AI 生成 3 個 title 候選
  3. AI 生成 description + CTA
  4. AI 識別相關文章 (向量相似度)
  5. AI 擴展 FAQ (5-7 問)
  6. AI 生成圖片 Alt text
  7. 驗證 schema 一致性
  └─ 輸出：seo_optimizations.jsonl
```

**生成結果示例：**
```json
{
  "post_id": 34844,
  "optimizations": {
    "title_options": [
      "Kodaline 台北告別演唱會 8/24 TICC | 搶票攻略",
      "Kodaline 解散最終巡迴台北站 | 8/24 TICC 演出",
      "Kodaline Farewell Tour 台北 8/24 | 票價搶票資訊"
    ],
    "meta_description": "Kodaline 最終告別演唱會 8/24 台北 TICC！15 億次點聽神曲〈All I Want〉。4/1 搶票開啟，DBS/台大卡友搶先購。",
    "internal_links": [
      {"post_id": 34848, "anchor": "拍謝少年 5/22 南港演唱會", "reason": "同類音樂演出"},
      {"post_id": 34836, "anchor": "秀集團十週年演唱會攻略", "reason": "演唱會搶票類似"}
    ],
    "faq_expansion": [
      {"q": "Kodaline 最後一場演唱會在哪裡？", "a": "台北國際會議中心 (TICC)，地址..."},
      {"q": "如何用 DBS 卡搶先購票？", "a": "..."},
      {"q": "Kodaline 〈All I Want〉的故事背景？", "a": "..."}
    ],
    "image_alts": [
      {"image_id": 34846, "alt": "Kodaline 樂團 TICC 告別演唱會海報"}
    ]
  }
}
```

### Phase 3: 安全更新 & 驗證（第 6-14 天）
```
每日批量：50-100 篇文章
├─ 建立版本快照 (rollback)
├─ 批量更新 title/meta/schema
├─ 自動驗證：
│  ├─ Title 字長檢查
│  ├─ Description 字長檢查
│  ├─ Schema JSON 合法性
│  ├─ 內部連結有效性
│  └─ 圖片 Alt 填充
├─ Batch commit: `chore(seo): optimize 50 posts SEO [ID: 34844-34893]`
└─ 監控 24h：無 404/破損連結
```

---

## 3. 自動化工具堆疊

### 工具 1: SEO Scanner (Python)
```python
# scan_seo_baseline.py
from wpcom import WPComAPI
from datetime import datetime

api = WPComAPI('yololab.net')
posts = api.get_all_posts(per_page=100)
baseline = []

for post in posts:
    seo = {
        'post_id': post['id'],
        'title_len': len(post['title']),
        'description_len': len(post['excerpt']),
        'h1_count': post['content'].count('<h1'),
        'internal_links': count_internal_links(post),
        'images': count_images_without_alt(post),
        'schema_present': 'script type="application/ld+json"' in post['content'],
        'views_30d': api.get_stats(post['id'])['views']
    }
    baseline.append(seo)

# 輸出 CSV + JSON
export_seo_baseline(baseline)
```

### 工具 2: AI 優化引擎 (Claude API + prompt chaining)
```python
# ai_optimizer.py
from anthropic import Anthropic

client = Anthropic()

def optimize_post(post: dict) -> dict:
    """
    Multi-turn 優化流程
    """

    # Turn 1: 生成 Title 候選
    titles = client.messages.create(
        model="claude-opus-4-6",
        messages=[{
            "role": "user",
            "content": f"""
你是 SEO 專家。為下列文章生成 3 個最優 Title Tag。
要求：55-60 字元，包含地點/日期/CTA，適合 YOLO LAB 風格。

原文章：
標題：{post['title']}
類別：{post['category']}
內容摘要：{post['excerpt'][:300]}

生成 JSON 格式：
{{"titles": [{{"option": 1, "text": "...", "length": XX}}]}}
"""
        }]
    ).content[0].text

    # Turn 2: 生成 Meta Description
    description = client.messages.create(
        model="claude-opus-4-6",
        messages=[{
            "role": "user",
            "content": f"""
生成 157-160 字元 Meta Description，包含：
1. 核心訊息
2. 數字/稀缺信息
3. 強力 CTA

標題：{post['title']}
內容：{post['content'][:500]}

JSON: {{"description": "...", "length": XX, "cta_strength": "high"}}
"""
        }]
    ).content[0].text

    # Turn 3: 識別相關文章 (vector similarity)
    related = find_related_posts(post)

    # Turn 4: 擴展 FAQ
    faq = client.messages.create(
        model="claude-opus-4-6",
        messages=[{
            "role": "user",
            "content": f"""
根據文章內容，生成 5-7 個高搜尋意圖的 Q&A。
應涵蓋：購票方式、日期、地點、藝人背景、類似活動等。

文章：{post['title']}
內容：{post['content']}

JSON: {{"faq": [{{"q": "...", "a": "..."}}]}}
"""
        }]
    ).content[0].text

    return {
        'post_id': post['id'],
        'optimizations': {
            'titles': parse_json(titles),
            'description': parse_json(description),
            'related_posts': related,
            'faq': parse_json(faq)
        }
    }
```

### 工具 3: 批量更新 & 驗證 (Batch API)
```python
# batch_updater.py
def batch_update_posts(optimizations: list, batch_size=50):
    """
    安全批量更新，可回滾
    """

    for batch in chunked(optimizations, batch_size):
        # Step 1: 建立版本快照
        snapshots = backup_batch(batch)

        # Step 2: 準備更新
        updates = []
        for opt in batch:
            updates.append({
                'id': opt['post_id'],
                'title': opt['optimizations']['titles'][0]['text'],  # 選最優
                'excerpt': opt['optimizations']['description'],
                'meta': {
                    '_yoast_wpseo_title': opt['optimizations']['titles'][0]['text'],
                    '_yoast_wpseo_metadesc': opt['optimizations']['description']
                }
            })

        # Step 3: 執行更新
        try:
            api.bulk_update_posts(updates)
        except Exception as e:
            # 自動回滾
            restore_snapshots(snapshots)
            log_error(f"Batch {batch[0]['post_id']} failed: {e}")
            continue

        # Step 4: 驗證
        for post_id in [u['id'] for u in updates]:
            verify_post_seo(post_id)

        # Step 5: Git commit
        commit_message = f"chore(seo): optimize {len(updates)} posts [{batch[0]['post_id']}-{batch[-1]['post_id']}]"
        git_commit(commit_message)

        # Step 6: 監控 24h
        schedule_monitoring(batch, duration_hours=24)
```

---

## 4. 監測與反饋迴圈

### SEO 指標儀表板
```
實時追蹤：
├─ 優化進度：300/2700 ✓
├─ 平均 SEO score：72 → 87 (+15)
├─ 破損連結：0
├─ 排名變化：
│  ├─ 前 100 篇：avg +2.3 位置 (2 週內)
│  ├─ 新 FAQ 點擊率：+34%
│  └─ CTR 提升：+12%
└─ 修正時間：avg 18h per batch
```

### A/B 測試
```
對照組 (100 篇)：無優化
測試組 (100 篇)：完整優化

週期：2-4 周
指標：
- 搜尋排名變化
- 有機流量 CTR
- 內部連結點擊率
- 停留時間
```

---

## 5. 執行時間表

| 階段 | 日期 | 任務 | 輸出 |
|------|------|------|------|
| **掃描** | Day 1-2 | 拉取全站 SEO 現狀 | `seo_baseline.json` |
| **生成** | Day 3-5 | AI 優化建議 (Tier 1+2) | `seo_optimizations.jsonl` |
| **驗證** | Day 6 | 人工抽查 50 篇 | `validation_report.md` |
| **更新** | Day 7-14 | 批量推送 (Day 50/天) | Git commits |
| **監控** | Day 15-21 | 追蹤 SEO 效果 | `seo_impact_report.md` |
| **Tier 3** | Week 4 | 低優先度文章優化 | 完成全站 |

---

## 6. 風險與回滾方案

### 潛在風險
- ❌ Title 被 Google 改寫（正常，無需擔心）
- ❌ 內部連結斷掉（有驗證）
- ❌ Schema JSON 格式錯誤（驗證器檢查）

### 回滾策略
```
IF 任何批次失敗:
  1. 自動恢復快照 (< 1 分鐘)
  2. 通知用戶
  3. 分析失敗原因
  4. 調整優化規則
  5. 重試 (手動確認)
```

---

## 下一步

你想：
- A) 先寫 SEO Scanner？
- B) 先設計 AI Optimizer prompt？
- C) 直接跑 Phase 1 掃描？
