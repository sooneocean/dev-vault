---
title: "DEXG16 Git 與 GitHub 設定"
type: resource
tags: [github]
created: "2026-03-28"
updated: "2026-03-30"
status: active
subtype: catalog
maturity: mature
domain: dev-environment
summary: "Git 設定、GitHub 帳號（sooneocean）、SSH 金鑰、delta 分頁器"
source: ""
related: ["[[dexg16-all-projects-catalog]]", "[[csm-feature-roadmap]]", "[[claude-code-configuration]]", "[[dexg16-ai-coding-tools]]", "[[dexg16-ai-stack]]", "[[開源開發者身分]]", "[[github-發布流程]]", "[[github-全部-repo-清單]]"]
---

# DEXG16 Git 與 GitHub 設定

## 重點

### GitHub 身分
- **使用者名稱：** sooneocean
- **Email：** 17285728+sooneocean@users.noreply.github.com（noreply）
- **認證方式：** GitHub CLI（`gh auth git-credential`）
- **SSH 金鑰：** Ed25519（`~/.ssh/id_ed25519`）

### Git 設定
```ini
[core]
  pager = delta
  preloadindex = true
  fscache = true

[interactive]
  diffFilter = delta --color-only

[delta]
  navigate = true
  dark = true
  line-numbers = true
  side-by-side = true

[merge]
  conflictStyle = diff3

[diff]
  colorMoved = default
```

### 值得注意的設定
- 使用 **delta** 作為分頁器 — 並排顯示 diff，附行號
- `fscache = true` — 針對 Windows 優化的 Git 效能
- 認證透過 `gh` CLI 處理（涵蓋 github.com 與 gist.github.com）
- 合併衝突風格：**diff3**（顯示基底版 + 我方 + 對方）

### Ollama 雲端模型
| 模型 | ID | 備註 |
|------|-----|------|
| minimax-m2.5:cloud | c0d5751c800f | 雲端託管 |
| kimi-k2.5:cloud | 6d1c3246c608 | 雲端託管 |
- 目前無本機下載的模型（使用雲端端點）

### 相關筆記
- [[dexg16-dev-environment]]
- [[claude-code-configuration]]

## 筆記
