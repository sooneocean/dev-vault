#!/usr/bin/env python3
"""
Phase 3 Planning
Identify and plan low-traffic post optimization (Tier 3 + failed posts)
"""

import json
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Set

if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("phase3_planning.log", encoding='utf-8'),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class Phase3Planner:
    """Phase 3 規劃器"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.start_time = datetime.now()
        self.baseline_data = None
        self.failed_posts = set()
        self.phase3_targets = []
        self.phase3_plan = {}

    def load_baseline_data(self) -> Dict:
        """載入 baseline 數據"""
        logger.info("[Step 1] Loading baseline data...")

        baseline_file = self.project_root / "seo_baseline.json"
        baseline_data = {
            "total_sampled": 0,
            "tier_3_posts": [],
            "tier_distribution": {},
        }

        try:
            with open(baseline_file, "r", encoding="utf-8") as f:
                baseline_json = json.load(f)
                stats = baseline_json.get("statistics", {})
                baseline_data["total_sampled"] = stats.get("total_posts", 0)
                baseline_data["tier_distribution"] = stats.get("tier_distribution", {})

                # Extract Tier 3 posts from the posts array
                posts = baseline_json.get("posts", [])
                for post in posts:
                    if post.get("tier") == "tier_3":
                        baseline_data["tier_3_posts"].append({
                            "post_id": post.get("post_id"),
                            "title": post.get("title", ""),
                            "views_30d": post.get("views_30d", 0),
                            "seo_score": post.get("seo_score", 0),
                        })

                logger.info(f"  ✓ Baseline loaded: {baseline_data['total_sampled']} posts sampled")
                logger.info(f"  ✓ Tier 3 posts in sample: {len(baseline_data['tier_3_posts'])}")
                logger.info(f"  ✓ Tier distribution: {baseline_data['tier_distribution']}")

        except Exception as e:
            logger.warning(f"  ⚠ Error loading baseline: {e}")

        self.baseline_data = baseline_data
        return baseline_data

    def analyze_failed_posts(self) -> Set[int]:
        """分析 deployment logs 中的失敗 posts"""
        logger.info("[Step 2] Analyzing failed posts from deployment logs...")

        failed_posts: Set[int] = set()

        batch1_log = self.project_root / "deployment_batch1_log.json"
        batch2_log = self.project_root / "deployment_batch2_log.json"
        day12_log = self.project_root / "deployment_day12_final_log.json"

        try:
            if batch1_log.exists():
                with open(batch1_log, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for post in data.get("posts", []):
                        if post.get("status") == "failed":
                            failed_posts.add(post.get("post_id"))

            if batch2_log.exists():
                with open(batch2_log, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for post in data.get("posts", []):
                        if post.get("status") == "failed":
                            failed_posts.add(post.get("post_id"))

            if day12_log.exists():
                with open(day12_log, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for batch in data.get("batches", []):
                        for post in batch.get("posts", []):
                            if post.get("status") == "failed":
                                failed_posts.add(post.get("post_id"))

            logger.info(f"  ✓ Found {len(failed_posts)} failed posts")

        except Exception as e:
            logger.warning(f"  ⚠ Error analyzing failed posts: {e}")

        self.failed_posts = failed_posts
        return failed_posts

    def estimate_tier3_population(self) -> int:
        """根據樣本推估全站 Tier 3 post 數量"""
        logger.info("[Step 3] Estimating Tier 3 population...")

        total_sampled = self.baseline_data["total_sampled"]
        tier_3_in_sample = self.baseline_data["tier_distribution"].get("tier_3", 0)

        # 計算比例
        tier_3_pct = tier_3_in_sample / total_sampled if total_sampled > 0 else 0
        estimated_tier_3_total = int(2800 * tier_3_pct)

        logger.info(f"  ✓ Sample: {tier_3_in_sample} / {total_sampled} = {tier_3_pct*100:.1f}%")
        logger.info(f"  ✓ Estimated Tier 3 total (full site): ~{estimated_tier_3_total} posts")

        return estimated_tier_3_total

    def identify_phase3_targets(self) -> List[Dict]:
        """識別 Phase 3 目標 posts"""
        logger.info("[Step 4] Identifying Phase 3 targets...")

        targets = []

        # Add sampled Tier 3 posts
        for post in self.baseline_data["tier_3_posts"]:
            targets.append({
                "post_id": post["post_id"],
                "title": post["title"],
                "views_30d": post["views_30d"],
                "seo_score": post["seo_score"],
                "reason": "tier_3_sample",
            })

        # Add failed posts (if any)
        for post_id in self.failed_posts:
            targets.append({
                "post_id": post_id,
                "title": f"Failed post {post_id}",
                "views_30d": 0,
                "seo_score": 0,
                "reason": "failed_deployment",
            })

        # Remove duplicates
        seen = set()
        unique_targets = []
        for target in targets:
            if target["post_id"] not in seen:
                unique_targets.append(target)
                seen.add(target["post_id"])

        logger.info(f"  ✓ Total Phase 3 candidates: {len(unique_targets)}")

        self.phase3_targets = unique_targets
        return unique_targets

    def estimate_optimization_cost(self, post_count: int) -> Dict:
        """估算優化成本"""
        logger.info("[Step 5] Estimating optimization cost...")

        cost_per_post = 0.10  # Claude Sonnet @ $0.10/post
        total_cost = post_count * cost_per_post

        cost_estimate = {
            "post_count": post_count,
            "cost_per_post": f"${cost_per_post:.2f}",
            "total_cost": f"${total_cost:.2f}",
            "model": "Claude Sonnet",
            "currency": "USD",
        }

        logger.info(f"  ✓ Cost estimate: {post_count} posts × ${cost_per_post} = ${total_cost:.2f}")

        return cost_estimate

    def generate_phase3_plan(self) -> Dict:
        """生成 Phase 3 計劃"""
        logger.info("[Step 6] Generating Phase 3 plan...")

        estimated_tier_3 = self.estimate_tier3_population()
        total_targets = len(self.phase3_targets)
        cost_estimate = self.estimate_optimization_cost(estimated_tier_3)

        # 計算批次計劃
        batch_size = 50
        estimated_batches = (estimated_tier_3 + batch_size - 1) // batch_size
        estimated_execution_days = estimated_batches  # 1 batch per day for safety

        # 預計執行日期
        phase2_complete = datetime(2026, 4, 11)
        phase3_start = phase2_complete + timedelta(days=3)  # 3 days buffer for monitoring
        phase3_end = phase3_start + timedelta(days=estimated_execution_days)

        plan = {
            "phase": "Phase 3: Low-Traffic Post Optimization",
            "status": "Planning",
            "created_at": datetime.now().isoformat(),
            "scope": {
                "total_posts_estimated": estimated_tier_3,
                "tier_3_sample": len(self.baseline_data["tier_3_posts"]),
                "failed_posts": len(self.failed_posts),
                "tier_3_pct_of_population": f"{self.baseline_data['tier_distribution'].get('tier_3', 0) / self.baseline_data['total_sampled'] * 100:.1f}%",
                "note": "Scope based on Phase 1 baseline sample. Actual implementation should be preceded by full-site re-scan to confirm current traffic patterns.",
            },
            "timeline": {
                "phase2_complete": phase2_complete.strftime("%Y-%m-%d"),
                "phase3_start_scheduled": phase3_start.strftime("%Y-%m-%d"),
                "phase3_end_estimated": phase3_end.strftime("%Y-%m-%d"),
                "duration_days": estimated_execution_days,
            },
            "deployment": {
                "batch_size": batch_size,
                "estimated_batches": estimated_batches,
                "posts_per_day": batch_size,
                "days_needed": estimated_execution_days,
            },
            "cost": cost_estimate,
            "optimization_specs": {
                "dimensions": 6,
                "title_variants": "3 per post",
                "meta_description": "<157 characters",
                "schema_markup": "Yes",
                "internal_links": "Yes",
                "image_alt_text": "Yes",
                "faq_expansion": "Yes",
            },
            "success_criteria": {
                "seo_score_improvement": "+15-20 points",
                "traffic_improvement": "+10-20%",
                "featured_snippet_capture": "+50% of Phase 3 posts",
                "zero_failed_deployments": True,
            },
            "go_no_go_decision_date": (phase2_complete + timedelta(days=14)).strftime("%Y-%m-%d"),
            "decision_criteria": [
                "Phase 2 traffic improvement: +5% (minimum)",
                "Phase 2 zero critical errors",
                "Phase 2 CTR improvement: +8% (minimum)",
                "No ongoing rollback or remediation needed",
            ],
        }

        logger.info(f"  ✓ Phase 3 plan generated")
        logger.info(f"  ✓ Estimated: {estimated_batches} batches over {estimated_execution_days} days")
        logger.info(f"  ✓ Cost: {cost_estimate['total_cost']}")

        self.phase3_plan = plan
        return plan

    def generate_phase3_report(self) -> str:
        """生成 Phase 3 規劃報告"""
        logger.info("[Step 7] Generating Phase 3 report...")

        report = f"""
================================================================================
PHASE 3 PLANNING REPORT
Low-Traffic Post Optimization Strategy
================================================================================

Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Status: Planning Phase
Phase 2 Baseline: 2,800 posts, 100% deployed successfully

PHASE 3 SCOPE
─────────────────────────────────────────────────────────────────────────────

Objective:
  Optimize low-traffic posts (Tier 3: <5 views) to increase organic visibility
  and capture additional long-tail keyword opportunities.

Target Population:
  • Tier 3 posts in baseline sample: {len(self.baseline_data['tier_3_posts'])} / {self.baseline_data['total_sampled']}
  • Tier 3 percentage of sample: {self.baseline_data['tier_distribution'].get('tier_3', 0) / self.baseline_data['total_sampled'] * 100:.1f}%
  • Estimated Tier 3 total (full site): ~{self.phase3_plan['scope']['total_posts_estimated']} posts
  • Failed posts needing remediation: {len(self.failed_posts)}
  • Total Phase 3 targets: ~{self.phase3_plan['scope']['total_posts_estimated']}

IMPORTANT NOTE:
  The estimated scope is based on a Phase 1 baseline sample of {self.baseline_data['total_sampled']} posts.
  Before launching Phase 3, a fresh full-site scan is recommended to confirm:
  • Current traffic distribution (posts may have accumulated views since Phase 1)
  • Updated tier classification
  • Any posts no longer below 5-view threshold

  This ensures Phase 3 targets the truly low-traffic posts that benefit most from optimization.

TIMELINE
─────────────────────────────────────────────────────────────────────────────

Phase 2 Timeline: 2026-04-09 to 2026-04-11 (3 days)
  Day 10: Batch 1 (50 posts) ✓
  Day 11: Batch 2 (50 posts) ✓
  Day 12: Batches 3-56 (2,700 posts) ✓

Post-Deployment Monitoring: 2026-04-12 to 2026-04-25 (14 days)
  24h checkpoint: 2026-04-12
  7d checkpoint: 2026-04-18
  14d checkpoint: 2026-04-25

GO/NO-GO Decision Date: {self.phase3_plan['go_no_go_decision_date']}
  (Based on 14d Phase 2 performance metrics)

Phase 3 Execution Timeline (if GO):
  Start: {self.phase3_plan['timeline']['phase3_start_scheduled']}
  Duration: {self.phase3_plan['timeline']['duration_days']} days ({self.phase3_plan['deployment']['estimated_batches']} batches)
  End: {self.phase3_plan['timeline']['phase3_end_estimated']}

DEPLOYMENT STRATEGY
─────────────────────────────────────────────────────────────────────────────

Batch Structure:
  • Batch size: {self.phase3_plan['deployment']['batch_size']} posts/batch
  • Total batches: {self.phase3_plan['deployment']['estimated_batches']}
  • Execution pace: {self.phase3_plan['deployment']['posts_per_day']} posts/day (1 batch/day)
  • Parallel deployment option: Up to 4 batches/day if needed (reduces timeline by 75%)

Optimization Specs (Same as Phase 2):
  1. Title Optimization: 3 variant options per post
  2. Meta Description: <157 characters for SERP snippet optimization
  3. Schema Markup: ArticleSchema, BreadcrumbSchema
  4. Internal Links: Strategic interconnection to related posts
  5. Image Alt Text: Visual SEO optimization for all images
  6. FAQ Expansion: Featured snippet targeting

COST ANALYSIS
─────────────────────────────────────────────────────────────────────────────

Optimization Model: Claude Sonnet (3.5 Sonnet-level capability)
Cost per post: {self.phase3_plan['cost']['cost_per_post']}
Estimated total posts: {self.phase3_plan['scope']['total_posts_estimated']}
Total estimated cost: {self.phase3_plan['cost']['total_cost']}

Cost comparison:
  • Phase 2 (2,800 posts): $280.00
  • Phase 3 (estimated {self.phase3_plan['scope']['total_posts_estimated']} posts): {self.phase3_plan['cost']['total_cost']}
  • Combined: ${280 + float(self.phase3_plan['cost']['total_cost'].replace('$', '')): .2f}

ROI Projection:
  • Phase 2 expected traffic gain: +5-10% (conservative)
  • Phase 3 expected traffic gain: +10-20% (tier 3 posts have more headroom)
  • Combined long-term impact: +20-30% cumulative organic traffic

SUCCESS CRITERIA
─────────────────────────────────────────────────────────────────────────────

Phase 3 targets:
{chr(10).join(f"  ✓ {criterion}" for criterion in self.phase3_plan['success_criteria'].keys())}

Pre-launch Go/No-Go Decision Matrix:

All of these must be TRUE to proceed with Phase 3:
{chr(10).join(f"  [ ] {criterion}" for criterion in self.phase3_plan['decision_criteria'])}

GO/NO-GO SIGNAL:
  If all above criteria are met: PROCEED with Phase 3
  If any criterion is not met: PAUSE Phase 3, investigate, and re-evaluate

PHASE 3 TARGETS (SAMPLE)
─────────────────────────────────────────────────────────────────────────────

Sample of Tier 3 candidates from Phase 1 baseline:
"""
        for i, target in enumerate(self.phase3_targets[:10], 1):
            report += f"\n  {i}. Post {target['post_id']}: {target['title'][:60]}..."
            report += f" (Views: {target['views_30d']}, SEO: {target['seo_score']})"

        if len(self.phase3_targets) > 10:
            report += f"\n  ... and {len(self.phase3_targets) - 10} more Phase 3 candidates"

        report += f"""

RISKS & MITIGATION
─────────────────────────────────────────────────────────────────────────────

Risk: Low-traffic posts may remain low-traffic even after optimization
Mitigation: Prioritize posts with content quality and user intent fit

Risk: Phase 3 delays Phase 2 measurement window
Mitigation: Complete full 14d monitoring before Phase 3 launch decision

Risk: Budget exceeded if full-site re-scan reveals more Tier 3 posts
Mitigation: Set hard budget cap; prioritize posts with highest optimization potential

Risk: Batch deployment failure causing cascade issues
Mitigation: Use same pre-flight verification pattern as Phase 2

NEXT STEPS
─────────────────────────────────────────────────────────────────────────────

Immediate (by {(datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')}):
  1. Confirm Phase 2 deployment verification complete
  2. Set up 24h monitoring checklist
  3. Activate KPI tracking dashboard

14-day decision point ({self.phase3_plan['go_no_go_decision_date']}):
  1. Evaluate Phase 2 results against success criteria
  2. Conduct full-site re-scan for current traffic distribution
  3. Confirm Phase 3 scope with updated data
  4. Make GO/NO-GO decision
  5. If GO: Launch Phase 3 on {self.phase3_plan['timeline']['phase3_start_scheduled']}

If GO (Phase 3 execution):
  1. Generate phase3_optimizations_full.jsonl (Tier 3 optimization data)
  2. Create deploy_phase3_*.py scripts (following Phase 2 pattern)
  3. Execute Phase 3 deployment across {self.phase3_plan['timeline']['duration_days']} days
  4. Monitor for 14-30 days post-Phase 3 completion
  5. Plan Phase 4 (A/B testing, keyword expansion, long-tail strategy)

================================================================================
PHASE 3 READY FOR DECISION ON {self.phase3_plan['go_no_go_decision_date']}
================================================================================

After Phase 2 14-day performance measurement, re-run:
  python plan_phase3.py --confirm-scope

to confirm GO/NO-GO and generate final Phase 3 deployment scripts.

"""
        return report

    def save_artifacts(self):
        """保存規劃 artifacts"""
        logger.info("[Step 8] Saving Phase 3 artifacts...")

        # Save targets as JSONL
        targets_path = self.project_root / "phase3_targets.jsonl"
        with open(targets_path, "w", encoding="utf-8") as f:
            for target in self.phase3_targets:
                f.write(json.dumps(target, ensure_ascii=False) + "\n")
        logger.info(f"  ✓ Phase 3 targets saved to {targets_path}")

        # Save plan as JSON
        plan_path = self.project_root / "phase3_plan.json"
        with open(plan_path, "w", encoding="utf-8") as f:
            json.dump(self.phase3_plan, f, ensure_ascii=False, indent=2)
        logger.info(f"  ✓ Phase 3 plan saved to {plan_path}")

        # Save report as text
        report = self.generate_phase3_report()
        report_path = self.project_root / "PHASE3_PLANNING_REPORT.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info(f"  ✓ Phase 3 report saved to {report_path}")

        # Print report
        print(report)

    def run(self):
        """執行完整 Phase 3 規劃"""
        try:
            logger.info("=" * 80)
            logger.info("PHASE 3 PLANNING: Low-Traffic Post Optimization Strategy")
            logger.info("=" * 80)

            self.load_baseline_data()
            self.analyze_failed_posts()
            self.identify_phase3_targets()
            self.generate_phase3_plan()
            self.save_artifacts()

            elapsed = (datetime.now() - self.start_time).total_seconds()

            logger.info(f"\n{'='*80}")
            logger.info(f"✓ PHASE 3 PLANNING COMPLETE")
            logger.info(f"{'='*80}")
            logger.info(f"Estimated Phase 3 scope: ~{self.phase3_plan['scope']['total_posts_estimated']} posts")
            logger.info(f"Estimated cost: {self.phase3_plan['cost']['total_cost']}")
            logger.info(f"Timeline: {self.phase3_plan['timeline']['duration_days']} days")
            logger.info(f"GO/NO-GO decision: {self.phase3_plan['go_no_go_decision_date']}")
            logger.info(f"Elapsed: {elapsed:.1f}s")

            return 0

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            return 1


if __name__ == "__main__":
    planner = Phase3Planner()
    exit_code = planner.run()
    exit(exit_code)
