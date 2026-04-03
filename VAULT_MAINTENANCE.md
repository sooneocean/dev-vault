# Vault 維護計劃

此文檔定義 Clausidian vault 的自動化維護流程。根據分析：孤立笔记 332 個 (87.6%)，96% 为 project，100% 未分配域。

## 🎯 維護目標

| 指標 | 當前 | 目標 | 優先級 |
|------|------|------|--------|
| Vault 健康評分 | 28% (F) | 65% (C) | 🔴 Critical |
| 孤立笔记 | 332 (87.6%) | < 50 (13%) | 🔴 Critical |
| 域分配 | 0% | 100% | 🟠 High |
| 標籤覆蓋 | 1.8% | 80% | 🟠 High |
| 連接性 | 13% | 40% | 🟡 Medium |

---

## 📋 日常任務 (每日)

```bash
# 開始工作日
clausidian journal          # 建立/開啟今日日誌

# 新笔記建立時
clausidian note "Title" project   # 確保分配類型
clausidian tag <new-note> <tag>   # 立即添加標籤

# 結束工作日
clausidian sync             # 重建索引 (確保變更已保存)
```

**檢查清單:**
- [ ] 日誌條目已建立
- [ ] 新笔記已分配至少 1 個標籤
- [ ] 相關笔記已链接 (`[[note]]` 格式)
- [ ] 索引已同步

---

## 📅 周間維護 (每周一)

```bash
# 連結檢測 & 自動連結
clausidian link --dry-run   # 預覽候選連結
clausidian link             # 執行自動連結

# 孤立笔记審查
clausidian list --json | jq '.notes[] | select(.related|length==0) | .title' \
  | head -20                # 列出前 20 個孤立笔记進行手動審查

# 周報生成
clausidian review           # 生成周合成報告
```

**檢查清單:**
- [ ] 自動連結已執行 (至少 5 個新連結)
- [ ] 孤立笔记已審查 (至少 20 個)
- [ ] 周報已生成
- [ ] 新發現的問題已記錄

---

## 📆 月度維護 (每月 1 日)

```bash
# 整體健康檢查
clausidian health           # 生成完整健康報告

# 元數據修復
clausidian list --json | jq '.notes[] | select(.domain=="unassigned") | .title' \
  > orphan_domain_list.txt  # 導出需要域分配的笔记清單

# 批量操作範例
# for note in $(cat orphan_domain_list.txt); do
#   clausidian tag "$note" "ai-engineering"  # 根據內容分配域標籤
# done

# 月度回顧
clausidian review monthly   # 生成月度合成與趨勢分析

# 備份
clausidian export vault-backup-$(date +%Y-%m-%d).json
```

**檢查清單:**
- [ ] 健康評分已記錄 (用於追蹤進度)
- [ ] 域分配策略已確定
- [ ] 至少 50 個無域笔记已分配
- [ ] 月度回顧已完成
- [ ] 備份已建立

---

## 🔧 修復步驟 (優先)

### 問題 1: 缺失域分配 (332 個笔记)

**方案 A: 交互式分配 (高品質，低效率)**
```bash
# 逐個審查並分配
clausidian list --type project --status active | head -20
# 手動查看每個笔记內容，分配適當域:
# - ai-engineering
# - dev-environment
# - knowledge-management
# - open-source
# - project-specific
```

**方案 B: 批量標籤標記 (快速，需驗證)**
```bash
# 使用現有標籤推斷域
# 例: 如果笔记有 "claude-code" 標籤 → "ai-engineering" 域
```

### 問題 2: 無標籤笔记 (326 個)

```bash
# 識別無標籤笔记
clausidian list --json | jq '.notes[] | select(.tags|length==0)' > no_tags.json

# 使用 title + type 推斷標籤
# 示例: "Unit 4 Gospel" (resource) → tags: ["writing", "gospel", "music"]
```

### 問題 3: 孤立笔记 (需要連結)

```bash
# 自動連結已執行，但可能需要手動審查
clausidian duplicates       # 尋找相似笔记進行合併
clausidian link --dry-run   # 檢查候選連結品質
```

---

## 🤖 自動化腳本

### 每日早晨 (Cron: 8:00 AM)

```bash
#!/bin/bash
cd '/c/DEX_data/Claude Code DEV'

# 建立今日日誌
/c/Users/User/AppData/Roaming/npm/clausidian journal

# 提醒檢查新笔记
echo "🔔 Daily reminder: Check for new orphan notes"
/c/Users/User/AppData/Roaming/npm/clausidian list --json | \
  jq '.notes[] | select(.created=="'$(date +%Y-%m-%d)'")' | \
  jq '.title' | head -5
```

### 每周一 10:00 AM (Cron: 0 10 * * 1)

```bash
#!/bin/bash
cd '/c/DEX_data/Claude Code DEV'

# 自動連結
/c/Users/User/AppData/Roaming/npm/clausidian link

# 重建索引
/c/Users/User/AppData/Roaming/npm/clausidian sync

# 生成周報並保存
/c/Users/User/AppData/Roaming/npm/clausidian review > \
  "weekly_review_$(date +%Y-W%V).txt"

# 提醒孤立笔记審查
echo "📋 Orphan notes to review:"
/c/Users/User/AppData/Roaming/npm/clausidian list --json | \
  jq '.notes[] | select(.related|length==0) | .title' | wc -l
```

### 每月 1 日 9:00 AM (Cron: 0 9 1 * *)

```bash
#!/bin/bash
cd '/c/DEX_data/Claude Code DEV'

# 完整健康檢查
echo "📊 Monthly Health Report"
/c/Users/User/AppData/Roaming/npm/clausidian health

# 備份
/c/Users/User/AppData/Roaming/npm/clausidian export \
  "backups/vault_$(date +%Y-%m-%d).json"

# 月度回顧
/c/Users/User/AppData/Roaming/npm/clausidian review monthly > \
  "monthly_review_$(date +%Y-%m).txt"
```

---

## 📊 追蹤指標

建立 `VAULT_METRICS.md` 記錄進度:

| 日期 | 健康評分 | 孤立笔记 | 域覆蓋 | 標籤覆蓋 | 連接性 |
|------|---------|---------|--------|---------|--------|
| 2026-04-03 | 28% | 332 (87.6%) | 0% | 1.8% | 13% |
| 2026-04-10 | — | — | — | — | — |
| 2026-04-17 | — | — | — | — | — |

---

## 🚀 改善里程碑

### Phase 1: 基礎清理 (4 周)
- [ ] 所有 326 個無標籤笔記已分配至少 1 個標籤
- [ ] 所有 332 個笔记已分配域
- [ ] Vault 健康評分 → 40%

### Phase 2: 連接優化 (4 周)
- [ ] 孤立笔记數量 → < 100
- [ ] 連接性 → 30%+
- [ ] Vault 健康評分 → 50%

### Phase 3: 成熟度提升 (4 周)
- [ ] 內容完整性 → 70%+
- [ ] 新鮮度 → 40%+
- [ ] Vault 健康評分 → 65% (目標)

---

## 📚 參考資源

- CONVENTIONS.md — 元數據標準
- AGENT.md — Clausidian CLI 命令
- CLAUDE.md — 開發工作流程

---

**Last Updated:** 2026-04-03
**Next Review:** 2026-04-10
**Owner:** sooneocean
