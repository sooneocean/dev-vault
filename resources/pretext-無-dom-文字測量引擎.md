---
title: "Pretext — 無 DOM 文字測量引擎"
type: resource
tags: [typescript, text-layout, performance]
created: "2026-03-29"
updated: "2026-03-30"
status: active
subtype: reference
maturity: seed
domain: project-specific
summary: "chenglou/pretext：兩階段架構（prepare + layout），用 Canvas measureText 取代 DOM reflow，sub-μs 熱路徑"
source: ""
related: []
---

# Pretext — 無 DOM 文字測量引擎

## 基本資訊

- **Repo**: [chenglou/pretext](https://github.com/chenglou/pretext)
- **NPM**: `@chenglou/pretext` (v0.0.2, 2026-03-28)
- **License**: MIT | **Stars**: ~4,760 | **Language**: TypeScript
- **Dependencies**: 零（只有 typescript peer dep）
- **作者**: Cheng Lou（ReasonML 核心、React Motion、BuckleScript/ReScript）

## 解決什麼問題

UI 元件各自用 DOM 讀取（`getBoundingClientRect`、`offsetHeight`）測量文字高度時，讀寫交錯會觸發**同步 layout reflow**（layout thrashing）。500 個文字區塊可能每幀耗 30ms+。

Pretext 完全移除熱路徑上的 DOM 讀取——`prepare()` 做一次性 Canvas 測量，之後 `layout()` 是**純算術**，零 DOM、零 Canvas、零字串操作、零分配。

## 兩階段架構

### Phase 1: `prepare(text, font, options?)` (~0.038ms/text)

1. 依 CSS `white-space` 規則正規化空白
2. `Intl.Segmenter({ granularity: "word" })` 分詞（支援 CJK、Thai、Arabic、Myanmar）
3. 標點合併至前詞（"better." 視為一個單位）
4. CJK 字詞拆成單一 grapheme（逐字換行，匹配瀏覽器行為）
5. 禁則處理（kinsoku shori）：行首/行尾禁止字元合併
6. URL 與數字序列合併為不可拆單位
7. `Canvas measureText()` 測量每段（優先用 `OffscreenCanvas`）
8. 長詞預測量 grapheme 寬度（`overflow-wrap: break-word` 用）
9. Emoji 膨脹修正（Chrome/Firefox macOS 在 <24px 時 Canvas 比 DOM 寬）
10. 簡化 bidi 等級計算（基於 pdf.js）
11. 回傳不透明 `PreparedText` handle（平行陣列：寬度、斷行類型、grapheme 寬度）

### Phase 2: `layout(prepared, maxWidth, lineHeight)` (~0.0002ms/text)

- 走訪預計算的寬度陣列，純整數/浮點算術
- 回傳 `{ height, lineCount }`
- **無 Canvas、無 DOM、無字串操作、無記憶體分配**

## API 總覽

| 函式 | 用途 |
|------|------|
| `prepare(text, font, opts?)` | 一次性分析 + 測量 → 不透明 handle |
| `layout(prepared, maxWidth, lineHeight)` | 純算術行數計算（熱路徑）|
| `prepareWithSegments(text, font, opts?)` | 同 prepare 但暴露 segments[] |
| `layoutWithLines(prepared, maxWidth, lineHeight)` | 回傳每行內容和寬度 |
| `walkLineRanges(prepared, maxWidth, onLine)` | 非物化行走訪（shrinkwrap 用）|
| `layoutNextLine(prepared, start, maxWidth)` | 逐行迭代（每行不同寬度）|
| `clearCache()` | 釋放內部快取 |
| `setLocale(locale?)` | 設定未來 prepare 的 locale |

## 關鍵設計決策

### CJK
- CJK 字詞拆成單一 grapheme（逐字換行）
- 禁則處理：`、。）` 等行首禁止字元與前段合併，`（「` 等行尾禁止字元與後段合併
- Chromium vs Safari 的收束引號 + CJK carry 規則差異，透過引擎偵測處理

### Emoji
- Chrome/Firefox macOS 在 <24px 時 emoji Canvas 測量比 DOM 寬
- 自動偵測：每 font 做一次 `span.getBoundingClientRect()`，結果快取
- Safari 無此問題

### 為何避免 `system-ui`
macOS 在小字級用 SF Pro Text、大字級用 SF Pro Display，Canvas 和 DOM 切換閾值不同，導致最高 14.5% 寬度偏差。指名字體（Inter、Helvetica 等）不受影響。

### 瀏覽器引擎 Profile
- **Safari**: 較大 epsilon (1/64)，使用前綴寬度
- **Chromium/Firefox**: 小 epsilon (0.005)，carry CJK

## 效能

| 操作 | 500 text batch | 單次 |
|------|---------------|------|
| `prepare()` | ~19ms | ~0.038ms |
| `layout()` | ~0.09ms | ~0.0002ms |

快的原因：
1. 準備/佈局兩階段分離
2. 平行陣列（cache-friendly）取代物件嵌套
3. 多層快取（segment metrics、emoji 修正、Segmenter 實例）
4. 快速路徑偵測（無特殊段時簡化 walker）
5. `layout()` 零分配

## 使用場景

1. **Virtual list / occlusion** — 渲染前就知道精確行高
2. **Canvas / SVG / WebGL 文字渲染** — `layoutWithLines()` 給每行內容和寬度
3. **文字環繞浮動元素** — `layoutNextLine()` 支援每行不同寬度
4. **Masonry / 自訂佈局** — 免 DOM 計算千張卡片高度
5. **Layout shift 防止** — 插入 DOM 前預知高度
6. **Shrinkwrap / 平衡文字** — `walkLineRanges()` 二分搜尋最窄容器
7. **Textarea 自動高度** — `pre-wrap` 模式預測高度

## 競品比較

| Library | 方式 | 差異 |
|---------|------|------|
| opentype.js | 完整字體解析器 | 重；解析 .otf/.ttf；不依賴瀏覽器引擎 |
| fontkit | 字體解析（pdfkit 用）| 類似 opentype.js |
| canvas-txt | Canvas 文字渲染+換行 | 簡單；無 i18n/bidi/emoji |
| harfbuzz (wasm) | 文字整形引擎 | glyph 層級；互補而非競爭 |
| CSS `text-wrap: balance` | 瀏覽器原生 | 只平衡；不給高度；無法在 DOM 外用 |

**Pretext 獨特定位**：委託瀏覽器字體引擎（Canvas measureText）做整形，自己實作行佈局邏輯。瀏覽器準確度 + 零 DOM reflow。

## 安裝

```bash
npm install @chenglou/pretext
```

## 何時用

任何 JS/TS 專案需要在**不觸發 DOM reflow** 的情況下測量多行文字尺寸時。特別適合：
- 高效能 virtual list
- Canvas/WebGL 文字渲染
- 自訂佈局引擎
- 需要防止 layout shift 的場景

