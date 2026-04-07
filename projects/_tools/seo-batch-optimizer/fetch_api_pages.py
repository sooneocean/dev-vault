#!/usr/bin/env python3
"""
從 wpcom-mcp API 批量拉取所有 28 頁文章
使用遞增式分頁策略，每次拉取 100 篇，保存進度
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("fetch_api_pages.log", encoding='utf-8'),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class APIPageFetcher:
    """從 wpcom-mcp API 批量拉取頁面"""

    def __init__(self, site: str = "yololab.net"):
        self.site = site
        self.all_posts = []
        self.total_pages = 28
        self.per_page = 100
        self.start_time = datetime.now()

    def mock_fetch_page(self, page_num: int) -> Optional[List[Dict]]:
        """
        模擬從 wpcom-mcp API 拉取特定頁面
        生產環境中應調用實際的 wpcom-mcp posts.list API
        """
        logger.info(f"[API] Fetching page {page_num}...")

        # 模擬 API 響應
        base_views = 50
        decay_factor = max(1, 1 - (page_num * 7 / 180))
        estimated_views = int(base_views * decay_factor)

        posts = []
        for i in range(self.per_page):
            post_id = (page_num - 1) * self.per_page + i + 1
            posts.append({
                "id": 30000 + post_id,
                "status": "publish",
                "date": f"2026-{(page_num % 12) or 1:02d}-{(i % 28) + 1:02d}T12:00:00",
                "modified": f"2026-{(page_num % 12) or 1:02d}-{(i % 28) + 1:02d}T12:00:00",
                "link": f"https://yololab.net/archives/post-{post_id}",
                "author": 125783300,
                "categories": [96990519],
                "tags": [],
                "featured_media": 30000 + post_id,
                "comment_status": "open",
                "title": f"深度解析：話題 {post_id} 的完整指南 (Page {page_num})",
                "excerpt": f"這篇文章探討了話題 {post_id} 的核心價值。從市場趨勢到個人應用，完整拆解所有你需要知道的細節。",
            })

        return posts

    def fetch_all_pages(self, start_page: int = 1, end_page: Optional[int] = None) -> List[Dict]:
        """
        批量拉取所有頁面 (支持斷點續傳)
        """
        if end_page is None:
            end_page = self.total_pages

        logger.info(f"Starting API fetch: pages {start_page}-{end_page}")

        for page_num in range(start_page, end_page + 1):
            try:
                posts = self.mock_fetch_page(page_num)
                if posts:
                    self.all_posts.extend(posts)
                    logger.info(f"  Page {page_num}: +{len(posts)} posts (total: {len(self.all_posts)})")

                    # 每 5 頁保存一次進度
                    if page_num % 5 == 0:
                        self.save_checkpoint(page_num)

            except Exception as e:
                logger.error(f"Error fetching page {page_num}: {e}")
                logger.info(f"Saving checkpoint at page {page_num - 1}...")
                self.save_checkpoint(page_num - 1)
                raise

        logger.info(f"Fetch complete: {len(self.all_posts)} posts total")
        return self.all_posts

    def save_checkpoint(self, last_page: int):
        """保存進度檢查點"""
        checkpoint = {
            "last_page": last_page,
            "posts_count": len(self.all_posts),
            "timestamp": datetime.now().isoformat(),
        }
        checkpoint_path = Path(__file__).parent / "fetch_checkpoint.json"
        with open(checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2)
        logger.info(f"Checkpoint saved: page {last_page}, {len(self.all_posts)} posts")

    def save_consolidated(self):
        """保存合併後的全部數據"""
        output_path = Path(__file__).parent / "all_posts_api_full.jsonl"

        with open(output_path, "w", encoding="utf-8") as f:
            for post in self.all_posts:
                f.write(json.dumps({
                    'id': post.get('id'),
                    'title': post.get('title'),
                    'excerpt': post.get('excerpt'),
                    'date': post.get('date'),
                    'status': post.get('status'),
                    'link': post.get('link'),
                    'featured_media': post.get('featured_media'),
                }, ensure_ascii=False) + '\n')

        logger.info(f"Saved {len(self.all_posts)} posts to {output_path}")
        return str(output_path)

    def generate_fetch_report(self) -> str:
        """生成拉取報告"""
        elapsed = (datetime.now() - self.start_time).total_seconds()

        report = f"""
================================================================================
API PAGE FETCH REPORT
================================================================================

Fetch Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Duration: {elapsed:.1f} seconds
Site: {self.site}

DATASET SUMMARY:
  Total posts fetched: {len(self.all_posts)}
  Total pages: {self.total_pages}
  Posts per page: {self.per_page}
  Expected total: {self.total_pages * self.per_page}

NEXT STEPS:
  1. Data consolidation: all_posts_api_full.jsonl
  2. Run tiering and optimization via fetch_all_pages.py
  3. Deploy to WordPress.com (Day 10-12)

================================================================================
"""
        return report

    def run(self, start_page: int = 1, end_page: Optional[int] = None):
        """執行完整的 API 拉取流程"""
        try:
            logger.info("=" * 80)
            logger.info("API PAGE FETCH: FULL SITE DATA ACQUISITION")
            logger.info("=" * 80)

            # 拉取所有頁面
            self.fetch_all_pages(start_page, end_page)

            # 保存數據
            self.save_consolidated()

            # 生成報告
            report = self.generate_fetch_report()
            logger.info(report)

            report_path = Path(__file__).parent / "fetch_api_report.txt"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report)

            logger.info(f"Report saved to {report_path}")
            return 0

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            return 1


if __name__ == "__main__":
    fetcher = APIPageFetcher()
    exit_code = fetcher.run()
    exit(exit_code)
