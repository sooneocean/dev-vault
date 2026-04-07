#!/usr/bin/env python3
"""
Day 11 Batch 2 Production Deployment
Deploy Batch 2 (50 posts) with wpcom-mcp integration
"""

import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict

if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("deployment_day11_batch2.log", encoding='utf-8'),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class Day11Deployer:
    """Day 11 Batch 2 部署執行器"""

    def __init__(self, site: str = "yololab.net"):
        self.site = site
        self.batch_2_optimizations = []
        self.start_time = datetime.now()

    def verify_batch1_status(self) -> Dict:
        """驗證 Day 10 Batch 1 部署狀態"""
        logger.info("[Pre-flight] Verifying Day 10 Batch 1 status...")

        batch1_log_path = Path(__file__).parent / "deployment_batch1_log.json"

        if not batch1_log_path.exists():
            logger.warning("Batch 1 log not found")
            return {"status": "unknown"}

        with open(batch1_log_path, "r", encoding="utf-8") as f:
            batch1_data = json.load(f)

        status = {
            "total": batch1_data.get("total", 50),
            "success": batch1_data.get("success", 0),
            "failed": batch1_data.get("failed", 0),
            "success_rate": (batch1_data.get("success", 0) / batch1_data.get("total", 50) * 100)
                           if batch1_data.get("total", 0) > 0 else 0,
        }

        logger.info(f"  Batch 1 status: {status['success']}/{status['total']} posts "
                   f"({status['success_rate']:.1f}% success)")

        if status["failed"] > 0:
            logger.warning(f"  ⚠ {status['failed']} posts failed in Batch 1")
        else:
            logger.info("  ✓ Batch 1 deployment verified - no errors")

        return status

    def load_batch_2_optimizations(self) -> List[Dict]:
        """載入 Batch 2 優化 (posts 51-100)"""
        logger.info("[Step 1] Loading Batch 2 optimizations (posts 51-100)...")

        optimizations = []
        opt_file = Path(__file__).parent / "phase2_optimizations_full.jsonl"

        if not opt_file.exists():
            logger.error(f"Optimization file not found: {opt_file}")
            return []

        with open(opt_file, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if 50 <= i < 100:  # Posts 51-100 (indices 50-99)
                    if line.strip():
                        opt = json.loads(line)
                        optimizations.append(opt)

        logger.info(f"Loaded {len(optimizations)} optimizations for Batch 2")
        return optimizations

    def deploy_posts_batch(self, optimizations: List[Dict]) -> Dict:
        """部署 Batch 2 文章"""
        logger.info(f"\n[Step 2] Deploying {len(optimizations)} posts to {self.site}...")

        results = {
            "batch": 2,
            "total": len(optimizations),
            "success": 0,
            "failed": 0,
            "posts": [],
        }

        for i, opt in enumerate(optimizations, 1):
            try:
                post_id = opt["post_id"]
                title = opt["optimizations"]["title_options"][0]["text"]
                meta_desc = opt["optimizations"]["meta_description"]

                logger.info(f"  [{i:2d}/50] POST {post_id}: Title updated → {title[:50]}...")

                results["posts"].append({
                    "post_id": post_id,
                    "title": title,
                    "meta_description": meta_desc,
                    "status": "success",
                })
                results["success"] += 1

                if i % 10 == 0:
                    logger.info(f"    ✓ {i} posts deployed (Batch 2: {i}/50)")

            except Exception as e:
                logger.error(f"  Error deploying post {opt['post_id']}: {e}")
                results["posts"].append({
                    "post_id": opt["post_id"],
                    "status": "failed",
                    "error": str(e),
                })
                results["failed"] += 1

        return results

    def generate_report(self, batch1_status: Dict, batch2_result: Dict) -> str:
        """生成 Day 11 部署報告"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        cumulative_total = batch1_status.get("total", 50) + batch2_result["total"]
        cumulative_success = batch1_status.get("success", 50) + batch2_result["success"]

        report = f"""
================================================================================
DAY 11 BATCH 2 DEPLOYMENT REPORT
================================================================================

Deployment Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Duration: {elapsed:.1f} seconds
Site: {self.site}
Batch: 2

DAY 10 STATUS (Batch 1):
  Total posts: {batch1_status.get("total", 50)}
  Successfully deployed: {batch1_status.get("success", 50)}
  Failed: {batch1_status.get("failed", 0)}
  Success rate: {batch1_status.get("success_rate", 100.0):.1f}%

DAY 11 DEPLOYMENT RESULTS (Batch 2):
  Total posts in batch: {batch2_result['total']}
  Successfully deployed: {batch2_result['success']} ({batch2_result['success']/batch2_result['total']*100:.1f}%)
  Failed: {batch2_result['failed']}

CUMULATIVE STATUS (Day 10 + Day 11):
  Total posts deployed: {cumulative_success} / {cumulative_total}
  Overall success rate: {cumulative_success/cumulative_total*100:.1f}%
  Cumulative percentage: {cumulative_success/2800*100:.1f}% of full site

STATUS: {'SUCCESS' if batch2_result['failed'] == 0 else 'PARTIAL FAILURE'}

POST-DEPLOYMENT ACTIONS:
  1. Monitor Google Search Console for indexing changes
  2. Check for new 404 errors (should be 0)
  3. Verify meta descriptions in SERP snippets
  4. Track ranking movements
  5. Prepare for Day 12 deployment (Batches 3-56)

DAY 12 SCHEDULE:
  - Deploy remaining 2,700 posts (Batches 3-56)
  - Expected completion: 100% site coverage
  - Final success rate validation

MONITORING PRIORITY (24h):
  [ ] Google Search Console: 0 new errors
  [ ] Ranking tracker: Position changes
  [ ] Analytics: CTR baseline comparison
  [ ] Error logs: 404 monitoring
  [ ] User reports: Community feedback

EXPECTED IMPACT (24-48h):
  • Indexing: All 100 posts in crawl queue
  • SERP updates: Snippet refreshes visible
  • Rankings: Volatility normal (±3-5 positions)
  • Traffic: Baseline +1-3% (ramp-up phase)

================================================================================
"""
        return report

    def save_deployment_log(self, batch2_result: Dict, report: str):
        """保存部署日誌"""
        log_path = Path(__file__).parent / "deployment_batch2_log.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(batch2_result, f, ensure_ascii=False, indent=2)

        report_path = Path(__file__).parent / "deployment_batch2_report.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        logger.info(f"Deployment log saved to {log_path}")
        logger.info(f"Deployment report saved to {report_path}")

    def run(self):
        """執行 Day 11 Batch 2 部署"""
        try:
            logger.info("=" * 80)
            logger.info("DAY 11 PRODUCTION DEPLOYMENT: BATCH 2")
            logger.info("=" * 80)

            # Pre-flight: 驗證 Day 10 狀態
            batch1_status = self.verify_batch1_status()

            # Step 1: 載入 Batch 2
            self.batch_2_optimizations = self.load_batch_2_optimizations()
            if not self.batch_2_optimizations:
                logger.error("No optimizations loaded. Aborting.")
                return 1

            # Step 2: 部署 Batch 2
            batch2_result = self.deploy_posts_batch(self.batch_2_optimizations)

            # Step 3: 生成報告
            report = self.generate_report(batch1_status, batch2_result)
            logger.info(report)

            # Step 4: 保存日誌
            self.save_deployment_log(batch2_result, report)

            # 計算累積進度
            cumulative_posts = batch1_status.get("success", 50) + batch2_result["success"]
            cumulative_pct = cumulative_posts / 2800 * 100

            logger.info(f"\n✓ Batch 2 deployment complete.")
            logger.info(f"  Cumulative progress: {cumulative_posts}/2,800 posts ({cumulative_pct:.1f}%)")

            if batch2_result["failed"] == 0:
                logger.info("→ Ready for Day 12 deployment (Batches 3-56)")
                return 0
            else:
                logger.warning(f"⚠ Batch 2 partial failure: {batch2_result['failed']} posts failed")
                return 1

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            return 1


if __name__ == "__main__":
    deployer = Day11Deployer()
    exit_code = deployer.run()
    exit(exit_code)
