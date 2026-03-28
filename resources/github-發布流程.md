---
title: "GitHub 發布流程"
type: resource
tags: [github, release, workflow, ci-cd]
created: "2026-03-28"
updated: "2026-03-28"
status: active
summary: "開源專案的標準發布流程 — 版本命名、Release 建立、CHANGELOG 維護"
source: ""
related: ["[[開源開發者身分]]", "[[開源專案品質標準]]", "[[dexg16-git-and-github]]", "[[github-全部-repo-清單]]"]
---

# GitHub 發布流程

## 重點

### 版本命名規範（Semantic Versioning）

遵循 [SemVer](https://semver.org/) 規範：`vMAJOR.MINOR.PATCH`

| 類型 | 何時遞增 | 範例 |
|------|----------|------|
| MAJOR | 有不相容的 API 變更 | v1.0.0 → v2.0.0 |
| MINOR | 新增功能，向下相容 | v1.0.0 → v1.1.0 |
| PATCH | 修復 Bug，向下相容 | v1.0.0 → v1.0.1 |

### 發布前檢查清單

1. **程式碼品質**
   - [ ] 所有測試通過
   - [ ] Linter 無錯誤（ruff / prettier）
   - [ ] 無安全漏洞（secrets、敏感資料）

2. **文件更新**
   - [ ] CHANGELOG.md 更新（列出本次變更）
   - [ ] README.md 版本號更新
   - [ ] 如有 API 變更，文件同步更新

3. **版本標記**
   - [ ] `pyproject.toml` / `package.json` 版本號更新
   - [ ] Git tag 建立：`git tag v0.x.0`

### 標準發布步驟

```bash
# 1. 確認在 main 分支，程式碼乾淨
git checkout main && git pull

# 2. 更新版本號
# Python: pyproject.toml → version = "X.Y.Z"
# Node:   npm version patch/minor/major

# 3. 更新 CHANGELOG.md
# 記錄本次變更重點

# 4. 提交版本變更
git add -A
git commit -m "chore: bump version to vX.Y.Z"

# 5. 建立 Git tag
git tag vX.Y.Z

# 6. 推送程式碼與 tag
git push origin main --tags

# 7. 建立 GitHub Release
gh release create vX.Y.Z --title "vX.Y.Z" --notes-file RELEASE_NOTES.md
```

### CHANGELOG 格式

```markdown
## [vX.Y.Z] - YYYY-MM-DD

### 新增
- 功能描述

### 修復
- Bug 描述

### 變更
- 行為變更描述

### 移除
- 移除項目
```

### Commit 訊息規範

遵循 Conventional Commits：
- `feat:` — 新功能
- `fix:` — Bug 修復
- `refactor:` — 重構（不影響功能）
- `docs:` — 文件變更
- `test:` — 測試相關
- `chore:` — 雜務（版本號、CI 設定等）

### 各語言特定發布

| 語言 | 套件發布平台 | 指令 |
|------|------------|------|
| Python | PyPI | `python -m build && twine upload dist/*` |
| TypeScript/Node | npm | `npm publish` |
| Rust | crates.io | `cargo publish` |

### 相關筆記
- [[開源開發者身分]]
- [[開源專案品質標準]]
- [[dexg16-git-and-github]]

## 筆記
