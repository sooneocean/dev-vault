# SEO 批量優化工具

YOLO LAB 的企業級 WordPress.com 批量 SEO 優化系統，支援：
- **安全批量更新**：交易式 (all-or-nothing) 更新，失敗自動回滾
- **版本控制**：每批前快照備份，支援完整恢復
- **嚴格驗證**：Title/Description/Schema/Link/Image Alt 規則檢查
- **Git 集成**：自動提交，每批留下追蹤記錄
- **24h 監控**：部署後驗證無 404、無破損

目標：3 週內安全優化 2700+ 篇文章

---

## 快速開始

### 1. 安裝

```bash
# 假設已有 Python 3.8+
cd tools/seo-batch-optimizer

# 安裝依賴 (如需)
# pip install -r requirements.txt
```

### 2. 乾運行 (檢查預覽)

```bash
python main.py \
  --site yololab.net \
  --optimizations-file example_optimizations.jsonl \
  --dry-run \
  --simulate-only
```

**輸出：** 清單顯示會變更哪些字段，不做實際修改

### 3. 執行更新

```bash
# 第一批：需要確認
python main.py \
  --site yololab.net \
  --optimizations-file seo_optimizations.jsonl \
  --batch-size 50 \
  --require-confirmation

# 後續批次：自動執行
python main.py \
  --site yololab.net \
  --optimizations-file seo_optimizations.jsonl \
  --batch-size 50 \
  --log-level INFO
```

### 4. 監控進度

```bash
# 查看實時日誌
tail -f batch_optimizer.log

# 統計成功
grep "successful_updates" batch_logs/*-result.json | awk -F: '{sum+=$NF} END {print sum}'
```

---

## 工具架構

```
seo-batch-optimizer/
├── snapshot_manager.py      # 版本備份/恢復
├── post_validator.py        # SEO 驗證規則
├── batch_updater.py         # 批量執行引擎
├── wpcom_client.py          # WordPress.com API 包裝
├── main.py                  # 主程式 + CLI
├── architecture.md          # 項目架構設計
├── EXECUTION_GUIDE.md       # 完整執行手冊
├── README.md                # 本文檔
├── example_optimizations.jsonl  # 示例輸入數據
└── batch_logs/              # 批次執行日誌 (自動生成)
```

---

## 核心模塊

### snapshot_manager.py - 版本控制

```python
from snapshot_manager import SnapshotManager

mgr = SnapshotManager()

# 備份單篇
snapshot_id = mgr.create_snapshot(
    post_id=34844,
    post_data={"title": "...", "excerpt": "..."},
    batch_id="batch-001"
)

# 恢復
post_data = mgr.restore_snapshot(snapshot_id)

# 列表
snapshots = mgr.list_snapshots(batch_id="batch-001")
```

### post_validator.py - 驗證規則

| 字段 | 規則 | 最佳 |
|------|------|------|
| Title | 55-65 字 | ~60 |
| Description | 155-165 字 + CTA | ~160 |
| Schema | 合法 JSON-LD | FAQPage |
| Links | ≥2 有效連結 | 3+ |
| Image Alt | 100% 有 Alt | >5 字 |

### batch_updater.py - 執行引擎

```python
from batch_updater import BatchUpdater, BatchUpdate

updater = BatchUpdater(site_name="yololab.net", dry_run=False)

updates = [
    BatchUpdate(post_id=34844, title="新標題", excerpt="新描述")
]

result = updater.execute_batch(updates, require_confirmation=True)
```

---

## 輸入格式

```jsonl
{
  "post_id": 34844,
  "optimizations": {
    "title_options": [
      {"option": 1, "text": "標題", "length": 58}
    ],
    "meta_description": "描述...",
    "internal_links": [
      {"post_id": 123, "anchor": "文字"}
    ],
    "faq_expansion": [
      {"q": "問題?", "a": "答案。"}
    ],
    "image_alts": [
      {"image_id": 456, "alt": "描述"}
    ]
  }
}
```

---

## 命令行

```bash
python main.py \
  --site yololab.net \
  --optimizations-file file.jsonl \
  --dry-run \
  --batch-size 50 \
  --require-confirmation \
  --log-level INFO
```

---

## 驗證規則示例

### Title (55-65 字)

```
✓ "Kodaline 台北告別演唱會 8/24 TICC | 搶票攻略" (58字)
✗ "Kodaline 演唱會" (太短)
✗ "Kodaline 樂團台北國際會議中心演唱會全網搶票..." (太長)
```

### Description (155-165 字 + CTA)

```
✓ "Kodaline 8/24 台北 TICC！15 億點聽〈All I Want〉。4/1 搶票開啟，DBS 卡友搶先購。" (158字, CTA: 搶票)
✗ 無 CTA 的描述不符合規範
```

### Schema (JSON-LD)

```json
✓ {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [{"@type": "Question", "name": "Q?", "acceptedAnswer": {"@type": "Answer", "text": "A."}}]
}

✗ {"@type": "FAQPage"} (缺 mainEntity)
```

---

## 回滾

```python
# 自動：批次全失敗時
[ERROR] All updates failed, rolling back...

# 手動
from snapshot_manager import SnapshotManager
mgr = SnapshotManager()
mgr.restore_batch(batch_id="batch-001")
```

---

## 進度追蹤

```bash
# 已完成批次
ls batch_logs/ | wc -l

# 總成功數
grep "successful_updates" batch_logs/*-result.json | awk -F: '{sum+=$NF} END {print sum}'

# 進度 %
python -c "import glob, json; total = sum(json.load(open(f))['successful_updates'] for f in glob.glob('batch_logs/*-result.json')); print(f'{total}/2700 ({100*total/2700:.1f}%)')"
```

---

## Git 整合

```bash
# 查看 SEO 提交
git log --oneline --grep="chore(seo)"

# 恢復
git revert <commit>
```

---

## 常見問題

**Q: 中斷後能繼續嗎？**
A: 可以，已完成批次不會重複，從下一批繼續。

**Q: 能改驗證規則嗎？**
A: 可以，編輯 `post_validator.py` 的常數。

**Q: 備份多大？**
A: ~10KB/篇，2700 篇 ≈ 27MB (可清理舊備份)。

**Q: 如何驗證更新？**
A: 檢查 `batch_logs/` 結果，查 WordPress.com 統計，運行 404 監控。

---

詳見 [EXECUTION_GUIDE.md](EXECUTION_GUIDE.md)
