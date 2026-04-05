---
title: Unit 2.2 快速實施指南：內部連結部署
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-03
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

# Unit 2.2 快速實施指南：內部連結部署

## ⚡ 5 分鐘快速上手

### 任務概要
為 TOP 50 文章添加內部連結，達成目標：
- ✅ TOP 50 每篇 ≥ 5 個內部連結
- ✅ 同分類互連率 ≥ 60%
- ✅ 所有連結有效且相關

### 文件清單
- `Unit2.2-Internal-Linking-Strategy.md` — 完整戰略（14KB，讀時 15 分鐘）
- `Unit2.2-TOP50-ArticleMapping.csv` — 文章清單（50 篇，ID + URL）
- `Unit2.1-Clustering-Topology.csv` — 聚集拓撲（45 個連結映射）

---

## 🎯 核心任務優先級

### P0（最高優先級）— 今天執行
**8 篇文章，每篇 4-5 個連結，耗時 6-8 小時**

| 文章 ID | 標題簡寫 | 分類 | 連結數 | 備註 |
|---------|---------|------|-------|------|
| 34942 | Kanye West | 音樂 | 5 | 需反向連到支柱頁 + 3 個同類 |
| 34935 | Central Cee | 音樂 | 4 | 需反向連到支柱頁 + 3 個同類 |
| 34899 | NO GOOD | 電影 | 4 | 需反向連到支柱頁 + 3 個同類 |
| 34893 | Sarah Chen | 音樂 | 3 | 需反向連到支柱頁 + 2 個同類 |
| 34888 | 誠品電影院 | 電影 | 3 | 需反向連到支柱頁 + 2 個同類 |
| 34881 | AI IDE | 科技 | 5 | 需反向連到支柱頁 + 4 個同類 |
| 34870 | Moto 極速 | 電影 | 4 | 需反向連到支柱頁 + 3 個同類 |
| 34853 | OpenAI 算力 | 科技 | 4 | 需反向連到支柱頁 + 3 個同類 |

**P0 小計**：32 個內部連結，最高優先級

---

### P1（中等優先級）— Day 2 執行
**15 篇文章，每篇 3-4 個連結，耗時 5-6 小時**

音樂分類：
- 34848：拍謝少年 x PEDRO (3 個)
- 34844：Kodaline 告別 (3 個)
- 34836：秀集團 (3 個)
- 34816：南穎 Fiona (3 個)
- 34809：高流爵對 (3 個)
- 34794：JOYCE (3 個)
- 34778：LITTLE JOHN (3 個)
- 34724：aDAN 薛詒丹 (3 個)
- 34702：Organik 祭 (3 個)
- 34691：誠品台語情歌 (3 個)

電影分類：
- 34831：寒戰 1994 (3 個)
- 34826：鼠一般的你 (3 個)
- 34821：高菊花傳奇 (3 個)
- 34804：愛在每一天 (3 個)
- 34788：死亡賭局 (3 個)

科技分類：
- 34666：OpenClaw 龍蝦 (3 個)

---

### P2（低優先級）— Day 3-4 執行
**20 篇文章，每篇 2-3 個連結，耗時 4-5 小時**

包括各分類的 P2 文章，優先級較低但仍需覆蓋。

---

## 📋 實施步驟

### Step 1：準備階段（30 分鐘）

```bash
# 1. 確認 3 個支柱頁已發佈
□ 音樂支柱頁已發佈：https://yololab.net/archives/music-pillar
□ 電影支柱頁已發佈：https://yololab.net/archives/film-pillar
□ 科技支柱頁已發佈：https://yololab.net/archives/tech-pillar

# 2. 打開 WordPress 編輯器
□ 進入 WordPress 後台
□ 準備好 2 個視窗：左邊編輯文章，右邊查看聚集拓撲 CSV
□ 測試一篇文章的內部連結編輯流程
```

### Step 2：編輯 P0 第 1 篇文章（Kanye West）

```markdown
**目標**：添加 5 個內部連結
- 1 個反向連到支柱頁
- 3 個連到同分類文章（Yohee、Jacob Collier、Central Cee）
- 1 個連到教育內容（Hip-Hop 歷史）

**操作流程**：
1. 打開 Kanye West 文章編輯頁面
2. 在「製作理念」段落，選擇「Jacob Collier」詞語
3. 點 Ctrl+K（或工具欄連結按鈕）
4. 輸入：https://yololab.net/archives/jacob-collier
5. 設置「在新視窗打開」（可選）
6. 重複此步驟 4 次
7. 最後一個連結：在結論段落添加「查看樂評評測完整指南」連回支柱頁
8. 更新文章
```

**耗時**：8-10 分鐘 per 文章

### Step 3：批量編輯（P0 所有文章）

```
Day 1 上午（2 小時）：編輯 Kanye West、Central Cee、Sarah Chen、NO GOOD
Day 1 下午（2 小時）：編輯誠品電影院、Moto 極速、AI IDE、OpenAI 算力
Day 2 上午（1 小時）：驗證 8 篇 P0 文章的連結有效性
```

### Step 4：編輯 P1 文章（Day 2-3）

```
重複 Step 2-3 的流程，但每篇只需 3-4 個連結
預期耗時：4-5 小時
```

### Step 5：驗證與報告（Day 4）

```
□ 隨機抽查 10 篇文章，檢查所有連結有效性（無 404）
□ 計算同分類互連率
□ 生成最終報告 CSV
□ 更新 Google Search Console（自動抓取）
```

---

## 🔗 內部連結錨文本範本

### 反向連結到支柱頁（Priority: 最高）

**音樂分類**：
```markdown
[查看 YOLO LAB 樂評評測完整指南](https://yololab.net/archives/music-pillar)
[樂評評測完整分析](https://yololab.net/archives/music-pillar)
[更多樂評分析](https://yololab.net/archives/music-pillar)
```

**電影分類**：
```markdown
[電影評測完整指南](https://yololab.net/archives/film-pillar)
[更多電影分析](https://yololab.net/archives/film-pillar)
[電影評論完整檔案](https://yololab.net/archives/film-pillar)
```

**科技分類**：
```markdown
[AI 工具評測完整指南](https://yololab.net/archives/tech-pillar)
[科技分析完整檔案](https://yololab.net/archives/tech-pillar)
[更多 AI 工具評測](https://yololab.net/archives/tech-pillar)
```

### 同分類相關連結

**音樂內部連結**：
```markdown
[Yohee 樂評](https://yololab.net/archives/yohee-if-i-were-a-player-diss-track-review)
[Jacob Collier 編曲分析](https://yololab.net/archives/jacob-collier)
[台灣嘻哈藝人地圖](https://yololab.net/archives/taiwan-hiphop-artists)
```

**電影內部連結**：
```markdown
[NO GOOD 評測](https://yololab.net/archives/no-good-ogs-movie-review-christopher-lee-mark-lee)
[李銘順電影專題](https://yololab.net/archives/actor-li-ming-shun)
[動作美學分析](https://yololab.net/archives/action-film-aesthetics)
```

---

## ⚠️ 常見陷阱與避免方法

| 陷阱 | 症狀 | 解決方案 |
|------|------|--------|
| **過度優化** | 所有錨文本都是「點擊樂評」 | 使用 3-5 種不同的錨文本變體 |
| **無關連結** | 連到完全無關的文章 | 參考聚集拓撲 CSV，只連相關文章 |
| **破損連結** | 目標文章不存在 | 先驗證目標文章的 URL 是否有效 |
| **連結過多** | 一篇文章有 10+ 個連結 | 每篇 TOP 5 個為上限，保持可讀性 |
| **連結位置不當** | 全部在最後一段 | 分散在正文、中段、結論各一個 |

---

## 📊 進度追蹤

### 每日檢查清單

```
Day 1：
□ P0 - Kanye West ✓
□ P0 - Central Cee ✓
□ P0 - Sarah Chen ✓
□ P0 - NO GOOD ✓

Day 2：
□ P0 - 誠品電影院 ✓
□ P0 - Moto 極速 ✓
□ P0 - AI IDE ✓
□ P0 - OpenAI 算力 ✓
□ 驗證 P0 所有文章 ✓

Day 3-4：
□ P1 所有 15 篇 ✓
□ 連結有效性檢查 ✓

Day 5：
□ P2 所有 20 篇 ✓
□ 最終驗證與報告 ✓
```

---

## 🎯 成功指標

| 指標 | 目標 | 達成 |
|------|------|------|
| **TOP 8 P0 文章** | 每篇 ≥ 4-5 個連結 | □ |
| **P1 文章** | 每篇 ≥ 3 個連結 | □ |
| **連結有效性** | 0 個 404 或損壞連結 | □ |
| **同分類互連率** | ≥ 60% | □ |
| **錨文本多樣性** | ≥ 3 種不同錨文本 | □ |

---

## 💡 快速決策樹

```
我現在要編輯 Yohee 文章...

1. 是否是 P0 文章？ → YES
2. 需要幾個連結？ → 5 個
3. 連結來源？
   - 1 個反向到支柱頁（結論段）
   - 2 個到同類藝人（Kanye、Central Cee）
   - 1 個到教育內容（嘻哈歷史）
   - 1 個到相關主題（台灣嘻哈）
4. 開始編輯！
```

---

## 📞 需要幫助？

- **不確定某個文章的連結目標？** → 參考 `Unit2.1-Clustering-Topology.csv`
- **不確定錨文本怎麼寫？** → 參考本文的「錨文本範本」section
- **找不到目標文章的 URL？** → 參考 `Unit2.2-TOP50-ArticleMapping.csv` 的 URL 列
- **連結已經添加但要驗證？** → 用 Screaming Frog 或「Broken Link Checker」外掛

---

## 📈 預期成果

**完成後**：
- 50 篇 TOP 文章已添加內部連結
- 支柱頁與文章形成聚集網絡
- 同分類文章相互強化
- 準備進入 Unit 2.3（內容缺口分析）

**預計耗時**：12-16 小時（包括驗證）

---

*準備好開始？打開 WordPress 後台，從 Kanye West 文章開始！*
