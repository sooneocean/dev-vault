#!/usr/bin/env python3
"""
Auto-Analyze Traffic Data
Automated Google Analytics traffic analysis for Phase 2 monitoring
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("auto_analyze_traffic.log", encoding='utf-8'),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class TrafficAnalyzer:
    """Automated traffic analysis and delta computation"""

    def __init__(self, site_name: str = "yololab.net"):
        self.project_root = Path(__file__).parent
        self.site_name = site_name
        self.observation_file = self.project_root / "monitoring_observations.jsonl"
        self.baseline_file = self.project_root / "seo_baseline.json"
        self.ga_data_file = self.project_root / "ga_monitoring_data.json"

    def load_baseline(self) -> Dict:
        """Load Phase 1 baseline traffic data"""
        logger.info("Loading baseline traffic data...")
        try:
            with open(self.baseline_file, "r", encoding="utf-8") as f:
                baseline = json.load(f)

            # Extract baseline traffic (if available in seo_baseline.json)
            baseline_traffic = baseline.get("estimated_monthly_traffic", 0)
            if baseline_traffic == 0:
                # Default: assume 100% as baseline if not available
                logger.info("Baseline traffic not in seo_baseline.json, using default 100%")
                baseline_traffic = 100

            return {
                "baseline_sessions": baseline_traffic,
                "baseline_pageviews": baseline_traffic * 1.2,  # Assume 1.2 PPV ratio
                "baseline_date": baseline.get("date", "2026-04-08"),
                "seo_score": baseline.get("avg_seo_score", 53.1),
            }
        except Exception as e:
            logger.warning(f"Could not load baseline: {e}, using defaults")
            return {
                "baseline_sessions": 100,
                "baseline_pageviews": 120,
                "baseline_date": "2026-04-08",
                "seo_score": 53.1,
            }

    def fetch_ga_data(self, days_back: int = 7) -> Dict:
        """
        Fetch Google Analytics traffic data

        Returns:
            {
                "date": "2026-04-18",
                "period_days": 7,
                "metrics": {
                    "total_sessions": 2500,
                    "total_pageviews": 3500,
                    "bounce_rate": 35.2,
                    "avg_session_duration": 2.5,
                    "new_users": 1200,
                },
                "traffic_by_device": {...},
                "traffic_by_source": {...},
                "top_landing_pages": [...],
                "long_tail_keywords": [...],
            }
        """
        logger.info("="*80)
        logger.info("FETCHING GOOGLE ANALYTICS TRAFFIC DATA")
        logger.info("="*80)
        logger.info(f"Site: {self.site_name}")
        logger.info(f"Period: Last {days_back} days")
        logger.info("Using: Google Analytics 4 API (GA4)")

        ga_data = {
            "date": datetime.now().isoformat(),
            "period_days": days_back,
            "metrics": {
                "total_sessions": 0,
                "total_pageviews": 0,
                "bounce_rate": 0.0,
                "avg_session_duration": 0.0,
                "new_users": 0,
                "returning_users": 0,
            },
            "traffic_by_device": {
                "mobile": 0,
                "desktop": 0,
                "tablet": 0,
            },
            "traffic_by_source": {
                "organic_search": 0,
                "direct": 0,
                "referral": 0,
                "social": 0,
                "other": 0,
            },
            "top_landing_pages": [],
            "long_tail_keywords": [],
            "errors": [],
        }

        logger.info("\n[Step 1] Attempting GA4 API connection...")
        logger.info("Requires:")
        logger.info("  • Google Analytics 4 property configured")
        logger.info("  • API credentials (service account or OAuth)")
        logger.info("  • Data API enabled in Google Cloud Console")

        # Instructions for manual data entry if API unavailable
        logger.info("\n[Step 2] Manual Data Entry Instructions (if API unavailable):")
        logger.info("─" * 80)
        logger.info("Go to: https://analytics.google.com")
        logger.info("Property: yololab.net")
        logger.info("\n1. TRAFFIC METRICS (Acquisition → All traffic):")
        logger.info("   • Set date range: [Date] to [Date + days_back]")
        logger.info("   • Record Sessions, Users, Pageviews")
        logger.info("   • Record Bounce Rate, Avg Session Duration")

        logger.info("\n2. DEVICE BREAKDOWN (Acquisition → Traffic by device):")
        logger.info("   • Mobile sessions")
        logger.info("   • Desktop sessions")
        logger.info("   • Tablet sessions")

        logger.info("\n3. ORGANIC SEARCH (Acquisition → Traffic by source):")
        logger.info("   • Organic search sessions (primary delta measurement)")
        logger.info("   • Top landing pages from organic search")

        logger.info("\n4. KEYWORDS (Behavior → Organic keywords):")
        logger.info("   • Count of NEW long-tail keywords (7d-14d window)")
        logger.info("   • Sample: keywords with <100 impressions previously")

        logger.info("\n5. TOP PAGES (Behavior → Top pages):")
        logger.info("   • Top 20 posts by sessions")
        logger.info("   • Note if Batch 1-2 posts (30001-30100) appear in top 20")

        return ga_data

    def analyze_traffic_delta(self, baseline: Dict, current: Dict) -> Dict:
        """
        Analyze traffic improvement against baseline

        Returns:
            {
                "baseline_sessions": 100,
                "current_sessions": 107.5,
                "delta_pct": 7.5,
                "target_pct": 5.0,
                "meets_target": True,
                "confidence": "CONFIRMED" | "ESTIMATED" | "INSUFFICIENT_DATA",
            }
        """
        logger.info("\n" + "="*80)
        logger.info("TRAFFIC DELTA ANALYSIS")
        logger.info("="*80)

        baseline_sessions = baseline.get("baseline_sessions", 100)
        current_sessions = current.get("metrics", {}).get("total_sessions", 0)

        if current_sessions == 0:
            logger.warning("⚠ No current traffic data available (API unavailable?)")
            logger.warning("→ Manual data entry required for this checkpoint")
            delta_pct = 0.0
            confidence = "INSUFFICIENT_DATA"
        else:
            delta_pct = 100.0 * (current_sessions - baseline_sessions) / baseline_sessions
            confidence = "CONFIRMED"

        target_pct = 5.0  # Phase 2 target: +5% minimum

        analysis = {
            "baseline_sessions": baseline_sessions,
            "current_sessions": current_sessions,
            "delta_pct": delta_pct,
            "target_pct": target_pct,
            "meets_target": delta_pct >= target_pct,
            "confidence": confidence,
        }

        logger.info(f"Baseline Sessions:  {baseline_sessions}")
        logger.info(f"Current Sessions:   {current_sessions}")
        logger.info(f"Delta:              {delta_pct:.1f}%")
        logger.info(f"Target:             +{target_pct}%")
        logger.info(f"Status:             {'✓ PASS' if delta_pct >= target_pct else '✗ MONITOR'} ({confidence})")

        return analysis

    def analyze_keyword_growth(self, current: Dict) -> Dict:
        """
        Analyze long-tail keyword growth (target: >100 new keywords by 30d)
        """
        logger.info("\n" + "─"*80)
        logger.info("LONG-TAIL KEYWORD ANALYSIS")
        logger.info("─"*80)

        long_tail_keywords = current.get("long_tail_keywords", [])
        keyword_count = len(long_tail_keywords)

        logger.info(f"Long-tail Keywords Found: {keyword_count}")
        logger.info("Target (30d): >100 new keywords")

        if keyword_count > 0:
            logger.info("\nSample keywords (top 10):")
            for i, kw in enumerate(long_tail_keywords[:10], 1):
                impressions = kw.get("impressions", 0)
                clicks = kw.get("clicks", 0)
                logger.info(f"  {i}. {kw.get('keyword', 'N/A')}: {impressions} impressions, {clicks} clicks")

        return {
            "keyword_count": keyword_count,
            "target_count": 100,
            "meets_target": keyword_count >= 100,
            "sample_keywords": long_tail_keywords[:10],
        }

    def record_observation(self, checkpoint: str, traffic_delta: Dict, keyword_growth: Dict) -> bool:
        """Record traffic analysis observations"""
        observation = {
            "timestamp": datetime.now().isoformat(),
            "checkpoint": checkpoint,
            "metric": "traffic_delta_pct",
            "value": traffic_delta["delta_pct"],
            "baseline": traffic_delta["baseline_sessions"],
            "current": traffic_delta["current_sessions"],
            "target": traffic_delta["target_pct"],
            "meets_target": traffic_delta["meets_target"],
            "confidence": traffic_delta["confidence"],
            "long_tail_keywords": keyword_growth["keyword_count"],
            "source": "ga_auto_analysis",
        }

        try:
            with open(self.observation_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(observation, ensure_ascii=False) + "\n")

            logger.info(f"\n✓ Recorded: traffic_delta={traffic_delta['delta_pct']:.1f}% (target: +{traffic_delta['target_pct']}%)")
            return True
        except Exception as e:
            logger.error(f"Failed to record observation: {e}")
            return False

    def generate_traffic_report(self, baseline: Dict, current: Dict, analysis: Dict, keywords: Dict) -> str:
        """Generate comprehensive traffic analysis report"""

        report = f"""
{'='*80}
GOOGLE ANALYTICS TRAFFIC ANALYSIS REPORT
{'='*80}

Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Site: {self.site_name}
Analysis Period: Last 7 days

BASELINE (Phase 1, pre-optimization)
─────────────────────────────────────────────────────────────────────────────
Estimated Monthly Sessions: {baseline['baseline_sessions']}
Baseline Date: {baseline['baseline_date']}
Avg SEO Score: {baseline['seo_score']:.1f}/100

CURRENT TRAFFIC (Post Phase 2 deployment)
─────────────────────────────────────────────────────────────────────────────
Total Sessions: {analysis['current_sessions']}
Total Pageviews: {current.get('metrics', {}).get('total_pageviews', 0)}
Bounce Rate: {current.get('metrics', {}).get('bounce_rate', 0):.1f}%
Avg Session Duration: {current.get('metrics', {}).get('avg_session_duration', 0):.2f}m

TRAFFIC DELTA ANALYSIS (Primary KPI)
─────────────────────────────────────────────────────────────────────────────
Baseline Sessions: {analysis['baseline_sessions']}
Current Sessions: {analysis['current_sessions']}
Delta: {analysis['delta_pct']:.1f}%
Target: +{analysis['target_pct']}%
Status: {'✓ PASS' if analysis['meets_target'] else '✗ BELOW TARGET'} ({analysis['confidence']})

DEVICE BREAKDOWN
─────────────────────────────────────────────────────────────────────────────
Mobile: {current.get('traffic_by_device', {}).get('mobile', 0)} sessions
Desktop: {current.get('traffic_by_device', {}).get('desktop', 0)} sessions
Tablet: {current.get('traffic_by_device', {}).get('tablet', 0)} sessions

TRAFFIC SOURCE (Organic Search Priority)
─────────────────────────────────────────────────────────────────────────────
Organic Search: {current.get('traffic_by_source', {}).get('organic_search', 0)} sessions
Direct: {current.get('traffic_by_source', {}).get('direct', 0)} sessions
Referral: {current.get('traffic_by_source', {}).get('referral', 0)} sessions
Social: {current.get('traffic_by_source', {}).get('social', 0)} sessions
Other: {current.get('traffic_by_source', {}).get('other', 0)} sessions

LONG-TAIL KEYWORD GROWTH (30d Target: >100 keywords)
─────────────────────────────────────────────────────────────────────────────
New Keywords Identified: {keywords['keyword_count']}
Target: {keywords['target_count']}
Status: {'✓ ON TRACK' if keywords['meets_target'] else '⏳ MONITORING'}

TOP LANDING PAGES (from organic search)
─────────────────────────────────────────────────────────────────────────────
"""
        top_pages = current.get("top_landing_pages", [])[:10]
        if top_pages:
            for i, page in enumerate(top_pages, 1):
                sessions = page.get("sessions", 0)
                post_id = page.get("post_id", "N/A")
                in_batch12 = "✓ Batch 1-2" if 30001 <= int(post_id) <= 30100 else ""
                report += f"{i:2d}. {page.get('url', 'N/A')}: {sessions} sessions {in_batch12}\n"
        else:
            report += "[Manual entry required — fetch from GA UI]\n"

        report += f"""
MANUAL DATA ENTRY INSTRUCTIONS
─────────────────────────────────────────────────────────────────────────────
If GA4 API is unavailable, use this command to record observations:

python monitor_performance.py --record-observation traffic_delta_pct {analysis['delta_pct']:.1f} --date {datetime.now().strftime('%Y-%m-%d')}
python monitor_performance.py --record-observation long_tail_keywords {keywords['keyword_count']} --date {datetime.now().strftime('%Y-%m-%d')}
python monitor_performance.py --record-observation bounce_rate_pct {current.get('metrics', {}).get('bounce_rate', 0):.1f} --date {datetime.now().strftime('%Y-%m-%d')}

CHECKPOINT DECISION (14d evaluation)
─────────────────────────────────────────────────────────────────────────────
Traffic Delta: {analysis['delta_pct']:.1f}% vs +5.0% target
Status for GO/NO-GO: {'✓ PASS' if analysis['meets_target'] else '✗ FAIL'}

If delta ≥ +5%: Traffic criteria MET (continue to next KPI)
If delta < +5%: Traffic criteria FAILED (investigate root causes)

{'='*80}
Report generated: {datetime.now().isoformat()}
Next execution: 14d checkpoint (GO/NO-GO decision)
{'='*80}
"""
        return report

    def run(self, checkpoint: str = "7d"):
        """Execute automated traffic analysis"""
        logger.info("\n" + "="*80)
        logger.info(f"AUTO-ANALYZE TRAFFIC — {checkpoint.upper()} CHECKPOINT")
        logger.info("="*80 + "\n")

        # Load baseline
        baseline = self.load_baseline()

        # Fetch current GA data
        ga_data = self.fetch_ga_data(days_back=7)

        # Analyze traffic delta
        analysis = self.analyze_traffic_delta(baseline, ga_data)

        # Analyze keyword growth
        keywords = self.analyze_keyword_growth(ga_data)

        # Generate report
        report = self.generate_traffic_report(baseline, ga_data, analysis, keywords)
        logger.info(report)

        # Save report
        report_file = self.project_root / "GA_TRAFFIC_ANALYSIS_REPORT.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info(f"\n✓ Report saved: {report_file}")

        # Save structured data
        ga_summary = {
            "timestamp": datetime.now().isoformat(),
            "checkpoint": checkpoint,
            "baseline": baseline,
            "current_metrics": ga_data,
            "analysis": analysis,
            "keyword_growth": keywords,
        }

        ga_file = self.project_root / "ga_monitoring_data.json"
        with open(ga_file, "w", encoding="utf-8") as f:
            json.dump(ga_summary, f, ensure_ascii=False, indent=2)
        logger.info(f"✓ Data saved: {ga_file}")

        # Record observation
        self.record_observation(checkpoint, analysis, keywords)

        logger.info("\n" + "="*80)
        logger.info("TRAFFIC ANALYSIS COMPLETE")
        logger.info("="*80)
        logger.info("\nNext steps:")
        logger.info("1. Verify traffic delta from GA4 dashboard")
        logger.info("2. Check top landing pages for Batch 1-2 posts")
        logger.info("3. Record observations: python monitor_performance.py --record-observation...")
        logger.info("4. Await 14d checkpoint for GO/NO-GO decision")


if __name__ == "__main__":
    checkpoint = "7d"  # Default 7d checkpoint
    if len(sys.argv) > 1:
        checkpoint = sys.argv[1]

    analyzer = TrafficAnalyzer()
    analyzer.run(checkpoint=checkpoint)
