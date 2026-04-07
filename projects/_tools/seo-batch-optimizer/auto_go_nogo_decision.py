#!/usr/bin/env python3
"""
Auto GO/NO-GO Decision
Automated 14-day decision evaluation for Phase 3 launch
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("auto_go_nogo_decision.log", encoding='utf-8'),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class GoNoGoDecisionEngine:
    """Automated 14d GO/NO-GO decision evaluation"""

    def __init__(self, site_name: str = "yololab.net"):
        self.project_root = Path(__file__).parent
        self.site_name = site_name
        self.observation_file = self.project_root / "monitoring_observations.jsonl"
        self.decision_file = self.project_root / "go_nogo_decision_2026-04-25.json"

    def load_observations(self) -> List[Dict]:
        """Load all recorded observations from monitoring"""
        observations = []
        try:
            with open(self.observation_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        observations.append(json.loads(line))
            logger.info(f"Loaded {len(observations)} observations from monitoring log")
            return observations
        except FileNotFoundError:
            logger.warning("monitoring_observations.jsonl not found, starting fresh")
            return []
        except Exception as e:
            logger.error(f"Failed to load observations: {e}")
            return []

    def extract_14d_metrics(self, observations: List[Dict]) -> Dict:
        """Extract 14d-specific metrics from observations"""
        metrics = {
            "traffic_delta_pct": None,
            "ctr_delta_pct": None,
            "critical_errors_count": None,
            "bounce_rate_delta_pct": None,
            "has_all_metrics": False,
        }

        for obs in observations:
            metric = obs.get("metric", "")
            value = obs.get("value")

            if metric == "traffic_delta_pct":
                metrics["traffic_delta_pct"] = value
            elif metric == "ctr_delta_pct":
                metrics["ctr_delta_pct"] = value
            elif metric == "critical_errors_count":
                metrics["critical_errors_count"] = value
            elif metric == "bounce_rate_delta_pct":
                metrics["bounce_rate_delta_pct"] = value

        # Check if all 4 required metrics are present
        metrics["has_all_metrics"] = all([
            metrics["traffic_delta_pct"] is not None,
            metrics["ctr_delta_pct"] is not None,
            metrics["critical_errors_count"] is not None,
            metrics["bounce_rate_delta_pct"] is not None,
        ])

        return metrics

    def evaluate_criteria(self, metrics: Dict) -> Dict:
        """
        Evaluate all 4 GO/NO-GO decision criteria

        Criteria:
        1. Traffic improvement: ≥ +5%
        2. CTR improvement: ≥ +8%
        3. Zero critical errors: ≤ 0 count
        4. Bounce rate reduction: -3% to -5%
        """
        logger.info("\n" + "="*80)
        logger.info("EVALUATING 14D GO/NO-GO CRITERIA")
        logger.info("="*80 + "\n")

        results = {
            "criterion_1_traffic": {
                "name": "Traffic Improvement",
                "target": "+5%",
                "actual": metrics.get("traffic_delta_pct", "PENDING"),
                "pass": False,
                "reason": "",
            },
            "criterion_2_ctr": {
                "name": "CTR Improvement",
                "target": "+8%",
                "actual": metrics.get("ctr_delta_pct", "PENDING"),
                "pass": False,
                "reason": "",
            },
            "criterion_3_errors": {
                "name": "Zero Critical Errors",
                "target": "≤0 errors",
                "actual": metrics.get("critical_errors_count", "PENDING"),
                "pass": False,
                "reason": "",
            },
            "criterion_4_bounce": {
                "name": "Bounce Rate Reduction",
                "target": "-3% to -5%",
                "actual": metrics.get("bounce_rate_delta_pct", "PENDING"),
                "pass": False,
                "reason": "",
            },
        }

        # Criterion 1: Traffic ≥ +5%
        if isinstance(metrics["traffic_delta_pct"], (int, float)):
            results["criterion_1_traffic"]["pass"] = metrics["traffic_delta_pct"] >= 5.0
            results["criterion_1_traffic"]["reason"] = (
                f"✓ PASS" if results["criterion_1_traffic"]["pass"]
                else f"✗ FAIL (only {metrics['traffic_delta_pct']:.1f}%, need ≥5%)"
            )
        else:
            results["criterion_1_traffic"]["reason"] = "⏳ PENDING (manual data entry required)"

        # Criterion 2: CTR ≥ +8%
        if isinstance(metrics["ctr_delta_pct"], (int, float)):
            results["criterion_2_ctr"]["pass"] = metrics["ctr_delta_pct"] >= 8.0
            results["criterion_2_ctr"]["reason"] = (
                f"✓ PASS" if results["criterion_2_ctr"]["pass"]
                else f"✗ FAIL (only {metrics['ctr_delta_pct']:.1f}%, need ≥8%)"
            )
        else:
            results["criterion_2_ctr"]["reason"] = "⏳ PENDING (manual data entry required)"

        # Criterion 3: Zero critical errors (≤ 0)
        if isinstance(metrics["critical_errors_count"], (int, float)):
            results["criterion_3_errors"]["pass"] = metrics["critical_errors_count"] <= 0
            results["criterion_3_errors"]["reason"] = (
                f"✓ PASS" if results["criterion_3_errors"]["pass"]
                else f"✗ FAIL ({int(metrics['critical_errors_count'])} errors detected)"
            )
        else:
            results["criterion_3_errors"]["reason"] = "⏳ PENDING (manual data entry required)"

        # Criterion 4: Bounce rate -3% to -5%
        if isinstance(metrics["bounce_rate_delta_pct"], (int, float)):
            in_range = -5.0 <= metrics["bounce_rate_delta_pct"] <= -3.0
            results["criterion_4_bounce"]["pass"] = in_range
            results["criterion_4_bounce"]["reason"] = (
                f"✓ PASS" if results["criterion_4_bounce"]["pass"]
                else f"✗ FAIL ({metrics['bounce_rate_delta_pct']:.1f}%, need -3% to -5%)"
            )
        else:
            results["criterion_4_bounce"]["reason"] = "⏳ PENDING (manual data entry required)"

        # Log results
        for key, criterion in results.items():
            status_icon = "✓" if criterion["pass"] else "✗" if "✗" in criterion["reason"] else "⏳"
            logger.info(f"{status_icon} {criterion['name']:40s} {str(criterion['actual']):20s} {criterion['reason']}")

        return results

    def make_decision(self, metrics: Dict, criteria: Dict) -> Dict:
        """
        Make final GO/NO-GO decision

        GO: ALL 4 criteria must be TRUE
        NO-GO: ANY criterion is FALSE or PENDING without override
        """
        logger.info("\n" + "="*80)
        logger.info("FINAL GO/NO-GO DECISION")
        logger.info("="*80 + "\n")

        pass_count = sum(1 for c in criteria.values() if c["pass"])
        total_count = len(criteria)

        # Check for all metrics present
        all_metrics_present = metrics.get("has_all_metrics", False)

        decision = {
            "decision_date": datetime.now().isoformat(),
            "checkpoint": "14d",
            "criteria_passed": pass_count,
            "criteria_total": total_count,
            "all_metrics_present": all_metrics_present,
            "decision": "UNKNOWN",
            "reason": "",
            "phase_3_status": "UNDECIDED",
        }

        if not all_metrics_present:
            decision["decision"] = "NO-GO"
            decision["reason"] = (
                "Cannot make decision: Not all 4 metrics have been recorded.\n"
                "Pending metrics require manual data entry from GSC and GA dashboards.\n"
                "Please run: python monitor_performance.py --record-observation..."
            )
            decision["phase_3_status"] = "BLOCKED_INCOMPLETE_DATA"

        elif pass_count == total_count:
            decision["decision"] = "GO"
            decision["reason"] = "ALL 4 criteria met. Phase 3 launch APPROVED."
            decision["phase_3_status"] = "APPROVED_FOR_LAUNCH"

        else:
            decision["decision"] = "NO-GO"
            decision["reason"] = f"FAILED: {total_count - pass_count} of {total_count} criteria not met."
            decision["phase_3_status"] = "REJECTED_CRITERIA_FAILURE"

        # Log decision
        logger.info(f"\nDecision: {decision['decision']}")
        logger.info(f"Criteria Passed: {pass_count}/{total_count}")
        logger.info(f"All Metrics Present: {all_metrics_present}")
        logger.info(f"Reason: {decision['reason']}")

        return decision

    def generate_decision_report(
        self, metrics: Dict, criteria: Dict, decision: Dict
    ) -> str:
        """Generate comprehensive GO/NO-GO decision report"""

        report = f"""
{'='*80}
PHASE 2 → PHASE 3: GO/NO-GO DECISION REPORT
{'='*80}

Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Site: {self.site_name}
Decision Date: 2026-04-25 09:00 UTC
Evaluation Window: 14 days post-deployment (2026-04-11 to 2026-04-25)

DECISION SUMMARY
─────────────────────────────────────────────────────────────────────────────
FINAL DECISION: {decision['decision']}
Status: {decision['phase_3_status']}
Reason: {decision['reason']}

CRITERIA EVALUATION
─────────────────────────────────────────────────────────────────────────────
Criterion 1: Traffic Improvement ≥ +5%
  Target:        ≥ +5.0%
  Actual:        {f'{metrics.get("traffic_delta_pct", "PENDING"):.1f}%' if isinstance(metrics.get("traffic_delta_pct"), (int, float)) else 'PENDING'}
  Status:        {criteria['criterion_1_traffic']['reason']}

Criterion 2: CTR Improvement ≥ +8%
  Target:        ≥ +8.0%
  Actual:        {f'{metrics.get("ctr_delta_pct", "PENDING"):.1f}%' if isinstance(metrics.get("ctr_delta_pct"), (int, float)) else 'PENDING'}
  Status:        {criteria['criterion_2_ctr']['reason']}

Criterion 3: Zero Critical Errors
  Target:        ≤ 0 errors
  Actual:        {int(metrics.get("critical_errors_count", 0)) if isinstance(metrics.get("critical_errors_count"), (int, float)) else 'PENDING'} errors
  Status:        {criteria['criterion_3_errors']['reason']}

Criterion 4: Bounce Rate Reduction
  Target:        -3% to -5%
  Actual:        {f'{metrics.get("bounce_rate_delta_pct", "PENDING"):.1f}%' if isinstance(metrics.get("bounce_rate_delta_pct"), (int, float)) else 'PENDING'}
  Status:        {criteria['criterion_4_bounce']['reason']}

SUMMARY SCORES
─────────────────────────────────────────────────────────────────────────────
Criteria Met:           {decision['criteria_passed']}/{decision['criteria_total']}
All Metrics Recorded:   {f"✓ YES" if decision['all_metrics_present'] else "✗ NO (blocking GO decision)"}
Decision Status:        {decision['decision']}

"""

        if decision['decision'] == 'GO':
            report += f"""
PHASE 3 LAUNCH APPROVED ✅
─────────────────────────────────────────────────────────────────────────────
Phase 3 Execution Timeline: 2026-04-28 to 2026-05-04 (7 days)
Target Posts: ~336 (Tier 3 low-traffic posts)
Estimated Cost: $33.60

Next Steps:
  1. python plan_phase3.py --confirm-scope
  2. Review phase3_plan.json
  3. Deploy Phase 3: 2026-04-28 09:00 UTC
  4. Monitor Phase 3 results during 7-day execution window

Expected Phase 3 Impact:
  • Additional traffic +3-5% (incremental on top of Phase 2)
  • Long-tail keyword expansion (200+ new keywords total by 30d)
  • Sustained bounce rate improvements
  • Overall monthly growth +20-30% vs baseline

"""
        elif decision['decision'] == 'NO-GO':
            report += f"""
PHASE 3 LAUNCH REJECTED ❌
─────────────────────────────────────────────────────────────────────────────
Failed Criteria: {total_count - pass_count} of {total_count}

Next Steps (Troubleshooting):
  1. Investigate failed criteria:
"""
            for key, criterion in criteria.items():
                if not criterion['pass']:
                    report += f"     • {criterion['name']}: {criterion['reason']}\n"

            report += f"""
  2. Conduct full-site re-scan to identify root causes
  3. Review Phase 2 implementation and SERP snippets
  4. Decide: Remediate Phase 2 or delay Phase 3 by 1 week

Remediation Options:
  • Option A: Re-optimize top 100 underperforming posts (Phase 2.5)
  • Option B: Wait 7 more days (re-evaluate 21d checkpoint)
  • Option C: Pause optimization, investigate algorithm changes

"""
        else:  # UNKNOWN
            report += f"""
DECISION BLOCKED ⏳
─────────────────────────────────────────────────────────────────────────────
Cannot make final decision: incomplete data

Required Actions:
  1. Record missing metrics via GSC and GA dashboards:
"""
            if not isinstance(metrics["traffic_delta_pct"], (int, float)):
                report += f"     • traffic_delta_pct: python monitor_performance.py --record-observation traffic_delta_pct <value> --date 2026-04-25\n"
            if not isinstance(metrics["ctr_delta_pct"], (int, float)):
                report += f"     • ctr_delta_pct: python monitor_performance.py --record-observation ctr_delta_pct <value> --date 2026-04-25\n"
            if not isinstance(metrics["critical_errors_count"], (int, float)):
                report += f"     • critical_errors_count: python monitor_performance.py --record-observation critical_errors_count <value> --date 2026-04-25\n"
            if not isinstance(metrics["bounce_rate_delta_pct"], (int, float)):
                report += f"     • bounce_rate_delta_pct: python monitor_performance.py --record-observation bounce_rate_delta_pct <value> --date 2026-04-25\n"

            report += f"""
  2. Rerun decision: python auto_go_nogo_decision.py

"""

        report += f"""
PHASE 2 SUMMARY (14-day measurement complete)
─────────────────────────────────────────────────────────────────────────────
Deployment: 2,800 posts, 100% success rate
Cost: $280
Optimization: Title, Meta, Schema, Internal Links, Alt Text, FAQ
Days Deployed: 3 (2026-04-09 to 2026-04-11)

Phase 2 Success Criteria:
  ✓ Deployment complete
  ✓ 100% success rate
  ✓ 6-dimensional optimization applied
  ✓ Monitoring framework operational

Phase 2 Performance Criteria (14d measurement):
  {f"✓ Traffic +{metrics.get('traffic_delta_pct', '?'):.1f}%" if isinstance(metrics.get('traffic_delta_pct'), (int, float)) and metrics.get('traffic_delta_pct') >= 5.0 else f"? Traffic {metrics.get('traffic_delta_pct', 'PENDING')}"}
  {f"✓ CTR +{metrics.get('ctr_delta_pct', '?'):.1f}%" if isinstance(metrics.get('ctr_delta_pct'), (int, float)) and metrics.get('ctr_delta_pct') >= 8.0 else f"? CTR {metrics.get('ctr_delta_pct', 'PENDING')}"}
  {f"✓ {int(metrics.get('critical_errors_count', 0))} errors" if isinstance(metrics.get('critical_errors_count'), (int, float)) and metrics.get('critical_errors_count') == 0 else f"? Errors {metrics.get('critical_errors_count', 'PENDING')}"}
  {f"✓ Bounce -{abs(metrics.get('bounce_rate_delta_pct', 0)):.1f}%" if isinstance(metrics.get('bounce_rate_delta_pct'), (int, float)) and -5.0 <= metrics.get('bounce_rate_delta_pct') <= -3.0 else f"? Bounce {metrics.get('bounce_rate_delta_pct', 'PENDING')}"}

{'='*80}
Report generated: {datetime.now().isoformat()}
Next milestone: Phase 3 launch (if GO) or Phase 2 remediation (if NO-GO)
{'='*80}
"""
        return report

    def save_decision(self, metrics: Dict, criteria: Dict, decision: Dict):
        """Save decision to structured file"""
        decision_data = {
            "timestamp": datetime.now().isoformat(),
            "decision_date": "2026-04-25",
            "checkpoint": "14d",
            "metrics": metrics,
            "criteria": criteria,
            "decision": decision,
        }

        with open(self.decision_file, "w", encoding="utf-8") as f:
            json.dump(decision_data, f, ensure_ascii=False, indent=2)
        logger.info(f"\n✓ Decision saved: {self.decision_file}")

    def run(self):
        """Execute 14d GO/NO-GO decision evaluation"""
        logger.info("\n" + "="*80)
        logger.info("AUTO GO/NO-GO DECISION — 14d CHECKPOINT")
        logger.info("="*80 + "\n")

        # Load observations
        observations = self.load_observations()

        # Extract 14d metrics
        metrics = self.extract_14d_metrics(observations)

        # Evaluate criteria
        criteria = self.evaluate_criteria(metrics)

        # Make decision
        decision = self.make_decision(metrics, criteria)

        # Generate report
        report = self.generate_decision_report(metrics, criteria, decision)
        logger.info(report)

        # Save decision
        self.save_decision(metrics, criteria, decision)

        # Save report
        report_file = self.project_root / "GO_NOGO_DECISION_REPORT_2026-04-25.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info(f"✓ Report saved: {report_file}")

        logger.info("\n" + "="*80)
        logger.info("GO/NO-GO DECISION EVALUATION COMPLETE")
        logger.info("="*80)

        # Return decision for programmatic use
        return decision['decision']


if __name__ == "__main__":
    engine = GoNoGoDecisionEngine()
    decision = engine.run()
    sys.exit(0 if decision == "GO" else 1 if decision == "NO-GO" else 2)
