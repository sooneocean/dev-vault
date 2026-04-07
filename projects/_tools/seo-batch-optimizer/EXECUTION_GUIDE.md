---
title: SEO 批量優化工具 - 執行指南
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-03
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

# SEO 批量優化工具 - 執行指南

## 概述

本工具實現了 YOLO LAB 2700+ 篇文章的 SEO 批量優化流程，包含：
- 安全批量更新 (all-or-nothing 交易)
- 版本快照備份與自動回滾
- 嚴格驗證 (Title/Description/Schema/Link/Image Alt)
- Git 集成
- 24h 監控

## 工具堆疊

| 模塊 | 職責 |
|------|------|
| `snapshot_manager.py` | 版本控制：備份前狀態、支援回滾 |
| `post_validator.py` | 驗證規則：字長、Schema、連結、Alt 文本 |
| `batch_updater.py` | 批量執行：交易、驗證、rollback、Git |
| `wpcom_client.py` | API 包裝：WordPress.com API 整合 |
| `main.py` | 主程式：流程編排、日誌、報告 |

---

## 執行流程

### Phase 1: 乾運行模擬 (Dry Run)

**用途**: 檢查會變更哪些字段，不做實際修改

```bash
# 基本乾運行
python main.py \
  --site yololab.net \
  --optimizations-file seo_optimizations.jsonl \
  --dry-run \
  --simulate-only

# 輸出示例：
# ════════════════════════════════════════════════════════════════════════════
# DRY RUN SIMULATION REPORT
# ════════════════════════════════════════════════════════════════════════════
#
# Total updates: 2700
# Displaying details for first 10 posts
#
# 1. Post ID: 34844
# ────────────────────────────────────────────────────────────────────────────
#    Title (58 chars):
#      Kodaline 台北告別演唱會 8/24 TICC | 搶票攻略
#
#    Description (158 chars):
#      Kodaline 最終告別演唱會 8/24 台北 TICC！15 億次點聽神曲〈All I Want〉...
#
#    Featured Image Alt:
#      Kodaline 樂團 TICC 告別演唱會海報
#
#    Content Additions:
#      Adding FAQ schema (3245 chars)
#
# ...
```

### Phase 2: 驗證第一批

**用途**: 執行第一批（50 篇）更新，測試流程

```bash
python main.py \
  --site yololab.net \
  --optimizations-file seo_optimizations.jsonl \
  --dry-run=false \
  --batch-size 50 \
  --require-confirmation \
  --log-level DEBUG

# 互動流程：
# [INFO] Loading optimizations from seo_optimizations.jsonl
# [INFO] Loading 2700 optimizations
# [INFO] Creating 2700 batch updates
# ...
# ════════════════════════════════════════════════════════════════════════════
# BATCH UPDATE SUMMARY
# ════════════════════════════════════════════════════════════════════════════
# Batch ID: batch-34844-34893-20260330-143022
# Posts to update: 50
# Dry run: False
# Started at: 2026-03-30T14:30:22.000000
#
# Sample updates:
#   Post 34844: Title (58 chars), Description (158 chars)
#   ...
# ════════════════════════════════════════════════════════════════════════════
#
# Proceed with 50 updates? (yes/no): yes
#
# [INFO] [BATCH] Creating snapshots...
# [INFO] [BATCH] Executing updates...
# [INFO] [BATCH] Updating 1/50: post 34844
# ...
# [INFO] [BATCH] Committed: abc1234
```

### Phase 3: 批量推送 (Production)

**用途**: 連續批量更新所有 2700 篇文章

```bash
# 自動批量處理（無需確認，適合後台運行）
python main.py \
  --site yololab.net \
  --optimizations-file seo_optimizations.jsonl \
  --batch-size 50 \
  --log-level INFO > batch_run.log 2>&1 &

# 監控進度
tail -f batch_run.log

# 輸出進度：
# [INFO] [UPDATER] Processing 54 batches (2700 total posts)
# [INFO] [UPDATER] Batch 1/54: 50 posts
# [INFO] [BATCH] Starting batch batch-34844-34893-20260330-143022
# [INFO] [BATCH] Validating 50 updates...
# [INFO] [BATCH] Creating snapshots...
# [INFO] [BATCH] Executing updates...
# [INFO] [BATCH] Completed: 50 successful, 0 failed
# [INFO] [BATCH] Committed: abc1234def5678
# [INFO] [BATCH] Started 24h monitoring for 50 posts
# ...
# [INFO] [UPDATER] Batch 54/54: 50 posts
# [INFO] [UPDATER] Batch processing complete: 2700 successful, 0 failed
```

### Phase 4: 監控與驗證

**用途**: 確保更新成功，無 404 或破損

```bash
# 查看批次日誌
ls batch_logs/
# batch-34844-34893-20260330-143022-result.json
# batch-34894-34943-20260330-143115-result.json
# ...

# 檢查批次結果
python -m json.tool batch_logs/batch-34844-34893-20260330-143022-result.json

# 輸出示例：
# {
#   "batch_id": "batch-34844-34893-20260330-143022",
#   "batch_size": 50,
#   "status": "completed",
#   "started_at": "2026-03-30T14:30:22",
#   "completed_at": "2026-03-30T14:32:18",
#   "successful_updates": 50,
#   "failed_updates": 0,
#   "git_commit": "abc1234",
#   "update_results": [
#     {
#       "post_id": 34844,
#       "success": true,
#       "snapshot_id": "post-34844-20260330143022345678",
#       "old_values": {...},
#       "new_values": {...}
#     },
#     ...
#   ]
# }

# 監控 404 錯誤（24h）
python monitor_404.py --batch-log batch_logs/batch-34844-34893-20260330-143022-result.json
```

---

## 回滾機制

### 自動回滾 (批次失敗時)

如果批次中所有更新失敗，自動執行回滾：

```bash
[ERROR] [BATCH] All updates failed, rolling back...
[INFO] [BATCH] Rolled back 50 posts from batch batch-34844-34893-20260330-143022
[INFO] [BATCH] Status: ROLLED_BACK
```

### 手動回滾 (特定批次)

```python
# 回滾指定批次
from snapshot_manager import SnapshotManager

mgr = SnapshotManager()
restored = mgr.restore_batch(
    batch_id="batch-34844-34893-20260330-143022"
)

print(f"Restored {len(restored)} posts")
```

---

## 驗證規則詳解

### 1. Title 字長驗證

```
規則: 55-65 字元 (最佳 ~60)
範例:
  ✓ 正確 (58 chars): "Kodaline 台北告別演唱會 8/24 TICC | 搶票攻略"
  ✗ 過短 (40 chars): "Kodaline 演唱會搶票"
  ✗ 過長 (75 chars): "Kodaline 樂團在台北國際會議中心舉辦的告別演唱會訊息 8 月 24 號..."
```

### 2. Description (Meta) 字長驗證

```
規則: 155-165 字元 (最佳 ~160) + 必須包含 CTA
範例:
  ✓ 正確 (158 chars, 含 CTA "搶票"):
    "Kodaline 最終告別演唱會 8/24 台北 TICC！15 億次點聽神曲〈All I Want〉。
     4/1 搶票開啟，DBS/台大卡友搶先購。"

  ✗ 無 CTA:
    "Kodaline 樂團的告別演唱會將在台北舉行，時間是 8 月 24 號..."
```

### 3. Schema JSON 驗證

```
規則: 有效的 JSON-LD，支援 FAQPage 和 BlogPosting
範例:
  ✓ 正確:
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": [
        {
          "@type": "Question",
          "name": "Kodaline 最後一場演唱會在哪裡？",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "台北國際會議中心 (TICC)，地址..."
          }
        }
      ]
    }
    </script>

  ✗ 格式錯誤:
    {"@type": "FAQPage", ...} (缺少 mainEntity)
```

### 4. 內部連結驗證

```
規則: 至少 2 個內部連結，連結的 post ID 必須存在
範例:
  ✓ 正確:
    <a href="https://yololab.net/p/34848/">拍謝少年演唱會</a>
    <a href="https://yololab.net/p/34836/">秀集團演唱會</a>

  ✗ 不足:
    只有 1 個連結

  ✗ 斷掉:
    <a href="https://yololab.net/p/999999/">已刪除文章</a> (post 不存在)
```

### 5. 圖片 Alt 文本驗證

```
規則: 所有圖片都要有 alt，且長度 > 5 字
範例:
  ✓ 正確:
    <img src="..." alt="Kodaline 樂團 TICC 告別演唱會海報" />

  ✗ 空 alt:
    <img src="..." alt="" />

  ✗ Alt 太短:
    <img src="..." alt="圖" />
```

---

## 故障排除

### 問題: 批次失敗並回滾

**症狀:**
```
[ERROR] [BATCH] All updates failed, rolling back...
[ERROR] Failed to update post 34844: 500 Internal Server Error
```

**解決:**
1. 檢查最新的批次日誌：`batch_logs/batch-*-result.json`
2. 查看詳細錯誤信息：`grep "ERROR" batch_optimizer.log`
3. 驗證 WordPress.com API 是否可用
4. 檢查最後一個成功的批次提交

### 問題: 驗證失敗

**症狀:**
```
[WARNING] Post 34844 failed validation:
  - Title too long: 73 chars (max 65)
  - Description missing CTA
```

**解決:**
1. 檢查優化建議文件 (`seo_optimizations.jsonl`)
2. 重新生成 AI 優化建議
3. 或手動調整驗證規則

### 問題: API 速率限制

**症狀:**
```
[ERROR] Failed to update post 34844: 429 Too Many Requests
```

**解決:**
1. 降低 `--batch-size` (e.g., 25 instead of 50)
2. 增加 API 延遲：編輯 `batch_updater.py` 中的 `API_RATE_LIMIT_DELAY`

---

## 進度追蹤

### 查看實時進度

```bash
# 方式 1: 尾隨日誌
tail -f batch_optimizer.log | grep "BATCH\|UPDATER"

# 方式 2: 統計已完成
ls -lrt batch_logs/ | wc -l  # 批次數

# 方式 3: 統計成功
grep "successful_updates" batch_logs/*-result.json | \
  awk -F: '{sum+=$NF} END {print "Total: " sum}'
```

### 進度報告範例

```
Day 1 (3 batches):
  ✓ Batch 1/54: posts 34844-34893 (50 updated)
  ✓ Batch 2/54: posts 34894-34943 (50 updated)
  ✓ Batch 3/54: posts 34944-34993 (50 updated)
  Progress: 150/2700 (5.5%)

Day 2 (10 batches):
  ✓ Batches 4-13 completed
  Progress: 650/2700 (24%)

Day 3 (Remaining):
  ✓ Batches 14-54 completed
  Progress: 2700/2700 (100%)
```

---

## Git 提交規範

每批完成後自動提交：

```
commit abc1234def5678
Author: SEO Optimizer <bot@yololab.net>
Date:   Mon Mar 30 14:30:22 2026 +0800

    chore(seo): optimize 50 posts [ID: 34844-34893]
```

查看所有 SEO 提交：

```bash
git log --oneline --grep="chore(seo)"
# abc1234 chore(seo): optimize 50 posts [ID: 34844-34893]
# def5678 chore(seo): optimize 50 posts [ID: 34894-34943]
# ...
```

---

## 備份與恢復

### 查看快照

```bash
python -c "
from snapshot_manager import SnapshotManager
mgr = SnapshotManager()
snapshots = mgr.list_snapshots(limit=20)
for s in snapshots:
    print(f'{s[\"snapshot_id\"]}: post {s[\"post_id\"]} ({s[\"status\"]})')
"
```

### 導出批次備份

```python
from snapshot_manager import SnapshotManager

mgr = SnapshotManager()
export_path = mgr.export_batch_snapshots(
    batch_id="batch-34844-34893-20260330-143022",
    export_path="backup_batch_34844.json"
)

print(f"Exported to {export_path}")
```

### 清理舊快照

```python
# 只保留最近 100 個快照
deleted = mgr.cleanup_old_snapshots(keep_recent=100)
print(f"Deleted {deleted} old snapshots")
```

---

## 性能最佳實踐

| 設置 | 建議值 | 說明 |
|------|--------|------|
| `batch_size` | 50 | API 速率限制適中，平衡吞吐量 |
| `rate_limit_delay` | 0.5 秒 | WordPress.com API 建議 |
| `require_confirmation` | 第一批是 | 生產環境後改為否 |
| `snapshot_cleanup` | 100 最近 | 節省磁碟空間 |

---

## 成功檢查清單

- [ ] 乾運行模擬正確顯示變更
- [ ] 第一批 (50 篇) 成功執行
- [ ] Git 提交正確記錄
- [ ] 快照能成功還原
- [ ] 沒有驗證錯誤
- [ ] API 沒有速率限制錯誤
- [ ] 24h 監控無 404
- [ ] 最終統計: 2700/2700 成功

---

## 聯繫與支援

遇到問題？

1. 檢查日誌：`batch_optimizer.log`
2. 查看批次結果：`batch_logs/`
3. 驗證錯誤：`-log-level DEBUG`
4. 停止批次：`Ctrl+C` (已更新的批次不會回滾)
