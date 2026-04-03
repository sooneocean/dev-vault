# 提示詞工程完全指南｜Chain-of-Thought × Few-Shot × 角色扮演最強技巧

2026 年，能否駕馭大型語言模型的關鍵早已不是「會不會用」，而是「用得好不好」。提示詞工程（Prompt Engineering）正是決定 AI 輸出品質的核心技能。無論你是軟體工程師、產品經理還是內容創作者，掌握系統化的提示詞方法論，將讓你從「靠運氣獲得好結果」進化為「穩定產出高品質輸出」。

本文將從基礎概念出發，深入拆解十大核心技巧，搭配實戰案例與程式碼範例，為你建立一套完整的提示詞工程知識體系。

## 什麼是提示詞工程

提示詞工程是指透過精心設計輸入文本（Prompt），引導大型語言模型產生期望輸出的一門實踐學科。它結合了語言學、認知科學與軟體工程思維，遠不只是「打字問問題」這麼簡單。

### 為什麼重要

同一個模型，面對不同的提示詞，輸出品質可能天差地遠。一個模糊的提示詞可能得到泛泛而談的回答；而經過精心設計的提示詞，則能引出結構清晰、邏輯嚴密的高品質回應。其價值體現在三個層面：

1. **效率提升**：減少反覆修改次數，一次到位
2. **品質保證**：結構化約束確保輸出符合預期格式與深度
3. **可重複性**：可複用模板讓團隊都能獲得穩定結果

### 核心組成要素

高品質的提示詞包含五大要素：

- **角色設定（Role）**：模型的身份定位
- **任務描述（Task）**：需要完成什麼
- **上下文（Context）**：必要的背景資訊
- **約束條件（Constraints）**：格式、長度、風格限制
- **輸出格式（Output Format）**：期望的回應結構

理解這些基礎後，讓我們進入十大技巧的深度解析。如果你正在將 AI 融入開發工作流，這些技巧是你最需要的工具箱。 [LINK: ai-ide-agent-collaboration-survival-guide]

## 十大提示詞工程技巧詳解

### 技巧一：Chain-of-Thought（思維鏈推理）

CoT 是目前最具影響力的提示詞技巧之一，由 Google Research 在 2022 年提出。核心思想是引導模型「一步一步思考」，而非直接跳到答案。LLM 被要求直接輸出答案時往往跳過關鍵推理步驟；CoT 強制其展示推理過程，進行逐步分析。

**基礎用法**：

```
問題：商店有 23 顆蘋果，用掉 20 顆做派，又買進 6 顆，還剩幾顆？

請一步一步思考，展示推理過程。
```

**進階用法**：在 system prompt 中預設推理步驟模板（識別條件、確定目標、列出邏輯、逐步計算、驗證答案），讓模型對每道題都自動套用 CoT 流程。實測顯示，CoT 在數學推理與多步驟任務中準確率提升可達 20%-40%。

### 技巧二：Few-Shot Prompting（少樣本提示）

Few-Shot 是透過在提示詞中提供若干示例，讓模型學習期望的輸入輸出模式。相比 Zero-Shot（不提供示例），Few-Shot 能大幅提升模型對特定任務格式的理解。

```
任務：將評論分類為正面、負面或中性。

範例 1：
評論：「品質太差，用一週就壞了」→ 負面

範例 2：
評論：「性價比很高，推薦給預算有限的朋友」→ 正面

範例 3：
評論：「功能還行，介面可再改進」→ 中性

請分類：「客服態度好，但物流慢」→
```

選擇有代表性的示例，覆蓋邊界情況。通常 3-5 個即可，過多反而引入噪音。

### 技巧三：角色扮演（Role Playing）

透過賦予模型特定身份，有效調整其回應的專業深度與關注焦點。

```
你是擁有 15 年經驗的資深後端架構師，專精分散式系統。
回答應從架構角度分析，考慮可擴展性與容錯性，使用專業術語但解釋清晰。

問題：API 每天處理 500 萬請求，延遲上升，如何優化？
```

**進階——多角色協作**：讓模型同時扮演架構師、安全專家和產品經理進行圓桌討論，從多視角分析問題後綜合給出建議。角色描述越具體，回應越聚焦。

### 技巧四：結構化輸出約束（Structured Output）

需要特定格式輸出時，明確定義 schema 至關重要：

```
分析以下程式碼問題，以 JSON 回傳：
def process(items):
    return [item["value"] / item["count"] for item in items]

格式：{"issues": [{"type": "bug|perf|security", "severity": "high|medium|low",
"description": "...", "suggestion": "..."}], "overall_risk": "high|medium|low"}
```

搭配 JSON Schema 或 TypeScript 型別定義可以更精確控制輸出。生產環境建議加入輸出驗證邏輯。

### 技巧五：Self-Consistency（自一致性）

Self-Consistency 是 CoT 的進階版本。核心概念是對同一問題進行多次推理，透過投票機制選出最一致的答案：

```python
def self_consistency(question, n=5):
    answers = [extract_answer(llm.generate(question, temperature=0.7)) for _ in range(n)]
    from collections import Counter
    return Counter(answers).most_common(1)[0][0]
```

適合高可靠性場景如醫療輔助、法律分析。代價是增加 API 呼叫次數，需在準確率與成本間取得平衡。

### 技巧六：Tree-of-Thought（思維樹）

Tree-of-Thought 將 CoT 進一步擴展為樹狀搜索結構。模型在每一步都生成多個候選思路，然後評估每條路徑的可行性，選擇最優路徑繼續深入：

```
設計離線筆記應用架構，使用思維樹分析：

第一層——三種技術方案（A/B/C）
第二層——各方案評分（複雜度、離線體驗、衝突處理）
第三層——深入展開最優方案的架構設計
```

特別適合開放性設計問題與技術選型。

### 技巧七：ReAct（推理 + 行動）

ReAct 結合了推理（Reasoning）與行動（Acting），讓模型在思考的同時執行工具呼叫。這是 AI Agent 架構的核心模式。 [LINK: openclaw-ai-agent-one-person-company]

```
思考：用戶想知道台北天氣，需查詢即時資料。
行動：call_weather_api(city="taipei")
觀察：晴天，28°C，濕度 65%
思考：已獲得資料，組織回答。
回答：台北晴朗 28°C，濕度 65%，建議輕便衣物並防曬。
```

```python
class ReActAgent:
    def run(self, query, max_steps=5):
        history = []
        for _ in range(max_steps):
            resp = self.llm.generate(self.build_prompt(query, history))
            if resp.type == "answer":
                return resp.content
            elif resp.type == "action":
                result = self.tools.execute(resp.tool, resp.args)
                history.append(("觀察", result))
```

ReAct 模式是建構 AI Agent 的基礎，從簡單的工具呼叫到複雜的多步驟任務編排，都建立在這個推理加行動的循環之上。

### 技巧八：Prompt Chaining（提示詞鏈）

對於複雜任務，將其拆解為多個子任務鏈，前一步的輸出作為下一步的輸入：

```python
research_prompt = "針對「{topic}」列出核心子主題、讀者痛點"  # 步驟 1
outline_prompt = "基於研究結果生成大綱：{research_output}"     # 步驟 2
section_prompt = "撰寫「{title}」章節，{word_count} 字"       # 步驟 3
polish_prompt = "整合各章節，確保過渡自然、術語一致"            # 步驟 4
```

Prompt Chaining 的關鍵在於明確定義好每步的輸入輸出介面。

### 技巧九：Negative Prompting（反向約束）

明確告訴模型「不要做什麼」，有時比正向指令更有效：

```
撰寫 Kubernetes Pod 概念說明。
【禁止】：不用口語轉折、不假設讀者是初學者、不超過 5 要點、不用比喻
【要求】：精確術語附英文原詞、YAML 範例、說明與 Container/Node 的關係
```

反向約束在消除「客套話」和「過度簡化」傾向時特別有效。

### 技巧十：Meta-Prompting（元提示詞）

讓模型自己生成或優化提示詞，是提示詞工程的自動化：

```
你是提示詞工程專家。目標：讓 LLM 將非結構化用戶回饋轉為 Bug Report。
請設計最優提示詞（含角色、任務、JSON Schema、兩個 Few-Shot 範例、邊界處理），
並解釋設計決策。
```

Meta-Prompting 讓 AI 協助你設計更好的 AI 互動方式，在建構提示詞模板庫時能大幅加速迭代。

## 實戰案例：Code Review Agent

用一個完整的實戰案例，串聯多種技巧。目標：建構自動化 Code Review Agent，分析 Pull Request 並產出結構化審查報告。

### 系統提示詞

```python
SYSTEM_PROMPT = """
# Role：資深程式碼審查員，10 年經驗，專精 Python/TypeScript/安全分析
# Process（CoT）：通讀 diff → 邏輯檢查 → 效能評估 → 安全掃描 → 評分建議
# Constraints：不建議純風格修改、不超過 10 條建議、必須給具體方案
# Output：JSON {"summary", "risk_level", "findings": [{"file", "line",
#   "category", "severity", "description", "suggestion"}], "overall_score"}
"""
```

### Agent 主循環

```python
class CodeReviewAgent:
    async def review(self, pr):
        # 階段 1：理解意圖（CoT）
        intent = await self.llm.generate(
            system=SYSTEM_PROMPT,
            user=f"分析 PR 變更意圖：\n{pr.diff}",
            temperature=0.3
        )

        # 階段 2：逐檔審查（Prompt Chaining + ReAct）
        reviews = []
        for f in pr.files:
            ctx = await self.tools["get_context"](f.path)
            review = await self.llm.generate(
                system=SYSTEM_PROMPT,
                user=self.build_prompt(f, ctx, intent),
                temperature=0.2
            )
            reviews.append(review)

        # 階段 3：綜合評估
        return await self.llm.generate(
            system=SYSTEM_PROMPT,
            user=self.build_summary(intent, reviews),
            temperature=0.1
        )
```

此案例結合了 CoT、角色扮演、結構化輸出、ReAct 和 Prompt Chaining 五種技巧，建構出一個完整且實用的 AI 自動化工作流。

## 最佳實踐與常見陷阱

### 五條黃金法則

**法則一：具體勝於抽象**

```
# 差：寫一篇關於 Docker 的文章。
# 好：面向有 Linux 基礎但未接觸容器的後端工程師，撰寫 Docker 入門教學，
#     涵蓋容器 vs 虛擬機、Dockerfile（Flask 為例）、docker-compose。2000 字。
```

**法則二：迭代優化而非一次成型**——提示詞工程是一個迭代過程。從簡單的提示詞開始，根據輸出結果逐步增加約束和指引。記錄每次調整和對應的效果變化，建立自己的提示詞優化日誌。

**法則三：善用分隔符號**——使用 XML 標籤、三重反引號、分隔線等清楚區分提示詞的不同段落，避免模型混淆指令與內容。

**法則四：控制溫度參數**——溫度（Temperature）直接影響輸出的創造性與穩定性，根據任務性質選擇：

| 任務類型 | 建議溫度 | 原因 |
|---------|---------|------|
| 程式碼生成 | 0.1-0.3 | 需要精確與一致性 |
| 技術文件 | 0.3-0.5 | 平衡準確性與可讀性 |
| 創意寫作 | 0.7-0.9 | 鼓勵多樣性與創新 |
| 腦力激盪 | 0.8-1.0 | 最大化探索空間 |

**法則五：建立提示詞模板庫**——將經過驗證的高效提示詞抽象為可複用的模板，建立團隊共享的提示詞資產。好的模板應該有清晰的變數插槽、使用說明和適用場景標注。

### 五個常見陷阱

**陷阱一：過度約束**——堆砌太多限制條件會讓模型「無所適從」，反而降低輸出品質。約束條件應該聚焦在最關鍵的三到五個維度。

**陷阱二：忽略 Token 預算**——提示詞本身佔用的 Token 數量會壓縮模型可用的生成空間。特別是在使用 Few-Shot 時，過多的範例可能導致模型的生成回應被截斷。務必計算提示詞加上預期輸出的總 Token 需求。

**陷阱三：範例偏差**——Few-Shot 中的範例如果過於相似或只覆蓋特定情況，模型會學到有偏差的模式。確保範例涵蓋正常情況、邊界情況和異常情況。

**陷阱四：缺乏輸出驗證**——在生產環境中，絕對不要盲目信任 LLM 的輸出。任何進入下游系統的 AI 生成內容，都應該經過格式驗證與邏輯檢查：

```python
def validate_output(llm_output, schema):
    data = json.loads(llm_output)
    validate(instance=data, schema=schema)  # jsonschema
    return data  # 驗證失敗則 retry_with_feedback
```

**陷阱五：不記錄不測量**——提示詞工程需要數據驅動。記錄每次提示詞的版本、對應的輸出品質評分和調整紀錄。沒有測量就沒有改進。建議使用版本控制管理提示詞，就像管理程式碼一樣。 [LINK: tech-pillar]

## 進階：組合拳策略

在實務中，單一技巧的效果往往有限。真正的高手會根據任務特性，組合多種技巧形成策略。以下是三種經過驗證的組合方案：

**策略一：CoT + Few-Shot + 結構化輸出**——適合需推理且格式固定的場景，如測試案例生成。先用 Few-Shot 展示推理路徑與格式，再用 CoT 確保一致性。

**策略二：角色扮演 + ReAct + Prompt Chaining**——適合複雜多步驟工作流，如方案評審。角色設定專業視角，ReAct 提供工具呼叫，Chaining 管理流程。

**策略三：Meta-Prompting + Self-Consistency + 反向約束**——適合高可靠性的提示詞自動化。生成候選提示詞後多次評估穩定性，過濾不合格結果。

## 總結與展望

提示詞工程並非一套僵硬的規則，而是一門需要持續實踐和迭代的技藝。從最基礎的 Chain-of-Thought 和 Few-Shot，到進階的 Tree-of-Thought 和 Meta-Prompting，每種技巧都有其最適合的應用場景。

掌握這些技巧的關鍵不在於記住每個名詞，而在於理解背後的設計原理——為什麼逐步推理能提升準確率？為什麼範例能幫助模型理解意圖？為什麼結構化約束能穩定輸出格式？理解了原理，你就能根據具體場景靈活組合，設計出最適合自己需求的提示詞。

在 AI Agent 快速發展的今天，提示詞工程正在從「手動編寫」演化為「系統化設計」。將提示詞視為軟體元件——有版本控制、有測試、有文件、有效能指標——這才是面向未來的工程化思維。

建議你從今天開始，選擇一到兩個技巧，在日常工作中刻意練習。記錄你的提示詞、標注效果、持續迭代。三個月後，你會發現自己與 AI 協作的效率已經發生質的飛躍。
