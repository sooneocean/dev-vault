# SEO Batch Optimizer — Phase 1: Baseline Scanner

自動化批量掃描 2700+ 篇文章的 SEO 現狀，生成優化基線與優先級排序。

---

## 1. 概述

### Phase 1：基線掃描 & 分類
**目的**：蒐集全站 SEO 現狀，識別 Top Issues，為 Phase 2（AI 優化）準備數據。

**輸出**：
- `seo_baseline.csv` — 可用表格檢視 (300 篇示例)
- `seo_baseline.json` — 完整分析 + 缺陷清單
- `scan_seo_baseline.log` — 執行日誌

**執行時間估算**：
| 規模 | 耗時 | 速度 |
|------|------|------|
| 300 posts (示例) | ~1 秒 | ~300 posts/sec |
| 1000 posts | ~5 秒 | ~200 posts/sec* |
| 2700 posts (全站) | ~15-20 秒 | ~150 posts/sec* |

*實際速度取決於 WordPress.com API 限流、網路延遲、內容大小

---

## 2. 快速開始

### 必備環境
- Python 3.8+
- 無額外依賴 (僅標準庫)

### 執行掃描

```bash
cd tools/seo-batch-optimizer/
python scan_seo_baseline.py
```

**輸出示例**：
```
============================================================
SEO Scanner - Phase 1: Baseline Collection
============================================================
Starting SEO scan of yololab.net
Configuration: per_page=100, max_pages=None

Progress: 50/2700 posts (1%) | Rate: 5547.5 posts/sec | ETA: 0:00:00
Progress: 100/2700 posts (3%) | Rate: 5508.1 posts/sec | ETA: 0:00:00
...
Progress: 300/2700 posts (11%) | Rate: 224.2 posts/sec | ETA: 0:00:10

SCAN SUMMARY
============================================================
Total posts processed: 300
Average SEO score: 53.1/100
Score range: 47-57
Average views (30d): 125.1

Tier Distribution:
  tier_1: 228 posts (76.0%)
  tier_2: 36 posts (12.0%)
  tier_3: 36 posts (12.0%)

Top Issues:
  title_length_issue: 300 posts
  description_length_issue: 300 posts
  schema_missing: 300 posts
  images_missing_alt: 201 posts
  internal_links_insufficient: 99 posts

Execution time: 0m 1s
```

---

## 3. 輸出文件格式

### CSV 格式 (`seo_baseline.csv`)
易於在 Excel/Google Sheets 中檢視和排序。

```csv
post_id,title,title_len,description_len,h1_count,internal_links,images_no_alt,schema_present,views_30d,seo_score,tier,issue_count
1,Kodaline 解散震撼彈！8/24 台北站...,32,56,1,2,1,no,20,51,tier_2,4
2,五月天 8/25 北京演唱會｜搶票...,21,45,1,1,0,no,296,54,tier_1,4
```

**欄位說明**：
| 欄位 | 說明 |
|------|------|
| `post_id` | WordPress 文章 ID |
| `title` | 文章標題（100 字元截斷） |
| `title_len` | 標題字數 (目標: 55-60) |
| `description_len` | Meta Description 字數 (目標: 155-160) |
| `h1_count` | H1 標籤數 (需≥1) |
| `internal_links` | 內部連結數 (目標: ≥2) |
| `images_no_alt` | 缺少 Alt Text 的圖片數 |
| `schema_present` | 是否存在 JSON-LD Schema |
| `views_30d` | 過去 30 天瀏覽數 |
| `seo_score` | SEO 評分 (0-100) |
| `tier` | 優先級 (tier_1/2/3) |
| `issue_count` | 缺陷數量 |

### JSON 格式 (`seo_baseline.json`)
包含完整分析、所有缺陷、優化潛力。

```json
{
  "metadata": {
    "timestamp": "2026-03-30T23:23:22.036882",
    "total_posts": 300,
    "phase": "Phase 1: SEO Baseline Scan"
  },
  "statistics": {
    "total_posts": 300,
    "avg_seo_score": 53.15,
    "min_score": 47,
    "max_score": 57,
    "avg_views_30d": 125.06,
    "tier_distribution": {
      "tier_1": 228,
      "tier_2": 36,
      "tier_3": 36
    },
    "top_issues": {
      "title_length_issue": 300,
      "description_length_issue": 300,
      "schema_missing": 300,
      "images_missing_alt": 201,
      "internal_links_insufficient": 99
    },
    "execution_time": "0m 1s"
  },
  "posts": [
    {
      "post_id": 50,
      "title": "五月天 8/24 北京演唱會｜搶票最新訊息",
      "title_len": 21,
      "description_len": 46,
      "h1_count": 1,
      "internal_links": 1,
      "images_no_alt": 0,
      "schema_present": false,
      "views_30d": 344,
      "seo_score": 54,
      "tier": "tier_1",
      "issues": [
        {
          "type": "title_length_issue",
          "value": 21,
          "target_range": [55, 60],
          "severity": "high"
        },
        {
          "type": "description_length_issue",
          "value": 46,
          "target_range": [155, 160],
          "severity": "high"
        }
      ],
      "optimization_potential": 46
    }
  ]
}
```

**統計欄位**：
| 欄位 | 說明 |
|------|------|
| `avg_seo_score` | 平均 SEO 分數 |
| `tier_distribution` | 各級別文章數 |
| `top_issues` | 最常見的 5-10 個缺陷及發生次數 |
| `execution_time` | 總掃描時間 |

**帖子對象**：
| 欄位 | 說明 |
|------|------|
| `issues` | 缺陷陣列（high/medium 優先級） |
| `optimization_potential` | 可提升分數 (100 - current_score) |

---

## 4. SEO 評分邏輯 (0-100)

### 計分規則

| 項目 | 權重 | 評分標準 |
|------|------|--------|
| **Title 最優** | 15 | 55-60 字元 → 滿分 |
| **Description 最優** | 15 | 155-160 字元 → 滿分 |
| **H1 存在** | 10 | ≥1 個 H1 → 滿分 |
| **內部連結** | 12 | ≥2 個相關連結 → 滿分 |
| **圖片 Alt Text** | 12 | 100% 圖片有描述 → 滿分 |
| **Schema** | 10 | JSON-LD BlogPosting 存在 → 滿分 |
| **流量加分** | 10 | views > 50 → 滿分 |
| **內容健康度** | 16 | 基礎檢驗 (內部 80% 滿分) |

### 優先級分層

| Tier | 條件 | 數量 | 優先度 |
|------|------|------|--------|
| **Tier 1** | 30d 瀏覽 > 20 | ~200 篇 | 最高 (優先優化) |
| **Tier 2** | 30d 瀏覽 5-20 | ~800 篇 | 次級 (依次優化) |
| **Tier 3** | 30d 瀏覽 < 5 | ~1700 篇 | 低 (長期優化) |

### 示例計分

```
Post ID: 50
─────────────
Title: "五月天 8/24 北京演唱會｜搶票最新訊息" (21 chars)
  → Issue: 太短 (目標 55-60)
  → Score: 15 × (21/55) ≈ 5.7 / 15

Description: 46 chars
  → Issue: 太短 (目標 155-160)
  → Score: 15 × (46/155) ≈ 4.5 / 15

H1: 1 個
  → OK
  → Score: 10 / 10

Internal Links: 1 個
  → Issue: 需 2 個
  → Score: 12 × (1/2) = 6 / 12

Images Alt: 0 缺少
  → OK
  → Score: 12 / 12

Schema: 無
  → Issue
  → Score: 10 × 0.4 = 4 / 10

Views: 344 (tier_1)
  → OK (>50)
  → Score: 10 / 10

Content: 基礎通過
  → Score: 16 × 0.8 = 12.8 / 16

總分: 5.7 + 4.5 + 10 + 6 + 12 + 4 + 10 + 12.8 = 54 / 100
```

---

## 5. 配置與自訂

編輯 `scan_seo_baseline.py` 頂部設定：

```python
SITE_URL = "yololab.net"
ENABLE_MOCK = True  # False 時使用真實 wpcom-mcp
MAX_PAGES = 3       # None = 掃描全部
```

### 環境變數 (未來支援)
```bash
# 連接到實際 WordPress.com 網站
export WPCOM_SITE=yololab.net
export SCAN_BATCH_SIZE=100
export SCAN_RETRY_COUNT=3

python scan_seo_baseline.py
```

---

## 6. 整合 WordPress.com MCP（生產環境）

### 步驟 1：安裝 wpcom-mcp
```bash
pip install wpcom-mcp
```

### 步驟 2：配置認證
```bash
export WPCOM_TOKEN=<your-token>
```

### 步驟 3：修改 scan_seo_baseline.py
```python
# 在 _fetch_posts_page() 中取消註解：
from wpcom_client import WPComAPI

api = WPComAPI(self.site_url)
return api.get_posts(page=page, per_page=per_page, stats=True)
```

### 步驟 4：啟用真實掃描
```python
ENABLE_MOCK = False
MAX_PAGES = None  # 掃描全部 2700 篇
```

---

## 7. 數據分析示例

### 導入 CSV 到 Google Sheets
1. 打開 Google Sheets
2. 檔案 > 匯入 > 上傳 `seo_baseline.csv`
3. 建立篩選器查看各 Tier：
   ```
   篩選 tier = "tier_1"
   排序 seo_score (低到高)
   ```

### 用 Python 分析 JSON
```python
import json

with open('seo_baseline.json') as f:
    data = json.load(f)

# 找到分數最低的 10 篇
worst_posts = data['posts'][-10:]
for post in worst_posts:
    print(f"[{post['seo_score']}/100] {post['title'][:50]}")
    for issue in post['issues'][:3]:
        print(f"  - {issue['type']}")
```

### 統計各 Tier 的平均分
```python
from collections import defaultdict

tier_scores = defaultdict(list)

for post in data['posts']:
    tier_scores[post['tier']].append(post['seo_score'])

for tier, scores in tier_scores.items():
    avg = sum(scores) / len(scores)
    print(f"{tier}: {avg:.1f}/100 ({len(scores)} posts)")
```

---

## 8. 常見問題

### Q1: 為什麼所有帖子都有 "title_length_issue"？
**A**: 這是測試數據。真實掃描會根據實際 WordPress 文章長度評估。測試模板標題故意設較短。

### Q2: 如何跳過特定文章？
**A**: 在 `_fetch_posts_page()` 中新增篩選：
```python
posts = [p for p in posts if p['id'] not in EXCLUDE_IDS]
```

### Q3: 能否並行掃描加速？
**A**: 可以。改用 `concurrent.futures.ThreadPoolExecutor`：
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    metrics = list(executor.map(self._scan_post, posts))
```

### Q4: 如何與 Phase 2（AI 優化）銜接？
**A**: 將 `seo_baseline.json` 輸入到 `ai_optimizer.py`：
```python
import json

with open('seo_baseline.json') as f:
    baseline = json.load(f)

# 篩選 tier_1 + tier_2
priority_posts = [
    p for p in baseline['posts']
    if p['tier'] in ('tier_1', 'tier_2')
]

# 傳給 AI 優化引擎
optimizations = ai_optimizer.optimize_batch(priority_posts)
```

---

## 9. 性能優化

### 當前實現
- 單線程順序掃描
- ~150-300 posts/sec (取決於內容大小)
- 2700 篇估計 15-20 秒

### 潛在優化
1. **批量 API 呼叫**：一次 100 篇而非逐個
   - 預估加速 ~40%

2. **非同步 I/O**
   - 使用 `aiohttp` + `asyncio`
   - 預估加速 ~60-80%

3. **並行掃描**（4 個 worker）
   - 每個 worker 獨立掃描不同 page
   - 預估加速 ~3-4 倍

**推薦**：對於 2700 篇文章，串行掃描 15-20 秒已足夠。如需更快，可在 Phase 2 時整合併行。

---

## 10. 下一步 (Phase 2-3)

### Phase 2：AI 優化建議 (Day 3-5)
```bash
python ai_optimizer.py seo_baseline.json
# 輸出: seo_optimizations.jsonl (AI 生成的標題、描述、FAQ)
```

### Phase 3：安全批量更新 (Day 6-14)
```bash
python batch_updater.py seo_optimizations.jsonl
# 輸出: git commits, 版本快照, 監控報告
```

---

## 11. 授權與貢獻

MIT License — 自由使用、修改、分享。

問題回報：請在 GitHub Issues 提交。

---

**祝優化順利！** 🚀
