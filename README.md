# Dev Vault

PARA-style Obsidian 知識庫 + 浮水印移除系統 + 自動化工具集。

## 快速開始

```bash
# 查看配置與設置
cat QUICK_START_SYSTEM.md    # 系統快速開始
cat CLAUDE.md                # 專案概覽

# 開始工作
clausidian journal           # 創建日誌
npm test                     # 運行測試
pytest tests/ -v             # 運行 Python 測試
```

## 專案結構

```
src/watermark_removal/   # 浮水印移除核心演算法（Python）
tests/                   # Python 測試（pytest）
test/                    # Node.js 測試（Jest）
docs/                    # 📚 文檔（CONFIG.md、TROUBLESHOOT.md、ARCHITECTURE.md）
  └── archive/           # 📦 歷史報告與完成的 Phase（74 個文件）
scripts/                 # 執行腳本（benchmark、Label Studio、Optuna）
config/                  # YAML 組態檔
projects/                # YOLO LAB 網站優化
workflows/               # ComfyUI workflow JSON
areas/                   # PARA — 長期關注領域
resources/               # PARA — 參考資料
templates/               # Obsidian 筆記模板
ideas/                   # 草稿想法
journal/                 # 每日日誌與週回顧
.claude/                 # Claude Code slash commands
```

## 技術棧

**Python** — OpenCV, NumPy, Optuna, scikit-image, aiohttp, pytest  
**Node.js** — Anthropic SDK, Octokit (GitHub API), Jest  
**外部** — FFmpeg, Docker, ComfyUI

## 快速開始

### Python（浮水印移除）

```bash
python -m venv .venv
.venv/Scripts/activate  # Windows
pip install -r requirements.txt
pytest tests/
```

### Node.js（知識管理自動化）

```bash
npm install
npm test
```

## 文件

- [架構文件](docs/ARCHITECTURE.md)
- [Phase 完成報告](docs/reports/)
- [計畫文件](docs/plans/)

## License

MIT
