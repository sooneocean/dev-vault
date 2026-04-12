"""
Metrics, monitoring, and observability subsystem.

Includes:
- Prometheus metrics collection
- Distributed tracing (OpenTelemetry with Jaeger/Zipkin)
- Alert rules and anomaly detection
- Structured JSON logging with PII redaction
"""

from src.metrics.prometheus import (
    PrometheusCollector,
    MetricsCollector,
    MetricSnapshot,
    metrics_collector,
)

from src.metrics.tracing import (
    TraceSpan,
    SimpleTracer,
    OTelTracer,
    DistributedTracer,
    distributed_tracer,
)

from src.metrics.alerts import (
    Alert,
    AlertRule,
    ThresholdAlert,
    BelowThresholdAlert,
    RateOfChangeAlert,
    AnomalyAlert,
    AlertManager,
    alert_manager,
)

from src.metrics.logging import (
    StructuredLogger,
    ComponentLogger,
    ComponentJsonFormatter,
    SecureLogFormatter,
    ELKIntegration,
    LokiIntegration,
    LogConfig,
    get_component_logger,
    set_component_log_level,
    component_logger,
    structured_logger,
    log_config,
)

__all__ = [
    # Prometheus
    "PrometheusCollector",
    "MetricsCollector",
    "MetricSnapshot",
    "metrics_collector",
    # Tracing
    "TraceSpan",
    "SimpleTracer",
    "OTelTracer",
    "DistributedTracer",
    "distributed_tracer",
    # Alerts
    "Alert",
    "AlertRule",
    "ThresholdAlert",
    "BelowThresholdAlert",
    "RateOfChangeAlert",
    "AnomalyAlert",
    "AlertManager",
    "alert_manager",
    # Logging
    "StructuredLogger",
    "ComponentLogger",
    "ComponentJsonFormatter",
    "SecureLogFormatter",
    "ELKIntegration",
    "LokiIntegration",
    "LogConfig",
    "get_component_logger",
    "set_component_log_level",
    "component_logger",
    "structured_logger",
    "log_config",
]
