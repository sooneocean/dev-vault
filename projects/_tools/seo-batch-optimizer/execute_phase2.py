#!/usr/bin/env python3
"""
Phase 2 統合執行器：拉取 → 分層 → 優化 → 推送
"""

import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("phase2_execution.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class Phase2Executor:
    """Phase 2 全流程執行器"""

    def __init__(self):
        self.posts = []
        self.tiers = {"tier_1": [], "tier_2": [], "tier_3": []}
        self.optimizations = []
        self.start_time = datetime.now()

    def load_posts_from_file(self, filepath: str) -> List[Dict]:
        """從 JSON 檔案載入文章"""
        logger.info(f"Loading posts from {filepath}...")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                posts = data.get('posts', [])
            logger.info(f"✓ Loaded {len(posts)} posts")
            return posts
        except Exception as e:
            logger.error(f"Failed to load posts: {e}")
            return []

    def estimate_views_from_metadata(self, post: Dict) -> int:
        """
        估算文章 30 日流量
        基於：發布日期、類別、特色圖片等信號
        """
        # 簡化邏輯：根據發布時間距離現在的天數估算
        # 實際應使用 WordPress.com stats API 取得真實數據
        from datetime import datetime as dt

        try:
            post_date = dt.fromisoformat(post.get('date', '').replace('Z', '+00:00'))
            days_old = (dt.now(post_date.tzinfo) - post_date).days
        except:
            days_old = 30

        # 簡單模型：較新的文章流量更高
        base_views = 50
        decay_factor = max(1, 1 - (days_old / 180))  # 180 天衰減到基線
        estimated_views = int(base_views * decay_factor)

        return max(5, estimated_views)  # 最低 5 views

    def tier_posts(self, posts: List[Dict]) -> Dict:
        """
        分層文章：
        - Tier 1: views > 20（高流量）
        - Tier 2: 5-20 views（中流量）
        - Tier 3: < 5 views（低流量）
        """
        logger.info("\n[Step 2] Tiering posts by estimated traffic...")

        tier_1 = []
        tier_2 = []
        tier_3 = []

        for post in posts:
            views = self.estimate_views_from_metadata(post)
            post['estimated_views'] = views  # 附加估算值

            if views > 20:
                tier_1.append(post)
            elif views >= 5:
                tier_2.append(post)
            else:
                tier_3.append(post)

        logger.info(f"Tier Distribution:")
        logger.info(f"  Tier 1 (views > 20):  {len(tier_1):>4} posts ({len(tier_1)/len(posts)*100:>5.1f}%)")
        logger.info(f"  Tier 2 (5-20 views):  {len(tier_2):>4} posts ({len(tier_2)/len(posts)*100:>5.1f}%)")
        logger.info(f"  Tier 3 (< 5 views):   {len(tier_3):>4} posts ({len(tier_3)/len(posts)*100:>5.1f}%)")

        tier_1_2_count = len(tier_1) + len(tier_2)
        logger.info(f"\nFocus Target (Tier 1+2): {tier_1_2_count} posts")
        logger.info(f"Estimated cost (Sonnet @ $0.10/post): ${tier_1_2_count * 0.10:.2f}")

        return {
            "tier_1": tier_1,
            "tier_2": tier_2,
            "tier_3": tier_3,
        }

    def generate_sample_optimizations(
        self, posts: List[Dict], limit: int = 5
    ) -> List[Dict]:
        """
        生成樣本優化建議（實際應呼叫 Claude API）

        優化項目：
        1. Title (3 options, 55-60 chars)
        2. Meta Description (157-160 chars + CTA)
        3. Internal links (3-5 relevant posts)
        4. FAQ expansion (5-7 Q&A)
        5. Image alt text
        """
        logger.info("\n[Step 3] Generating AI optimizations (sample)...")

        optimizations = []

        for i, post in enumerate(posts[:limit]):
            original_title_len = len(post.get('title', ''))

            optimization = {
                "post_id": post.get('id'),
                "original": {
                    "title": post.get('title'),
                    "title_len": original_title_len,
                    "excerpt_len": len(post.get('excerpt', '')),
                },
                "optimizations": {
                    "title_options": [
                        {
                            "text": post.get('title', '')[
                                :60
                            ],  # 截斷到 60 字示例
                            "length": min(60, original_title_len),
                            "reason": "Character optimization for SERP display",
                        },
                        {
                            "text": post.get('title', '') + " | 完整攻略",
                            "length": min(70, original_title_len + 7),
                            "reason": "Added CTA modifier",
                        },
                    ],
                    "meta_description": (
                        post.get('excerpt', '')[: 157] + "…"
                        if len(post.get('excerpt', '')) > 157
                        else post.get('excerpt', '')
                    ),
                    "internal_links": [
                        {
                            "target_post_id": 34844,
                            "anchor_text": "Kodaline 演唱會攻略",
                        },
                        {
                            "target_post_id": 34848,
                            "anchor_text": "拍謝少年台北場次",
                        },
                    ],
                    "faq_expansion": [
                        {
                            "q": f"關於「{post.get('title', '')[:20]}」的常見問題？",
                            "a": "這是生成的範例常見問題解答，實際應由 Claude API 生成詳細內容。",
                        },
                    ],
                    "image_alts": [
                        {
                            "image_id": post.get('featured_media'),
                            "alt": f"Featured image for {post.get('title', '')}",
                        }
                    ],
                },
            }

            optimizations.append(optimization)

        logger.info(f"✓ Generated {len(optimizations)} sample optimizations")
        return optimizations

    def export_optimizations(
        self, optimizations: List[Dict], output_file: str = "phase2_optimizations.jsonl"
    ) -> str:
        """導出優化結果為 JSONL"""
        logger.info(f"\n[Step 4] Exporting optimizations...")

        output_path = Path(__file__).parent / output_file
        with open(output_path, "w", encoding="utf-8") as f:
            for opt in optimizations:
                f.write(json.dumps(opt, ensure_ascii=False) + "\n")

        logger.info(f"✓ Exported {len(optimizations)} optimizations to {output_path}")
        return str(output_path)

    def prepare_batch_deployment(
        self, optimizations: List[Dict], batch_size: int = 50
    ) -> List[List[Dict]]:
        """準備分批推送"""
        logger.info(f"\n[Step 5] Preparing batch deployment...")

        batches = [
            optimizations[i : i + batch_size]
            for i in range(0, len(optimizations), batch_size)
        ]

        logger.info(f"Total batches: {len(batches)}")
        logger.info(f"Batch size: {batch_size} posts")
        logger.info(f"Deployment window: Day 10-12 (50 posts/day)")

        for i, batch in enumerate(batches, 1):
            logger.info(f"  Batch {i}: {len(batch)} posts")

        return batches

    def generate_report(self) -> str:
        """生成執行報告"""
        elapsed = (datetime.now() - self.start_time).total_seconds()

        report = f"""
================================================================================
PHASE 2 EXECUTION REPORT
================================================================================

Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Duration: {elapsed:.1f} seconds

SAMPLE DATA (Page 1 of 28):
  Posts processed: {len(self.posts)}
  Tier 1 posts: {len(self.tiers['tier_1'])} ({len(self.tiers['tier_1'])/len(self.posts)*100:.1f}%)
  Tier 2 posts: {len(self.tiers['tier_2'])} ({len(self.tiers['tier_2'])/len(self.posts)*100:.1f}%)
  Tier 3 posts: {len(self.tiers['tier_3'])} ({len(self.tiers['tier_3'])/len(self.posts)*100:.1f}%)

FULL SITE PROJECTION (28 pages × 100 posts):
  Total posts: 2,716
  Estimated Tier 1+2: {int(2716 * (len(self.tiers['tier_1']) + len(self.tiers['tier_2']))/max(len(self.posts), 1))} posts
  Cost estimate (Sonnet @ $0.10): ${int(2716 * (len(self.tiers['tier_1']) + len(self.tiers['tier_2']))/max(len(self.posts), 1)) * 0.10:.2f}

OPTIMIZATIONS GENERATED: {len(self.optimizations)} (sample)
BATCHES PREPARED: {len(self.optimizations) // 50 + (1 if len(self.optimizations) % 50 else 0)}

NEXT STEPS:
  1. Complete fetching pages 2-28 via wpcom-mcp API
  2. Run AI optimization on {int(2716 * (len(self.tiers['tier_1']) + len(self.tiers['tier_2']))/max(len(self.posts), 1))} Tier 1+2 posts
  3. Deploy batches to WordPress.com (Day 10-12)
  4. Monitor 24h for 404 errors and ranking changes

================================================================================
"""
        return report

    def run(self, posts_file: str = "posts_page1.json"):
        """執行完整 Phase 2 流程"""
        try:
            logger.info("=" * 70)
            logger.info("Phase 2: FULL SITE SEO OPTIMIZATION")
            logger.info("=" * 70)

            # Step 1: 載入文章
            logger.info("\n[Step 1] Loading posts data...")
            self.posts = self.load_posts_from_file(posts_file)
            if not self.posts:
                logger.error("No posts loaded. Exiting.")
                return 1

            # Step 2: 分層
            self.tiers = self.tier_posts(self.posts)

            # Step 3: 優化 (樣本)
            posts_to_optimize = (
                self.tiers["tier_1"] + self.tiers["tier_2"]
            )
            self.optimizations = self.generate_sample_optimizations(
                posts_to_optimize
            )

            # Step 4: 導出
            output_path = self.export_optimizations(self.optimizations)

            # Step 5: 準備批次
            batches = self.prepare_batch_deployment(self.optimizations)

            # 報告
            report = self.generate_report()
            logger.info(report)

            # 保存報告
            report_path = Path(__file__).parent / "phase2_report.txt"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)

            logger.info(f"✓ Phase 2 execution complete")
            logger.info(f"Report saved to {report_path}")
            return 0

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            return 1


if __name__ == "__main__":
    executor = Phase2Executor()
    exit_code = executor.run("posts_page1.json")
    exit(exit_code)
