---
title: Unit 2.3 補充文章選題 — Phase 2 執行清單
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-03
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

# Unit 2.3 補充文章選題 — Phase 2 執行清單

**生成時間**：2026-04-03 12:01
**目標**：新增 12 篇文章，達成 TOP 62 聚集網絡
**預計耗時**：6-8 小時（批量生成 + 優化）

---

## 🎯 新增文章清單 — 按優先級排序

### **優先級 P3：Tech（5 篇）— 最急迫**

#### 1️⃣ LLM 模型完整對比 2026

**基本信息**
- **類別**：Tech
- **支柱頁**：tech-pillar
- **SEO 目標 KW**：LLM 模型對比、GPT-4 vs Claude、大語言模型選擇
- **預期字數**：3,500-4,000 字
- **內部連結目標**：3-4 條
  - → AI IDE（34881）
  - → OpenAI 算力（34853）
  - → tech-pillar

**內容大綱**
```
[開場] 2026 LLM 戰國時代
- GPT-4o（OpenAI）：成本、速度、推理能力
- Claude 3.5 Opus（Anthropic）：安全性、編程能力、長文本
- Gemini 2.0（Google）：多模態、搜尋整合、定價
- Llama 3.1（Meta）：開源、自部署、社區支持
- Qwen（阿里）：中文優化、成本優勢

[對標表] 性能 × 成本 × 延遲 × 上下文窗口
[應用場景] 編程助手、內容生成、數據分析、智能體
[結論] 2026 如何選型
```

**SEO 優化**
- Meta：「2026年LLM模型全面對比：性能、成本、速度完整評測。GPT-4o vs Claude 3.5 Opus vs Gemini 2.0最新對比。」
- Title：「LLM模型完整對比2026｜GPT-4o vs Claude vs Gemini vs Llama最強評測」（60字）
- Schema：FAQSchema（5個常見問題）

---

#### 2️⃣ 提示詞工程完全指南

**基本信息**
- **類別**：Tech
- **支柱頁**：tech-pillar
- **SEO 目標 KW**：提示詞工程、Prompt Engineering、ChatGPT 使用技巧
- **預期字數**：3,500 字
- **內部連結**：3 條
  - → AI IDE（34881）
  - → OpenClaw 龍蝦（34666）
  - → tech-pillar

**內容大綱**
```
[基礎層] 為什麼好的 Prompt 很重要？
- Token 成本差異分析
- 質量差異（好 prompt vs 爛 prompt 案例對比）

[進階技巧]
- Chain-of-Thought（步驟分解）
- Few-Shot Learning（示例驅動）
- Role-Based Prompting（角色扮演）
- System Prompt 設計
- Temperature/Top-P 參數調優

[實戰場景]
- 編程任務的 prompt 設計
- 內容生成的 prompt 框架
- 數據分析的查詢結構化

[工具生態]
- LangSmith（提示詞版本控制）
- PromptFoo（自動化評測）
- Cursor 的 prompt 優化

[案例研究] 3 個真實高效 prompt
```

**SEO 優化**
- Meta：「提示詞工程完全指南：Chain-of-Thought、Few-Shot、角色扮演等10大技巧。讓ChatGPT和Claude輸出品質翻倍的終極秘籍。」
- Schema：HowToSchema

---

#### 3️⃣ AI 智能體框架完全對比

**基本信息**
- **類別**：Tech
- **支柱頁**：tech-pillar
- **SEO 目標 KW**：AI Agent、智能體、AutoGPT vs LangGraph
- **預期字數**：3,000 字
- **內部連結**：3 條
  - → OpenClaw 龍蝦（34666）
  - → CLI for AI Agents（34647）
  - → tech-pillar

**內容大綱**
```
[什麼是 AI Agent？]
- 智能體 vs 聊天機器人的本質差異
- 為什麼 2026 Agent 大爆發？

[框架對比]
- LangGraph（LangChain 生態）
  - 圖狀工作流
  - 內建工具呼叫
  - 記憶管理

- Claude SDK（Anthropic 官方）
  - 原生支援工具使用
  - 可靠性更高
  - 上下文窗口優勢

- AutoGPT / AgentGPT（開源生態）
  - 社區驅動
  - 自部署
  - 造價低

[工作流設計模式]
- ReAct（Reasoning + Acting）
- Plan-Execute-Verify
- Tool-Use Chain

[成本與延遲分析]

[案例：構建一個簡單 Agent]
```

**SEO 優化**
- Meta：「AI智能體完全對比：LangGraph vs Claude SDK vs AutoGPT。2026最強Agent框架選型指南。」
- Schema：ComparisonSchema

---

#### 4️⃣ 向量數據庫選型指南

**基本信息**
- **類別**：Tech
- **支柱頁**：tech-pillar
- **SEO 目標 KW**：向量數據庫、Embedding、RAG、Pinecone vs Weaviate
- **預期字數**：2,800 字
- **內部連結**：2-3 條
  - → AI IDE（34881）
  - → tech-pillar

**內容大綱**
```
[為什麼需要向量數據庫？]
- Embedding 的本質
- 傳統數據庫無法做什麼

[主流方案對比]
- Pinecone（託管，最簡單）
  - 成本：$0.04/100k 向量
  - 優勢：無需運維

- Weaviate（開源，最彈性）
  - 成本：自部署無額外費用
  - 優勢：完全掌控

- Milvus（開源，性能最強）
  - 成本：自部署
  - 優勢：大規模擴展

- Qdrant（新興，相對平衡）
  - 優勢：過濾能力強

[選型決策樹]
- 預算 < $1000/月？→ Weaviate 自部署
- 需要託管？→ Pinecone
- 大規模？→ Milvus
- 需要向量過濾？→ Qdrant

[集成案例]
- 與 LangChain 整合
- 與 Claude API 整合

[成本計算器]
```

**SEO 優化**
- Meta：「向量數據庫完整選型指南：Pinecone vs Weaviate vs Milvus成本對比。RAG系統最佳實踐。」

---

#### 5️⃣ AI 編程助手工作流優化指南

**基本信息**
- **類別**：Tech
- **支柱頁**：tech-pillar
- **SEO 目標 KW**：GitHub Copilot、Claude Code、AI 編程、程式開發效率
- **預期字數**：3,000 字
- **內部連結**：3-4 條
  - → AI IDE（34881）
  - → CLI for AI Agents（34647）
  - → OpenClaw 龍蝦（34666）
  - → tech-pillar

**內容大綱**
```
[2026 AI 編程助手格局]
- GitHub Copilot X（多模態，上下文深）
- Claude Code（長文本，推理能力強）
- Cursor（IDE 整合最佳）
- JetBrains AI Assistant

[工作流優化框架]
1️⃣ 需求解析
   - 用自然語言描述需求，不寫偽代碼
   - 讓 AI 理解上下文（路由不該在這裡）

2️⃣ 架構討論
   - 先設計，不是先代碼
   - 讓 AI 批評你的架構

3️⃣ 迭代循環
   - 部份替換 > 全量重寫
   - 自動化測試 > 手動驗證

[高效 Prompt 模板]
- 代碼審查 prompt
- 性能優化 prompt
- 重構 prompt
- 測試生成 prompt

[陷阱與最佳實踐]
- ❌ 盲目相信 AI 的代碼
- ✅ 自己驗證邏輯，讓 AI 寫細節

[成本效益分析]
- 時間省約 40-60%（根據任務類型）
- 付費方案 vs 免費方案的選擇

[團隊採用策略]
```

**SEO 優化**
- Meta：「AI編程助手工作流完整優化指南：GitHub Copilot vs Claude Code vs Cursor效率對比。程式開發提效40%的終極秘籍。」
- Schema：HowToSchema + FAQSchema

---

### **優先級 P4：Music（3 篇）**

#### 6️⃣ 台灣民謠新浪潮 — 90 後獨立樂手

- **類別**：Music
- **SEO KW**：台灣獨立樂手、民謠、新世代音樂
- **字數**：2,800 字
- **內部連結**：3 條（Yohee、Sarah Chen、music-pillar）

---

#### 7️⃣ 電子音樂製作完全入門

- **類別**：Music
- **SEO KW**：電子音樂製作、合成器、DAW、音樂製作教學
- **字數**：3,500 字
- **內部連結**：3 條（Organik Festival、Yohee、music-pillar）

---

#### 8️⃣ 古典 × 搖滾的藝術碰撞

- **類別**：Music
- **SEO KW**：古典樂、搖滾音樂、跨界合作
- **字數**：2,500 字
- **內部連結**：3-4 條

---

### **優先級 P5：Film（3 篇）**

#### 9️⃣ 紀錄電影完整指南

- **類別**：Film
- **SEO KW**：紀錄片、紀錄電影、奧斯卡最佳紀錄片
- **字數**：3,000 字
- **內部連結**：3 條

---

#### 🔟 日本新浪潮電影復興論

- **類別**：Film
- **SEO KW**：日本電影、是枝裕和、新浪潮、當代電影
- **字數**：3,500 字
- **內部連結**：3-4 條

---

#### 1️⃣1️⃣ 性別研究視角的現代電影批評

- **類別**：Film
- **SEO KW**：女性主義、電影批評、性別研究
- **字數**：3,500 字
- **內部連結**：3-4 條

---

## 📊 執行時間表

| 週次 | 文章 | 分類 | 預計完成 | 發佈時間 |
|------|------|------|---------|---------|
| **Week 2** | 3/5 | Tech | 2026-04-13 | 2026-04-14 |
| **Week 3** | 2/2 | Tech/Music | 2026-04-20 | 2026-04-21 |
| **Week 4** | 2/3 | Music/Film | 2026-04-27 | 2026-04-28 |

---

## 🚀 後續步驟

1. ✅ 確認選題 → 2026-04-03
2. 🔄 發送給 ContentMaster → Week 2 批量生成
3. 📝 人性化優化（AI 移除 70%+）
4. 🔗 內部連結部署（Unit 2.2 方式）
5. 📤 發佈 + Google 索引提交（Unit 3.1）

**準備啟動 ContentMaster 批量生成？**
