# Dev Vault

PARA-style Obsidian 知識庫 + 浮水印移除系統 + 自動化工具集。

## 專案結構

```
src/watermark_removal/   # 浮水印移除核心演算法（Python）
tests/                   # Python 測試（pytest）
test/                    # Node.js 測試（Jest）
docs/                    # 架構文件、計畫、報告
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
