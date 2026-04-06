---
title: Clausidian Quick Reference
type: resource
subtype: reference
status: active
maturity: mature
domain: knowledge-management
created: 2026-04-03
updated: 2026-04-03
summary: Fast reference for Clausidian CLI commands and common workflows
---

# Clausidian 快速參考卡

## 🚀 常用命令

### 日常工作

| 任務 | 命令 |
|------|------|
| **開始工作** | `clausidian journal` |
| **新建筆記** | `clausidian note "Title" project` |
| **快速想法** | `clausidian capture "Idea"` |
| **搜索** | `clausidian search "keyword"` |
| **查看筆記** | `clausidian read <note>` |
| **結束工作** | `clausidian sync` |

### 組織與維護

| 任務 | 命令 |
|------|------|
| **自動連結** | `clausidian link` |
| **健康檢查** | `clausidian health` |
| **統計** | `clausidian stats` |
| **歸檔項目** | `clausidian archive <note>` |
| **重命名** | `clausidian rename <note> "New Title"` |
| **合併筆記** | `clausidian merge <source> <target>` |
| **查找相似** | `clausidian duplicates` |
| **建議優先** | `clausidian focus` |

### 報告與可視化

| 任務 | 命令 |
|------|------|
| **周報** | `clausidian review` |
| **月報** | `clausidian review monthly` |
| **知識圖** | `clausidian graph` |
| **儀表板** | `clausidian daily` |
| **備份** | `clausidian export vault-backup.json` |

---

## 📝 筆記類型

### type 字段值

```yaml
- project:  進行中的工作 (有 goal + deadline)
- area:     長期關注領域 (ai-engineering, dev-environment 等)
- resource: 參考資料或已學習 (需要 subtype)
- idea:     潛在項目或草稿
- journal:  日誌條目 (自動生成)
```

### resource subtype

```yaml
- reference:  工具、庫、概念說明
- research:   持續研究的主題
- catalog:    清單、索引
- config:     組態文檔
- learning:   已解決的問題 (經驗教訓)
- standard:   流程或質量標準
- article:    已發佈的文章
- improvement: 改進建議
```

---

## 🏷️ 推薦標籤架構

### 按域

```
claude-code, knowledge-management, ai-engineering, dev-environment, open-source
```

### 按工作類型

```
feature, bug-fix, refactor, research, documentation, workflow
```

### 按狀態

```
blocked, waiting, in-review, ready-to-ship, learning
```

### 例子

```yaml
# 好的標籤組合
tags: [claude-code, feature, learning]
tags: [ai-engineering, research, prompt-engineering]
tags: [open-source, refactor, documentation]

# 避免過多標籤 (>5 個)
tags: [one, two, three, four, five]  # ⚠️ 太多
```

---

## ⚙️ 環境變數

```bash
# 設置 vault 路徑 (一次)
export OA_VAULT="/c/DEX_data/Claude Code DEV"

# 設置時區 (可選)
export OA_TIMEZONE="Asia/Taipei"

# 永久設置 (加到 .bashrc 或 .zshrc)
echo 'export OA_VAULT="/c/DEX_data/Claude Code DEV"' >> ~/.bashrc
```

---

## 🔄 工作流程模板

### 新項目啟動

```bash
# 1. 建立項目筆記
clausidian note "Project Name" project

# 2. 新增詳情 (手動編輯)
# 添加: goal, deadline, status: active

# 3. 新增相關標籤
# 在文檔中添加適當標籤

# 4. 連結相關資源
# 使用 [[reference-note]] 格式
```

### 每日工作循環

```bash
# 早晨
clausidian journal              # 建立今日日誌
clausidian focus                # 看有什麼要優先處理

# 工作中
clausidian capture "idea"       # 快速記錄
clausidian note "Task" project  # 建立新項目

# 下班
clausidian sync                 # 同步索引
clausidian daily                # 查看今日成果
```

### 周間回顧

```bash
# 周一早晨
clausidian review               # 週回顧
clausidian link --dry-run       # 預覽新連結
clausidian link                 # 執行連結

# 周末
clausidian health               # 健康檢查
# 記錄指標到 VAULT_METRICS.md
```

---

## ⚡ 進階技巧

### 條件查詢

```bash
# 列出 draft 狀態的筆記
clausidian list --status draft

# 列出特定類型
clausidian list --type project

# 按標籤過濾
clausidian list --json | jq '.notes[] | select(.tags[] | contains("claude-code"))'
```

### 批量操作

```bash
# 批量重命名標籤
clausidian tag rename old-tag new-tag

# 導出特定篩選
clausidian export vault-backup.json --type project

# 日誌中導出
clausidian list --json > notes.json
```

### 圖形可視化

```bash
# 生成 Mermaid 知識圖
clausidian graph > graph.md

# 在 Obsidian 中查看 (支持 Mermaid 插件)
```

---

## 🆘 常見問題

### Q: 孤立筆記怎麼辦?

A: 執行 `clausidian link` 自動連結，或手動添加相關筆記連結 `[[note]]`

### Q: 如何刪除筆記?

A: 改用 `clausidian archive <note>` 而非刪除

### Q: 如何合併重複筆記?

A: `clausidian merge <source> <target>` (將 source 內容合到 target)

### Q: 健康評分低怎麼辦?

A: 參考 VAULT_MAINTENANCE.md 的修復步驟

---

## 📚 完整文檔

- **[VAULT_MAINTENANCE.md](VAULT_MAINTENANCE.md)** — 維護計劃和自動化
- **[MAINTENANCE_SETUP.md](MAINTENANCE_SETUP.md)** — 設置定時任務
- **[CONVENTIONS.md](CONVENTIONS.md)** — 元數據標準
- **[AGENT.md](AGENT.md)** — 完整 CLI 命令列表

---

**更新時間:** 2026-04-03
**使用技巧:** 將此文件加入書籤以快速查詢
