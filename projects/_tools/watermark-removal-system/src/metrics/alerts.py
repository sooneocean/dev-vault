"""
Alert rules and conditions for monitoring.

Detects anomalies and triggers alerts.
"""

import logging
from typing import Callable, Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class Alert:
    """An alert trigger."""
    alert_id: str
    rule_name: str
    severity: str  # "info", "warning", "critical"
    message: str
    timestamp: datetime
    value: float
    threshold: float


class AlertRule:
    """Base class for alert rules."""

    def __init__(
        self,
        rule_name: str,
        severity: str = "warning",
        threshold: Optional[float] = None,
    ):
        self.rule_name = rule_name
        self.severity = severity
        self.threshold = threshold
        self.enabled = True
        self.triggered_at: Optional[datetime] = None
        self.triggered_count = 0

    def evaluate(self, value: float) -> Optional[Alert]:
        """Evaluate if alert should trigger."""
        if not self.enabled:
            return None

        if self.should_trigger(value):
            alert = self._create_alert(value)
            self.triggered_count += 1
            self.triggered_at = datetime.now(timezone.utc)
            return alert

        return None

    def should_trigger(self, value: float) -> bool:
        """Determine if alert should trigger."""
        raise NotImplementedError

    def _create_alert(self, value: float) -> Alert:
        """Create alert object."""
        import uuid

        return Alert(
            alert_id=str(uuid.uuid4()),
            rule_name=self.rule_name,
            severity=self.severity,
            message=f"{self.rule_name}: {value}",
            timestamp=datetime.now(timezone.utc),
            value=value,
            threshold=self.threshold or 0,
        )


class ThresholdAlert(AlertRule):
    """Alert when value exceeds threshold."""

    def should_trigger(self, value: float) -> bool:
        """Alert if value > threshold."""
        if self.threshold is None:
            return False

        return value > self.threshold


class BelowThresholdAlert(AlertRule):
    """Alert when value falls below threshold."""

    def should_trigger(self, value: float) -> bool:
        """Alert if value < threshold."""
        if self.threshold is None:
            return False

        return value < self.threshold


class RateOfChangeAlert(AlertRule):
    """Alert when rate of change is high."""

    def __init__(self, rule_name: str, window_size: int = 10, threshold: float = 50.0):
        super().__init__(rule_name, threshold=threshold)
        self.window_size = window_size
        self.values: List[float] = []

    def should_trigger(self, value: float) -> bool:
        """Alert if rate of change > threshold."""
        self.values.append(value)

        if len(self.values) < self.window_size:
            return False

        # Keep only recent values
        if len(self.values) > self.window_size:
            self.values = self.values[-self.window_size :]

        # Calculate rate of change
        if len(self.values) < 2:
            return False

        old_value = self.values[0]
        new_value = self.values[-1]

        if old_value == 0:
            return False

        rate_of_change = abs((new_value - old_value) / old_value) * 100

        return rate_of_change > (self.threshold or 50)


class AnomalyAlert(AlertRule):
    """Alert when value is anomalous."""

    def __init__(
        self,
        rule_name: str,
        window_size: int = 100,
        std_dev_threshold: float = 2.0,
    ):
        super().__init__(rule_name, threshold=std_dev_threshold)
        self.window_size = window_size
        self.std_dev_threshold = std_dev_threshold
        self.values: List[float] = []

    def should_trigger(self, value: float) -> bool:
        """Alert if value is anomalous (>N std dev from mean)."""
        self.values.append(value)

        if len(self.values) < self.window_size:
            return False

        # Keep only recent values
        if len(self.values) > self.window_size:
            self.values = self.values[-self.window_size :]

        # Calculate statistics
        import statistics

        mean = statistics.mean(self.values)
        stdev = statistics.stdev(self.values)

        if stdev == 0:
            return False

        # Check if current value is anomalous
        z_score = abs((value - mean) / stdev)

        return z_score > self.std_dev_threshold


class AlertManager:
    """Manage alert rules and trigger alerts."""

    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.alerts: List[Alert] = []

    def add_rule(self, rule_name: str, rule: AlertRule):
        """Add alert rule."""
        self.rules[rule_name] = rule
        logger.info(f"Added alert rule: {rule_name}")

    def evaluate_all(self, metrics: Dict[str, float]) -> List[Alert]:
        """Evaluate all rules against metrics."""
        triggered_alerts = []

        for metric_name, value in metrics.items():
            # Find rules for this metric
            for rule_name, rule in self.rules.items():
                if metric_name in rule_name:
                    alert = rule.evaluate(value)
                    if alert:
                        triggered_alerts.append(alert)
                        self._handle_alert(alert)

        return triggered_alerts

    def _handle_alert(self, alert: Alert):
        """Handle triggered alert."""
        self.alerts.append(alert)

        # Log at appropriate level
        level = {
            "info": logging.INFO,
            "warning": logging.WARNING,
            "critical": logging.CRITICAL,
        }.get(alert.severity, logging.WARNING)

        logger.log(level, f"[ALERT] {alert.rule_name}: {alert.message}")

        # Keep only recent alerts
        if len(self.alerts) > 10000:
            self.alerts = self.alerts[-5000 :]

    def get_active_alerts(self) -> List[Alert]:
        """Get currently active alerts."""
        # Return alerts from last hour
        import time

        one_hour_ago = datetime.now(timezone.utc).timestamp() - 3600
        return [a for a in self.alerts if a.timestamp.timestamp() > one_hour_ago]

    def get_rule_status(self) -> Dict[str, Dict[str, any]]:
        """Get status of all alert rules."""
        return {
            rule_name: {
                "enabled": rule.enabled,
                "severity": rule.severity,
                "threshold": rule.threshold,
                "triggered_count": rule.triggered_count,
                "triggered_at": rule.triggered_at.isoformat() if rule.triggered_at else None,
            }
            for rule_name, rule in self.rules.items()
        }

    def setup_default_rules(self):
        """Setup common alert rules."""
        # Latency alerts
        self.add_rule(
            "latency_high",
            ThresholdAlert("Processing Latency High", severity="warning", threshold=1000),
        )

        # GPU memory alert
        self.add_rule(
            "gpu_memory_high",
            ThresholdAlert("GPU Memory High", severity="critical", threshold=90),
        )

        # Queue depth alert
        self.add_rule(
            "queue_depth_anomaly",
            AnomalyAlert("Queue Depth Anomaly", window_size=50, std_dev_threshold=3.0),
        )

        # Error rate alert
        self.add_rule(
            "error_rate_high",
            ThresholdAlert("Error Rate High", severity="warning", threshold=0.05),
        )

        # Frame drop rate alert
        self.add_rule(
            "drop_rate_high",
            ThresholdAlert("Frame Drop Rate High", severity="critical", threshold=0.1),
        )

        logger.info("Default alert rules configured")


# Global alert manager
alert_manager = AlertManager()
alert_manager.setup_default_rules()
