---
title: "PARA+ZK 整合可以用 metadata overlay 實現，不需重建目錄"
type: inbox
note_class: fleeting
tags: [knowledge-management, vault-design]
created: "2026-04-06"
updated: "2026-04-06"
status: active
summary: "ZK 層不需要新目錄，note_class 欄位就夠了——PARA 做位置，ZK 做概念分類"
source: "journal/2026-04-06.md"
---

# PARA+ZK 整合可以用 metadata overlay 實現，不需重建目錄

整合 PARA 和 Zettelkasten 時，常見錯誤是替 ZK 建新目錄（`/zettelkasten/`、`/permanent/`）
導致與 PARA 結構打架。

關鍵洞見：ZK 的角色是**概念層**，不是**位置層**。
只要在 frontmatter 加 `note_class` 欄位，Bases/Dataview 就能用 ZK 邏輯查詢，
而 PARA 繼續負責「這個檔案住在哪裡」。

兩個系統正交，互不干涉。

## Process Next

- [x] 擴展為 literature note? → 不需要，無外部來源
- [x] 蒸餾為 permanent note? → [[202604061430-para-zk-are-orthogonal-layers]]
- [ ] Route to project?
- [ ] Discard?
