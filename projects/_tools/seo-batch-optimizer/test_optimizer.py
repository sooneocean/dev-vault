#!/usr/bin/env python3
"""
Test suite for AI optimizer with 3 representative YOLO LAB posts:
1. Music event (演唱會) - High search intent for tickets
2. Tech analysis (科技) - Product comparison
3. Lifestyle review (生活品鑑) - Product evaluation
"""

import pytest
import json
from ai_optimizer import AIOptimizer, Post, OptimizationResult
from pathlib import Path


class TestAIOptimizer:
    """Test cases for AI optimizer."""

    @pytest.fixture(scope="class")
    def optimizer(self):
        """Initialize optimizer once per class."""
        return AIOptimizer()

    @pytest.fixture
    def test_posts(self):
        """Provide 3 test posts covering YOLO LAB categories."""
        return [
            # 1. MUSIC EVENT
            Post(
                post_id=34844,
                title="Kodaline 解散震撼彈！8/24 台北站告別巡演搶票全攻略",
                content="""Kodaline 樂團正式宣布解散，將於今年舉辦最後告別巡迴演唱會。
台北站確定為 8/24 舉辦，地點為台北國際會議中心 (TICC)。
樂團代表作《All I Want》已累計 15 億次點聽，是 90 年代搖滾的傳奇。

★ 搶票時程：
- 4 月 1 日 10:00 開放售票
- DBS 信用卡持卡人享 4 月 1 日 9:00 搶先購
- 台大校友卡享購票優惠 8 折

★ 票價：
- VIP 區 $3,500
- 甲票 $2,500
- 乙票 $1,500

★ 場地資訊：
台北國際會議中心 (TICC)
地址：台北市中正區信義路一段 1 號
捷運：板南線國父紀念館站 1 號出口

★ 更多資訊：
Kktix、Ticketplus、KKTIX 都可購票
官方粉絲團：Kodaline Taiwan""",
                excerpt="Kodaline 最後一場演唱會確定在 8 月 24 日台北舉行。15 億次點聽神曲、搶票攻略全解。",
                category="music",
            ),

            # 2. TECH ANALYSIS
            Post(
                post_id=34845,
                title="iPhone 16 Pro vs Pixel 9 Pro：2024 攝影旗艦終極對決",
                content="""2024 年度最期待的兩款旗艦手機正式發表，到底誰的相機更強？

★ iPhone 16 Pro 規格：
- 晶片：A18 Pro（新款）
- 主鏡頭：48MP，f/1.78 光圈
- 超廣角：12MP，f/2.2 光圈
- 長焦：12MP，5 倍光學變焦，f/2.8 光圈
- 夜間模式：新增 AI 夜景增強
- 價格：$36,900 起（256GB）

★ Google Pixel 9 Pro 規格：
- 晶片：Google Tensor G4
- 主鏡頭：50MP，f/1.68 光圈
- 超廣角：10.5MP，f/2.2 光圈
- 長焦：10MP，5 倍光學變焦，f/2.0 光圈
- AI 魔法橡皮擦：移除背景物體
- 價格：$25,999 起（256GB）

★ 實測對比（台北街景、室內、人像）：
1. 夜景表現：Pixel 9 Pro 稍領先（AI 演算法）
2. 人像模式：iPhone 16 Pro 邊緣處理更精準
3. 色彩還原：iPhone 偏暖，Pixel 偏冷
4. 變焦穩定性：兩者平分秋色
5. 廣角變形：iPhone 控制較好

★ 誰該買誰：
- 想要 5 年穩定支援 → iPhone
- 想要 AI 功能搶先體驗 → Pixel
- 預算有限 → Pixel（便宜 $11,000）
- 生態系考量 → 看你的 MacBook、iPad""",
                excerpt="終極攝影對決：iPhone 16 Pro 和 Pixel 9 Pro 2024 年誰最強？我們實測對比給你看。",
                category="tech",
            ),

            # 3. LIFESTYLE REVIEW
            Post(
                post_id=34846,
                title="LANEIGE 拉尼傑 晶透感唇膜深度評測：年輕人最愛護唇神器",
                content="""韓國美妝品牌 LANEIGE 的拉尼傑唇膜在 IG、小紅書爆紅，每天都有素人分享「唇膜日記」。

★ 產品基本資訊：
- 品牌：LANEIGE（蘭芝）
- 商品名：Lip Sleeping Mask（唇膜）
- 容量：20g
- 官方售價：$380 新台幣
- 開架通路：屈臣氏、康是美、寶雅全有貨
- 保固期限：開封後 12 個月

★ 成分分析：
主成分：
- 維生素 E（抗氧化）
- 玫瑰果油（舒緩保濕）
- 保濕複合體（鎖水）
- 蜂蜜提取物（修護）

不含：香精、重金屬、礦物油

★ 使用體驗：
1. 質地：厚重型唇膜，像軟膏狀
2. 香氣：淡淡莓果香（天然香精）
3. 吸收速度：厚敷 15 分鐘後吸收 70%
4. 保濕時間：上膜後 6 小時內唇部不乾
5. 唇色變化：偏深色唇變得透亮，效果明顯

★ 對比競品（同價位）：
| 品牌 | 價格 | 保濕度 | 持久度 | CP值 |
|------|------|--------|--------|------|
| LANEIGE | $380 | 9/10 | 6h | 10/10 |
| 歐舒丹 | $650 | 8/10 | 4h | 7/10 |
| COSRX | $220 | 6/10 | 3h | 6/10 |
| Melano CC | $280 | 7/10 | 4h | 8/10 |

★ 誰該買：
✓ 唇紋多、易乾唇的人
✓ 想要唇色變透亮的人
✓ 預算 $300-400 的人
✗ 追求快速吸收的人（應選輕質乳液型）
✗ 過敏肌膚（含天然香精，有人過敏報告）

★ 使用建議：
- 晚間厚敷當睡眠面膜效果最佳
- 早上可當唇部打底，再上唇膏
- 一支可用 3-4 個月（每晚一次）

★ 在哪買最便宜：
Momo 購物節打 85 折 → $323
屈臣氏會員卡結帳 → $361 送折價券
Costco（限會員）→ $350/兩支""",
                excerpt="LANEIGE 唇膜為什麼這麼紅？深度評測：成分、使用體驗、對比競品、是否值得買。",
                category="lifestyle",
            ),
        ]

    def test_optimizer_initialization(self, optimizer):
        """Test optimizer initializes correctly."""
        assert optimizer.model == "claude-opus-4-6"
        assert optimizer.input_cost_per_m == 5.00
        assert optimizer.output_cost_per_m == 25.00

    def test_category_system_prompt(self, optimizer):
        """Test category-specific prompts are returned."""
        music_prompt = optimizer._get_category_system_prompt("music")
        assert "演唱會" in music_prompt or "音樂" in music_prompt

        tech_prompt = optimizer._get_category_system_prompt("tech")
        assert "科技" in tech_prompt or "技術" in tech_prompt

        lifestyle_prompt = optimizer._get_category_system_prompt("lifestyle")
        assert "生活" in lifestyle_prompt or "品鑑" in lifestyle_prompt

    def test_turn1_prompt_generation(self, optimizer, test_posts):
        """Test Turn 1 prompt generates correctly."""
        post = test_posts[0]
        prompt = optimizer._get_turn1_prompt(post)
        assert "Title Tag" in prompt or "標題" in prompt or "title" in prompt.lower()
        assert "55-60" in prompt
        assert post.title in prompt
        assert post.category in prompt

    def test_turn2_prompt_generation(self, optimizer, test_posts):
        """Test Turn 2 prompt generates correctly."""
        post = test_posts[0]
        title = "Kodaline 台北告別演唱會"
        prompt = optimizer._get_turn2_prompt(post, title)
        assert "Meta Description" in prompt or "描述" in prompt.lower() or "description" in prompt.lower()
        assert "157-160" in prompt

    def test_json_parsing_titles(self, optimizer):
        """Test parsing of title JSON from response."""
        sample_response = """根據要求，我生成了以下標題：

{"titles": [
  {"option": 1, "text": "Kodaline 台北告別演唱會 8/24 TICC | 搶票攻略", "length": 32},
  {"option": 2, "text": "Kodaline 解散最終巡迴台北站 | 8/24 TICC 演出", "length": 35},
  {"option": 3, "text": "Kodaline Farewell Tour 台北 8/24 | 票價搶票資訊", "length": 37}
]}"""
        titles = optimizer._parse_titles(sample_response)
        assert len(titles) == 3
        assert titles[0]["option"] == 1
        assert "Kodaline" in titles[0]["text"]

    def test_json_parsing_description(self, optimizer):
        """Test parsing of description JSON from response."""
        sample_response = """{"description": "Kodaline 最終告別演唱會 8/24 台北 TICC！15 億次點聽神曲〈All I Want〉。4/1 搶票開啟，DBS/台大卡友搶先購。", "length": 58}"""
        desc, length = optimizer._parse_description(sample_response)
        assert len(desc) > 0
        assert "Kodaline" in desc
        assert length > 0

    def test_json_parsing_faq(self, optimizer):
        """Test parsing FAQ from response."""
        sample_response = """{"faq": [
  {"q": "Kodaline 最後一場演唱會在哪裡？", "a": "台北國際會議中心 (TICC)，地址..."},
  {"q": "如何用 DBS 卡搶先購票？", "a": "4 月 1 日 9:00..."},
  {"q": "Kodaline 〈All I Want〉的故事背景？", "a": "..."}
]}"""
        faq = optimizer._parse_faq(sample_response)
        assert len(faq) >= 3
        assert "演唱會" in faq[0]["q"]

    def test_cost_estimation(self, optimizer):
        """Test cost estimation logic."""
        estimate = optimizer.estimate_full_batch_cost(num_posts=2700)
        assert estimate["num_posts"] == 2700
        assert estimate["estimated_cost_usd"] > 0
        assert estimate["cost_per_post"] > 0

    def test_optimization_result_structure(self):
        """Test OptimizationResult data class structure."""
        result = OptimizationResult(
            post_id=12345,
            titles=[{"option": 1, "text": "Test Title", "length": 20}],
            description="Test description",
            description_length=100,
            internal_links=[{"post_id": 999, "anchor": "link text", "reason": "related"}],
            faq=[{"q": "question?", "a": "answer"}],
            image_alts=[{"image_id": 1, "alt": "alt text"}],
            cost_estimate={"total_input_tokens": 1000, "estimated_cost_usd": 0.05},
            raw_turns={},
        )
        assert result.post_id == 12345
        assert len(result.titles) == 1
        assert len(result.faq) == 1

    def test_batch_export_jsonl(self, optimizer, test_posts, tmp_path):
        """Test JSONL export format."""
        # Create mock results
        results = [
            OptimizationResult(
                post_id=post.post_id,
                titles=[{"option": 1, "text": f"Title for {post.post_id}", "length": 30}],
                description=f"Description for post {post.post_id}",
                description_length=150,
                internal_links=[],
                faq=[],
                image_alts=[],
                cost_estimate={},
                raw_turns={},
            )
            for post in test_posts
        ]

        output_file = tmp_path / "test_output.jsonl"
        optimizer.export_jsonl(results, str(output_file))

        # Verify file was created and has correct format
        assert output_file.exists()
        lines = output_file.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == len(test_posts)

        # Verify each line is valid JSON
        for line in lines:
            data = json.loads(line)
            assert "post_id" in data
            assert "optimizations" in data


class TestMultiTurnConversation:
    """Test multi-turn conversation handling."""

    def test_message_history_format(self):
        """Test message history maintains correct format."""
        messages = [
            {"role": "user", "content": "Turn 1 prompt"},
            {"role": "assistant", "content": "Turn 1 response"},
            {"role": "user", "content": "Turn 2 prompt"},
        ]

        # Verify alternating pattern
        for i, msg in enumerate(messages):
            if i % 2 == 0:
                assert msg["role"] == "user"
            else:
                assert msg["role"] == "assistant"

    def test_json_extraction_from_response(self):
        """Test JSON extraction from various response formats."""
        responses = [
            'Here is the JSON:\n{"titles": [{"option": 1, "text": "Title", "length": 30}]}',
            '{"description": "test description", "length": 150}',
            'Some text before\n{"faq": [{"q": "?", "a": ""}]}\nSome text after',
        ]

        optimizer = AIOptimizer()
        # All responses should extract JSON successfully
        for resp in responses:
            match = __import__("re").search(r"\{.*\}", resp, __import__("re").DOTALL)
            assert match is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
