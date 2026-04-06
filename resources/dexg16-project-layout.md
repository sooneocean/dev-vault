---
title: "DEXG16 專案目錄結構"
type: resource
tags: [workspace, reference, knowledge-management]
created: "2026-03-28"
updated: "2026-04-03"
status: active
subtype: catalog
maturity: mature
domain: dev-environment
summary: "工作目錄配置 — DEX_data 分區、Projects 資料夾、主要 Repo"
source: ""
related: ["[[dexg16-ai-stack]]", "[[dexg16-dev-environment]]", "[[dexg16-machine-specs]]", "[[dexg16-all-projects-catalog]]", "[[github-全部-repo-清單]]"]
---

# DEXG16 專案目錄結構

## 重點

### 主要工作目錄

```
C:\DEX_data\                          # 主資料分區
├── Claude Code DEV\                  # 🔸 目前 Vault + CSM 開發區
│   └── projects\tools\
│       ├── claude-session-manager\   # CSM 原版
│       └── claude-session-manager-new\ # CSM 重構版
├── _AI\                              # AI/ML 專案
│   ├── COMFYUI\                      # Stable Diffusion 工作流
│   ├── BasicSR\, SUPIR\             # 超解析度
│   ├── IOPaint\, INpaint-web\       # 圖片修補
│   ├── YOLOLAB\                     # 物件偵測
│   └── Gausian_native_editor\       # 3D 高斯編輯
├── _Dev\                             # 開發工具與實驗
│   ├── claude-session-manager\      # CSM（另一份副本）
│   ├── OpenDEX\                     # DEX 平台
│   ├── CodeWhisper\                 # 程式碼工具
│   ├── Oh My OpenCode\             # OpenCode 分支
│   ├── Planning-with-files\        # 規劃工具
│   ├── PowerToys\                  # MS PowerToys
│   ├── moltbot\                    # 機器人專案
│   └── clean\, iclean\            # 清理工具
├── _Events\                         # 活動資料
├── _Media\                          # 多媒體檔案
├── _Notes\                          # 筆記存檔
└── _Projects\                       # 活躍產品
    ├── AionUI\                      # UI 框架
    └── VIBE KANBAN\                 # 看板工具

C:\Users\User\Projects\              # 次要專案資料夾
├── ALI_DeepResearch\                # 深度研究工具
├── chrome-devtools-mcp\             # Chrome DevTools MCP 伺服器
├── comfyui\                         # ComfyUI（另一份副本）
├── firecrawl\                       # 網頁爬取
├── open-lovable\                    # 開源 Lovable 複製版
├── spec-kit\                        # Spec 工具包
└── youtube_dl\                      # YouTube 下載器
```

### 目錄慣例
- `DEX_data/` — 主要工作區，以底線前綴（`_`）分類資料夾
- `Projects/` — 第三方或實驗性專案
- CSM 有三份副本（`Claude Code DEV`、`_Dev`、一份可能已過時）

## 筆記
