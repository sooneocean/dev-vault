---
title: "PARA 和 Zettelkasten 是正交的層：位置 vs 概念"
type: resource
subtype: reference
note_class: permanent
zettel_id: "202604061430"
atomic: true
tags: [knowledge-management, vault-design, para, zettelkasten]
created: "2026-04-06"
updated: "2026-04-06"
status: active
maturity: mature
domain: knowledge-management
summary: "PARA 管位置（檔案住哪裡），ZK 管概念（想法的成熟度）。用 note_class 欄位做 overlay，不需建新目錄。"
related: ["[[areas/knowledge-management]]"]
relation_map: "areas/knowledge-management:documents"
distilled_from: ["inbox/2026-04-06-1430-para-zk-overlay-insight.md"]
agent_written: true
agent_reviewed: true
confidence: "high"
---

# PARA 和 Zettelkasten 是正交的層：位置 vs 概念

PARA 和 Zettelkasten 解決的是不同問題，因此可以疊加而不衝突：

- **PARA** 回答「這個檔案**住在哪裡**？」（位置層）
- **Zettelkasten** 回答「這個想法**成熟到哪裡**？」（概念層）

實作上，不需要為 ZK 建新目錄。只要在 YAML frontmatter 加一個 `note_class` 欄位（`fleeting → literature → permanent`），查詢工具（Obsidian Bases、Dataview）就能用 ZK 邏輯過濾，而 PARA 繼續決定實際路徑。

兩個系統正交，各自完整，互不干涉。

## Evidence

- Vault Spec v1.0 實作驗證：現有 `areas/projects/resources/journal/ideas/` 不動，`note_class` overlay 即可啟用 ZK 查詢
- `resources/permanent/` 子目錄是慣例，不是強制：永久筆記放在 `resources/` 下任何位置都有效

## Implications

- 可以對**既有 vault 漸進式加入 ZK**，不需遷移
- `note_class: permanent` 是 Bases query 的核心 filter，比目錄結構更可靠
- 同一個概念可以從 journal capture → inbox → permanent，路徑改變但 `zettel_id` 不變

## Related

- [[areas/knowledge-management]]
- [[docs/VAULT_SPEC_V1]]
