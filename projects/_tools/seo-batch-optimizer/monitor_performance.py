#!/usr/bin/env python3
"""
Performance Monitoring Framework
Track KPI progress at 24h, 7d, 14d, 30d checkpoints
Support manual observation recording for GSC data, rankings, traffic
"""

import json
import logging
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("monitoring.log", encoding='utf-8'),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """性能監控框架"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.baseline_data = None
        self.deployment_summary = None
        self.observations = []

    def load_baseline(self) -> Dict:
        """載入 SEO baseline"""
        logger.info("[Loading] SEO Baseline data...")

        baseline_file = self.project_root / "seo_baseline.json"
        baseline_data = {
            "avg_seo_score": 0,
            "avg_views_30d": 0,
            "tier_distribution": {},
            "top_issues": {},
        }

        try:
            with open(baseline_file, "r", encoding="utf-8") as f:
                baseline_json = json.load(f)
                stats = baseline_json.get("statistics", {})
                baseline_data["avg_seo_score"] = stats.get("avg_seo_score", 0)
                baseline_data["avg_views_30d"] = stats.get("avg_views_30d", 0)
                baseline_data["tier_distribution"] = stats.get("tier_distribution", {})
                baseline_data["top_issues"] = stats.get("top_issues", {})
                logger.info(f"  ✓ Baseline loaded: SEO score {baseline_data['avg_seo_score']:.1f}, "
                           f"views {baseline_data['avg_views_30d']:.1f}")
        except Exception as e:
            logger.warning(f"  ⚠ Error loading baseline: {e}")

        self.baseline_data = baseline_data
        return baseline_data

    def load_deployment_summary(self) -> Dict:
        """載入部署摘要"""
        logger.info("[Loading] Deployment summary...")

        summary = {
            "total_posts": 0,
            "success_count": 0,
            "failed_count": 0,
            "success_rate": 0.0,
            "batch_count": 0,
            "execution_days": 3,
        }

        batch1_log = self.project_root / "deployment_batch1_log.json"
        batch2_log = self.project_root / "deployment_batch2_log.json"
        day12_log = self.project_root / "deployment_day12_final_log.json"

        try:
            if batch1_log.exists():
                with open(batch1_log, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    summary["total_posts"] += data.get("total", 0)
                    summary["success_count"] += data.get("success", 0)
                    summary["failed_count"] += data.get("failed", 0)
                    summary["batch_count"] += 1

            if batch2_log.exists():
                with open(batch2_log, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    summary["total_posts"] += data.get("total", 0)
                    summary["success_count"] += data.get("success", 0)
                    summary["failed_count"] += data.get("failed", 0)
                    summary["batch_count"] += 1

            if day12_log.exists():
                with open(day12_log, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    summary["total_posts"] += data.get("total_posts", 0)
                    summary["success_count"] += data.get("total_success", 0)
                    summary["failed_count"] += data.get("total_failed", 0)
                    summary["batch_count"] += data.get("total_batches", 0)

            summary["success_rate"] = (summary["success_count"] / summary["total_posts"] * 100
                                      if summary["total_posts"] > 0 else 0)
            logger.info(f"  ✓ Deployment: {summary['total_posts']} posts, "
                       f"{summary['success_rate']:.1f}% success")

        except Exception as e:
            logger.warning(f"  ⚠ Error loading deployment summary: {e}")

        self.deployment_summary = summary
        return summary

    def load_observations(self) -> List[Dict]:
        """載入既有的觀測數據"""
        obs_file = self.project_root / "monitoring_observations.jsonl"
        observations = []

        try:
            if obs_file.exists():
                with open(obs_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            observations.append(json.loads(line))
                logger.info(f"  ✓ Loaded {len(observations)} existing observations")
        except Exception as e:
            logger.warning(f"  ⚠ Error loading observations: {e}")

        self.observations = observations
        return observations

    def generate_checklist_24h(self) -> str:
        """生成 24h 監控清單"""
        deployment_date = datetime(2026, 4, 11)
        checkpoint_date = deployment_date + timedelta(hours=24)

        checklist = f"""
================================================================================
MONITORING CHECKLIST: 24h Checkpoint
================================================================================

Target Date: {checkpoint_date.strftime('%Y-%m-%d %H:%M')}
Purpose: Verify initial indexing and technical integrity post-deployment

TECHNICAL CHECKS
─────────────────────────────────────────────────────────────────────────────
[ ] Google Search Console Errors
    • Login to GSC for {'{'}yololab.net{'}'}
    • Check "Coverage" tab
    • Expected: 0 new 404 errors from deployed posts
    • Log finding: gsc_404_errors = [actual count]

[ ] Indexation Queue Status
    • Check "Pages" > "Coverage" for 2,800 posts
    • Verify Batch 1-2 (100 posts) are in "Discovered" or "Indexed"
    • Log finding: batch_1_2_indexation_status = "[status]"

[ ] Crawl Errors
    • Check "Crawl stats" tab
    • Verify no new crawl errors on deployed posts
    • Log finding: crawl_errors_count = [actual count]

SERP VERIFICATION (Sample 10 Posts)
─────────────────────────────────────────────────────────────────────────────
Run Google search for each post and verify:

Post ID 30001: [Check SERP title]
  • Title appears optimized: [Yes/No]
  • Meta description showing: [Yes/No]
  • Snippet length correct: [Yes/No]

(Repeat for posts: 30005, 30010, 30020, 30030, 30040, 30050, 30051, 30075, 30100)

Summary: [X]/10 posts have updated SERP snippets

TECHNICAL AUDITS
─────────────────────────────────────────────────────────────────────────────
[ ] Mobile Rendering
    • Google Mobile-Friendly Test (test up to 5 posts)
    • Expected: All pass (100%)
    • Result: [Pass/Fail]

[ ] No Redirect Chains
    • Check sample posts for 301/302 chains
    • Expected: Direct to canonical
    • Result: [Pass/Fail]

[ ] Core Web Vitals Status
    • Check PageSpeed Insights for sample posts
    • Expected: No regression vs pre-deployment
    • Result: [No change/Improved/Degraded]

INTERNAL LINK VERIFICATION
─────────────────────────────────────────────────────────────────────────────
[ ] Internal Links Working
    • Spot-check 5 internal links in Batch 1
    • All should be 200 OK (no 404)
    • Result: [Pass/Fail]

PERFORMANCE BASELINE (Optional)
─────────────────────────────────────────────────────────────────────────────
[ ] Analytics Dashboard Check
    • Login to Google Analytics
    • Set date range: Last 24h
    • Screenshot baseline metrics (for later comparison)
    • Sessions, Users, Pageviews, Avg Duration, Bounce Rate

================================================================================
SUMMARY & NEXT STEPS
================================================================================

24h Status: [GREEN/YELLOW/RED]

Critical Issues Found: [0/specify]
  If any: [list issues]

Next Checkpoint: 7d ({(deployment_date + timedelta(days=7)).strftime('%Y-%m-%d')})

To record observations:
  python monitor_performance.py --record-observation gsc_404_errors 0 --date {checkpoint_date.strftime('%Y-%m-%d')}
  python monitor_performance.py --record-observation batch_1_2_indexation_status "Indexed" --date {checkpoint_date.strftime('%Y-%m-%d')}

================================================================================
"""
        return checklist

    def generate_checklist_7d(self) -> str:
        """生成 7d 監控清單"""
        deployment_date = datetime(2026, 4, 11)
        checkpoint_date = deployment_date + timedelta(days=7)

        checklist = f"""
================================================================================
MONITORING CHECKLIST: 7d Checkpoint
================================================================================

Target Date: {checkpoint_date.strftime('%Y-%m-%d')}
Purpose: Early performance signals and ranking monitoring

INDEXATION COVERAGE
─────────────────────────────────────────────────────────────────────────────
[ ] GSC Coverage Status
    • Check "Coverage" tab in GSC
    • Target: >95% of 2,800 posts indexed
    • Actual count indexed: [___] / 2,800 ({'{'}____%{'}'}')
    • Status: [On track / Behind / Ahead]

RANKING POSITION TRACKING
─────────────────────────────────────────────────────────────────────────────
[ ] Keyword Position Snapshot
    • Use ranking tracker or Google Search Console Performance tab
    • Track top 50 keywords from Batch 1-2 (100 posts)
    • Baseline positions (from pre-deployment): [snapshot file]
    • Current positions (7d): [snapshot file]
    • Avg position change: [___ positions]
    • Status: [Stable / Moving up / Moving down / Volatile]

FEATURED SNIPPET CAPTURE
─────────────────────────────────────────────────────────────────────────────
[ ] Position 0 Tracking
    • Check which posts now own featured snippets
    • Run: site:yololab.net "answer box" OR "rich snippet" on Google
    • Count: [___] featured snippets captured
    • Target: >50
    • Status: [On track / Need adjustment]

CTR BASELINE MEASUREMENT
─────────────────────────────────────────────────────────────────────────────
[ ] Google Search Console Performance Tab
    • Date range: 2026-04-11 to 2026-04-18 (first 7 days)
    • Metric: Average CTR for deployed posts
    • Baseline CTR (pre-deployment): [___]%
    • Current CTR (7d average): [___]%
    • Delta: [___]% (target: +8-15%)

CORE WEB VITALS TREND
─────────────────────────────────────────────────────────────────────────────
[ ] PageSpeed Insights (Re-audit sample posts)
    • Desktop scores: [LCP / FID / CLS]
    • Mobile scores: [LCP / FID / CLS]
    • Change vs 24h: [Same / Improved / Degraded]

USER BEHAVIOR BASELINE
─────────────────────────────────────────────────────────────────────────────
[ ] Analytics Metrics (First 7 days)
    • Total users (optimized posts): [___]
    • Total sessions: [___]
    • Avg session duration: [__._] minutes
    • Bounce rate: [__]%
    • Pages/session: [_._]

================================================================================
SUMMARY & DECISION POINT
================================================================================

7d Overall Status: [GREEN / YELLOW / RED]

Key Findings:
  • Indexation: [___]% complete
  • Avg ranking change: [___] positions
  • Featured snippets: [___] captured
  • CTR delta: [___]%

On Track for 14d Goals? [Yes / Needs attention]

Next Checkpoint: 14d ({(deployment_date + timedelta(days=14)).strftime('%Y-%m-%d')})

To record observations:
  python monitor_performance.py --record-observation indexation_coverage_pct 95 --date {checkpoint_date.strftime('%Y-%m-%d')}
  python monitor_performance.py --record-observation avg_ranking_change -3 --date {checkpoint_date.strftime('%Y-%m-%d')}
  python monitor_performance.py --record-observation featured_snippets_count 52 --date {checkpoint_date.strftime('%Y-%m-%d')}

================================================================================
"""
        return checklist

    def generate_checklist_14d(self) -> str:
        """生成 14d 監控清單"""
        deployment_date = datetime(2026, 4, 11)
        checkpoint_date = deployment_date + timedelta(days=14)

        checklist = f"""
================================================================================
MONITORING CHECKLIST: 14d Checkpoint
================================================================================

Target Date: {checkpoint_date.strftime('%Y-%m-%d')}
Purpose: Primary measurement window for business impact

TRAFFIC IMPACT MEASUREMENT
─────────────────────────────────────────────────────────────────────────────
[ ] Google Analytics: Total Traffic Delta
    • Date range: 2026-04-11 to 2026-04-25 (14 days post-deployment)
    • Metric: Sessions / Users from organic search
    • Baseline (pre-deployment 14d avg): [___] sessions
    • Actual (2026-04-11 to 2026-04-25): [___] sessions
    • Delta: [___]% (target: +5-10%)
    • Confidence: [Low / Medium / High]

[ ] By-Post Traffic Analysis
    • Batch 1 (posts 1-50) avg traffic change: [___]%
    • Batch 2 (posts 51-100) avg traffic change: [___]%
    • Day 12 (posts 101-2800) avg traffic change: [___]%
    • Variance: [___] (are some posts performing better?)

CTR MEASUREMENT (Primary)
─────────────────────────────────────────────────────────────────────────────
[ ] GSC Performance: CTR Delta
    • Date range: 2026-04-11 to 2026-04-25
    • Baseline CTR (7d pre-deployment): [___]%
    • Current CTR (2026-04-11 to 2026-04-25): [___]%
    • Delta: [___]% (target: +8-15%)
    • Status: [Meeting target / Below target / Exceeding target]

RANKING POSITIONS (14d Update)
─────────────────────────────────────────────────────────────────────────────
[ ] Top 100 Keyword Positions
    • Baseline (pre-deployment): [snapshot file]
    • Current (14d): [snapshot file]
    • Avg improvement: [___] positions (target: -2 to -5, i.e., moving up)
    • Keywords with +1 position: [___]
    • Keywords with -1 position: [___]
    • Stability: [Stable / Volatile]

ENGAGEMENT METRICS
─────────────────────────────────────────────────────────────────────────────
[ ] Bounce Rate Change
    • Baseline avg bounce rate (pre-deploy): [__]%
    • Current bounce rate (2026-04-11 to 2026-04-25): [__]%
    • Delta: [___]% (target: -3 to -5%, i.e., less bouncing)
    • Interpretation: [Improved / Neutral / Degraded]

[ ] Avg Session Duration
    • Baseline (pre-deploy): [___] minutes
    • Current (14d): [___] minutes
    • Delta: [___]% (target: +5-10%)

[ ] Pages per Session
    • Baseline: [_._]
    • Current: [_._]
    • Delta: [___]%

CONVERSION TRACKING (If applicable)
─────────────────────────────────────────────────────────────────────────────
[ ] Goal Conversions (if e-commerce or form submissions tracked)
    • Baseline conversion rate: [___]%
    • Current conversion rate: [___]%
    • Delta: [___]%

CONTENT PERFORMANCE WINNERS/LOSERS
─────────────────────────────────────────────────────────────────────────────
[ ] Top 20 Posts (by traffic gain)
    List posts with >15% traffic improvement:
    1. Post [ID]: [___]% gain
    2. Post [ID]: [___]% gain
    ... (top 20)

[ ] Underperforming Posts
    List posts with <0% traffic change (need attention):
    1. Post [ID]: [___]% loss
    2. Post [ID]: [___]% loss
    ... (if any)

TECHNICAL HEALTH (14d Check)
─────────────────────────────────────────────────────────────────────────────
[ ] GSC Errors (should still be 0)
    • 404 errors: [___]
    • Crawl errors: [___]
    • Mobile usability issues: [___]

[ ] Core Web Vitals (Stability check)
    • LCP: [Good / Needs improvement]
    • FID: [Good / Needs improvement]
    • CLS: [Good / Needs improvement]
    • Overall: [Passed / Failed]

================================================================================
SUMMARY & BUSINESS DECISION
================================================================================

14d Overall Status: [GREEN / YELLOW / RED]

Primary Metrics vs Targets:
  ✓ CTR: [___]% delta (target: +8-15%) → [Met / Not met]
  ✓ Traffic: [___]% delta (target: +5-10%) → [Met / Not met]
  ✓ Avg ranking: [___] positions (target: -2 to -5) → [Met / Not met]
  ✓ Bounce rate: [___]% delta (target: -3-5%) → [Met / Not met]

Business Impact: [Positive / Neutral / Negative]

Recommendation: [Continue monitoring / Adjust optimization / Halt/Rollback]

Phase 3 Readiness: [Yes, proceed / Wait for 30d data / Not ready]

Next Checkpoint: 30d ({(deployment_date + timedelta(days=30)).strftime('%Y-%m-%d')})

To record observations:
  python monitor_performance.py --record-observation traffic_delta_pct 7.5 --date {checkpoint_date.strftime('%Y-%m-%d')}
  python monitor_performance.py --record-observation ctr_delta_pct 10.2 --date {checkpoint_date.strftime('%Y-%m-%d')}
  python monitor_performance.py --record-observation avg_ranking_improvement 3 --date {checkpoint_date.strftime('%Y-%m-%d')}

================================================================================
"""
        return checklist

    def generate_checklist_30d(self) -> str:
        """生成 30d 監控清單"""
        deployment_date = datetime(2026, 4, 11)
        checkpoint_date = deployment_date + timedelta(days=30)

        checklist = f"""
================================================================================
MONITORING CHECKLIST: 30d Checkpoint (Full Assessment)
================================================================================

Target Date: {checkpoint_date.strftime('%Y-%m-%d')}
Purpose: Complete business impact assessment and Phase 3 readiness decision

FULL-MONTH BUSINESS METRICS
─────────────────────────────────────────────────────────────────────────────
[ ] Organic Traffic (30-day aggregate)
    • Baseline (30d pre-deploy): [___] sessions
    • Actual (2026-04-11 to 2026-05-11): [___] sessions
    • Delta: [___]% (target: +15-25% cumulative over 30d)
    • Annualized impact: [___]% yearly

[ ] Long-tail Keyword Wins
    • New keywords ranking on SERP: [___] (target: >100)
    • Position 1-3: [___]
    • Position 4-10: [___]
    • Position 11-20: [___]

[ ] Top Post Performance
    • Posts with >20% traffic gain: [___] / 2,800 (target: >50%)
    • Avg traffic gain (winners): [___]%
    • Avg traffic change (all posts): [___]%

REVENUE/CONVERSION IMPACT
─────────────────────────────────────────────────────────────────────────────
[ ] Conversion Rate Trend
    • 7d avg conversion rate: [___]%
    • 14d avg conversion rate: [___]%
    • 30d avg conversion rate: [___]%
    • Trend: [Improving / Stable / Declining]

[ ] Revenue Impact (if applicable)
    • Baseline monthly revenue (est. from traffic): $[___]
    • Projected revenue (from current trajectory): $[___]
    • Estimated monthly impact: $[___] (+[___]%)

DOMAIN AUTHORITY SIGNALS
─────────────────────────────────────────────────────────────────────────────
[ ] Backlink Profile
    • New backlinks acquired (optional tracking): [___]
    • Any negative SEO signals: [None / Yes (describe)]

[ ] Brand Search Volume
    • Branded keyword impressions: [___] (check GSC)
    • Branded CTR: [___]%
    • Trend vs baseline: [Increasing / Stable / Decreasing]

CONTENT PERFORMANCE DISTRIBUTION
─────────────────────────────────────────────────────────────────────────────
[ ] Winners Distribution (by tier)
    • Tier 1 (>20 views baseline) with +10% gain: [___]%
    • Tier 2 (5-20 views baseline) with +10% gain: [___]%
    • Tier 3 (<5 views baseline) with +10% gain: [___]%

[ ] Avg Performance by Tier
    • Tier 1 avg change: [___]%
    • Tier 2 avg change: [___]%
    • Tier 3 avg change: [___]%

TECHNICAL HEALTH (Final 30d Check)
─────────────────────────────────────────────────────────────────────────────
[ ] GSC Health Status
    • Coverage: [___]% indexed
    • Errors: [___] (target: 0)
    • Status: [Excellent / Good / Needs attention]

[ ] Core Web Vitals (Full 30 days)
    • LCP: [___]ms
    • FID: [___]ms
    • CLS: [___]
    • Overall: [Pass / Fail]

COMPETITIVE POSITION
─────────────────────────────────────────────────────────────────────────────
[ ] Relative Ranking Gains
    • # of posts that outrank top 3 competitors: [___]
    • Featured snippet wins vs competitors: [___]
    • Overall competitive position: [Improved / Stable / Lost ground]

================================================================================
PHASE 3 DECISION MATRIX
================================================================================

Phase 3 Launch Criteria (all must be met for GO):

[_] Traffic improvement: >5% (ACTUAL: [___]%)
[_] CTR improvement: >8% (ACTUAL: [___]%)
[_] No critical errors (ACTUAL: [___] errors)
[_] User engagement: Bounce rate -3% to -5% (ACTUAL: [___]%)
[_] >50% of posts profitable (ACTUAL: [___]%)

PHASE 3 SCOPE DECISION:
─────────────────────────────────────────────────────────────────────────────

Based on 30d performance, recommend Phase 3 targeting:
  • Tier 3 posts (<5 views): [YES / NO]
  • Failed Phase 2 posts: [___] posts (if any)
  • Underperforming Tier 2: [YES / NO]
  • Estimated Phase 3 scope: [___] posts
  • Estimated Phase 3 cost: $[___]

Timeline: [Start immediately / Wait until date / Not recommended]

================================================================================
FINAL SUMMARY & RECOMMENDATIONS
================================================================================

30d Overall Assessment: [MAJOR SUCCESS / SUCCESS / MIXED / FAILURE]

Key Wins:
  • [___]

Areas for improvement:
  • [___]

Operational Changes (if any):
  • [___]

Next Phase:
  □ Proceed with Phase 3 (Tier 3 optimization)
  □ Continue monitoring Phase 2
  □ Investigate underperformers
  □ Plan Phase 4 (A/B testing)

Final Status: [Ready for Phase 3 / Keep current / Pause for review]

================================================================================
"""
        return checklist

    def record_observation(self, metric: str, value: float, date: str, notes: Optional[str] = None):
        """記錄單一觀測"""
        observation = {
            "timestamp": datetime.now().isoformat(),
            "metric": metric,
            "value": value,
            "date": date,
            "notes": notes or "",
        }

        obs_file = self.project_root / "monitoring_observations.jsonl"
        with open(obs_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(observation, ensure_ascii=False) + "\n")

        logger.info(f"✓ Observation recorded: {metric} = {value} on {date}")

    def run(self, checkpoint: str = "24h"):
        """執行監控"""
        try:
            logger.info("=" * 80)
            logger.info(f"PERFORMANCE MONITORING: {checkpoint.upper()} Checkpoint")
            logger.info("=" * 80)

            # Load baseline
            self.load_baseline()
            self.load_deployment_summary()
            self.load_observations()

            # Generate appropriate checklist
            if checkpoint == "24h":
                checklist = self.generate_checklist_24h()
            elif checkpoint == "7d":
                checklist = self.generate_checklist_7d()
            elif checkpoint == "14d":
                checklist = self.generate_checklist_14d()
            elif checkpoint == "30d":
                checklist = self.generate_checklist_30d()
            else:
                logger.error(f"Unknown checkpoint: {checkpoint}")
                return 1

            # Save checklist
            checklist_path = self.project_root / f"monitoring_checklist_{checkpoint}.txt"
            with open(checklist_path, "w", encoding="utf-8") as f:
                f.write(checklist)

            # Print to console
            print(checklist)
            logger.info(f"Checklist saved to {checklist_path}")

            return 0

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Performance Monitoring Framework")
    parser.add_argument("--checkpoint", default="24h", choices=["24h", "7d", "14d", "30d"],
                       help="Monitoring checkpoint (default: 24h)")
    parser.add_argument("--record-observation", metavar="METRIC",
                       help="Record an observation (use with --value, --date)")
    parser.add_argument("--value", type=float, help="Observation value")
    parser.add_argument("--date", help="Observation date (YYYY-MM-DD)")
    parser.add_argument("--notes", help="Optional notes")

    args = parser.parse_args()

    monitor = PerformanceMonitor()

    if args.record_observation:
        if not args.value or not args.date:
            logger.error("--record-observation requires --value and --date")
            exit(1)
        monitor.record_observation(args.record_observation, args.value, args.date, args.notes)
        exit(0)
    else:
        exit_code = monitor.run(checkpoint=args.checkpoint)
        exit(exit_code)
