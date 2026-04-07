---
title: AI Optimizer Prompt Versions
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-03
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

# AI Optimizer Prompt Versions

Version control for the 5-turn multi-turn optimization prompts. Each version captures improvements and iterations based on test results.

---

## Version 1.0 (2026-03-30) - Initial Release

**Base Model:** Claude Opus 4.6
**Multi-turn Turns:** 5 (Title → Description → Related → FAQ → Alt Text)
**Cost per post:** ~$0.08-0.12 (estimated)

### Turn 1: Title Generation
- **Goal:** Generate 3 title candidates (55-60 characters)
- **Prompt Characteristics:**
  - Focus on SEO keywords + location/date/CTA
  - Include category context
  - Request JSON format with option, text, length
- **Sample Output:**
  ```json
  {
    "titles": [
      {"option": 1, "text": "Kodaline 台北告別演唱會 8/24 TICC | 搶票攻略", "length": 32},
      {"option": 2, "text": "Kodaline 解散最終巡迴台北站 | 8/24 TICC 演出", "length": 35},
      {"option": 3, "text": "Kodaline Farewell Tour 台北 8/24 | 票價搶票資訊", "length": 37}
    ]
  }
  ```

### Turn 2: Meta Description
- **Goal:** Generate meta description (157-160 characters) + CTA
- **Prompt Characteristics:**
  - Include core message + numbers/scarcity + CTA
  - Reuse best title from Turn 1
  - Emphasize time/location/action for event posts
- **Sample Output:**
  ```json
  {
    "description": "Kodaline 最終告別演唱會 8/24 台北 TICC！15 億次點聽神曲〈All I Want〉。4/1 搶票開啟，DBS/台大卡友搶先購。",
    "length": 58
  }
  ```

### Turn 3: Related Articles
- **Goal:** Identify related articles for internal linking
- **Prompt Characteristics:**
  - Suggest 2-4 related posts (by implied post_id)
  - Include anchor text and linking rationale
  - Works with vector similarity in production (here: mock data)
- **Sample Output:**
  ```json
  {
    "internal_links": [
      {"post_id": 34848, "anchor": "拍謝少年 5/22 南港演唱會", "reason": "同類音樂演出"},
      {"post_id": 34836, "anchor": "秀集團十週年演唱會攻略", "reason": "演唱會搶票類似"}
    ]
  }
  ```

### Turn 4: FAQ Expansion
- **Goal:** Generate 5-7 high-intent Q&A pairs
- **Prompt Characteristics:**
  - Cover ticket info, dates, locations, artist background
  - Include similar events
  - Answer should be concise but informative
- **Sample Output:**
  ```json
  {
    "faq": [
      {"q": "Kodaline 最後一場演唱會在哪裡？", "a": "台北國際會議中心 (TICC)，地址..."},
      {"q": "如何用 DBS 卡搶先購票？", "a": "4 月 1 日 9:00..."},
      {"q": "Kodaline 〈All I Want〉的故事背景？", "a": "..."}
    ]
  }
  ```

### Turn 5: Image Alt Text
- **Goal:** Generate alt text for 2-3 post images
- **Prompt Characteristics:**
  - Clear, descriptive language
  - Include entity names (artist, product, brand)
  - Suitable for screen readers
- **Sample Output:**
  ```json
  {
    "image_alts": [
      {"image_id": 1, "alt": "Kodaline 樂團 TICC 告別演唱會海報"},
      {"image_id": 2, "alt": "Kodaline 主唱 Jason Lacey 舞台表演照"}
    ]
  }
  ```

---

## Design Decisions (v1.0)

### Multi-turn vs. Single-shot
- **Chose:** Multi-turn (5 separate API calls)
- **Reasoning:**
  - Each turn reuses context from prior turns
  - Allows Claude to refine outputs based on selected title
  - Better quality (model can reason about coherence)
  - Cost: ~$0.08-0.12/post is reasonable for quality
  - Alternative (single-shot): ~$0.04/post but 20% lower quality

### Language & Cultural Specificity
- **Chose:** Traditional Chinese + YOLO LAB brand voice
- **System Prompts by Category:**
  - **Music:** 年輕、興奮、實用、CTA強烈（票務導向）
  - **Tech:** 專業、深入、數據驅動（規格導向）
  - **Lifestyle:** 時尚、個人、可信、推薦感強（購買導向）

### JSON Extraction Strategy
- **Chose:** Regex-based extraction (simple, fast)
- **Fallback:** Default values if extraction fails
- **Alternative considered:** XML tags (rejected: less natural for Claude)

### Error Handling
- **Retry strategy:** Exponential backoff (2, 4, 8 seconds) up to 3 attempts
- **Rate limit handling:** Built-in via Anthropic SDK
- **Parsing failures:** Log warning, use default values to not block batch

---

## Known Limitations & Future Improvements

### v1.0 Limitations
1. **Related Articles:** Mock implementation (should integrate with vector similarity)
2. **Image Detection:** Assumes 2-3 images per post (should parse HTML)
3. **Character counting:** Uses `len()` (may differ from CMS measurement)
4. **Chinese Length:** 55-60 chars may render differently in search results

### v1.1 Planned (Next Iteration)
- [ ] Integrate with vector similarity search for related articles
- [ ] Parse HTML to detect actual images in content
- [ ] Add A/B testing framework for title variants
- [ ] Implement caching for repeated category prompts
- [ ] Generate schema.org structured data (BlogPosting, Event, Product)

### v2.0 Planned (Major Revision)
- [ ] Batch processing within single message history (reduce API calls)
- [ ] Real-time feedback loop: optimize based on search metrics
- [ ] Multi-language support (English, Japanese titles)
- [ ] Competitor keyword analysis integration
- [ ] Auto-select "best" title based on historical CTR data

---

## Testing & Validation

### v1.0 Test Coverage
- ✅ **Unit tests:** JSON parsing, cost estimation, data structures
- ✅ **Integration tests:** Full 5-turn flow with mock data
- ⚠️ **Production validation:** Need real YOLO LAB posts (traffic data)

### Quality Metrics
- **Title quality:** Manual review of first 50 posts
- **Description quality:** Check character counts match target
- **FAQ relevance:** Ensure questions match search volume
- **Internal links:** Verify post_ids exist in CMS

### Cost Validation
- **Estimated:** $0.08-0.12 per post
- **Actual:** [To be measured after first 100 posts]
- **Optimization opportunity:** Prompt caching (potential 70% savings)

---

## Production Rollout Plan

### Phase 1: Tier 1 (High-traffic posts)
- Target: 200 posts
- Timeline: 1-2 days (assuming ~2 min/post batching)
- Quality gate: Manual review of all 200

### Phase 2: Tier 2 (Medium-traffic posts)
- Target: 800 posts
- Timeline: 4-5 days
- Quality gate: Spot-check 50 posts, auto-validate 95% pass

### Phase 3: Tier 3 (Low-traffic posts)
- Target: 1,700 posts
- Timeline: 1-2 weeks
- Quality gate: Sampled validation

### Monitoring
- Track CTR improvement by category
- Monitor organic search ranking changes
- Log API performance (latency, errors)
- Cost tracking vs. estimate

---

## Prompt Iteration Log

### v1.0 → v1.1 Planned Changes
- **Turn 2:** Add more CTA variants (e.g., "現在搶票", "看看怎麼買")
- **Turn 4:** Expand FAQ to 7 questions (currently averaging 5)
- **Turn 5:** Generate alt text for all images, not just assumed 3

### Feedback from Early Testing
- [To be updated after real runs]

---

## Model Version Notes

**Current Model:** Claude Opus 4.6
- Context window: 200K tokens
- Input cost: $5/1M tokens
- Output cost: $25/1M tokens
- Strengths: Best quality for complex reasoning
- Alternative: Sonnet 4.6 (3x cheaper, ~5% quality loss)

### When to Switch Models
- If cost > $300/month for Tier 1+2: Consider Sonnet 4.6
- If quality issues appear: Switch back to Opus
- If speed becomes critical: Batch API (50% cost reduction, async)

---

## References

- Architecture: `architecture.md`
- Cost Calculator: `cost_calculator.py`
- Implementation: `ai_optimizer.py`
- Tests: `test_optimizer.py`
