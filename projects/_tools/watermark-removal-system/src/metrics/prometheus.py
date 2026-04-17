"""
Prometheus metrics collection for monitoring and observability.

Tracks pipeline performance, system resources, and business metrics.
"""

import logging
import time
from typing import Optional, Dict
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Try to import prometheus client
try:
    from prometheus_client import Counter, Gauge, Histogram, Summary, CollectorRegistry
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False
    logger.warning("prometheus-client not available, metrics disabled")


@dataclass
class MetricSnapshot:
    """Snapshot of current metrics."""
    timestamp: datetime
    frames_processed: int
    frames_dropped: int
    api_requests: int
    average_latency_ms: float
    gpu_utilization_pct: float
    memory_used_mb: float
    queue_depth: int
    error_count: int
    error_rate: float


class PrometheusCollector:
    """Collect Prometheus metrics."""

    def __init__(self, registry: Optional["CollectorRegistry"] = None):
        self.registry = registry or (CollectorRegistry() if HAS_PROMETHEUS else None)
        self.enabled = HAS_PROMETHEUS

        if self.enabled:
            self._init_metrics()
        else:
            logger.warning("Prometheus metrics disabled (library not available)")

    def _init_metrics(self):
        """Initialize Prometheus metrics."""
        # Pipeline metrics
        self.frames_processed = Counter(
            "watermark_frames_processed_total",
            "Total frames processed",
            registry=self.registry,
        )
        self.frames_dropped = Counter(
            "watermark_frames_dropped_total",
            "Total frames dropped",
            registry=self.registry,
        )

        # Latency metrics
        self.processing_latency = Histogram(
            "watermark_processing_latency_ms",
            "Frame processing latency",
            buckets=[10, 50, 100, 250, 500, 1000],
            registry=self.registry,
        )

        # System metrics
        self.gpu_utilization = Gauge(
            "watermark_gpu_utilization_percent",
            "GPU utilization percentage",
            registry=self.registry,
        )
        self.memory_usage = Gauge(
            "watermark_memory_usage_mb",
            "Memory usage in MB",
            registry=self.registry,
        )
        self.disk_io = Gauge(
            "watermark_disk_io_bytes_per_sec",
            "Disk I/O rate in bytes/sec",
            registry=self.registry,
        )

        # Queue metrics
        self.queue_depth = Gauge(
            "watermark_queue_depth",
            "Current frame queue depth",
            registry=self.registry,
        )

        # API metrics
        self.api_requests = Counter(
            "watermark_api_requests_total",
            "Total API requests",
            ["method", "endpoint"],
            registry=self.registry,
        )
        self.api_errors = Counter(
            "watermark_api_errors_total",
            "Total API errors",
            ["method", "endpoint", "status_code"],
            registry=self.registry,
        )

        # Business metrics
        self.sessions_created = Counter(
            "watermark_sessions_created_total",
            "Total streaming sessions created",
            registry=self.registry,
        )
        self.sessions_active = Gauge(
            "watermark_sessions_active",
            "Currently active sessions",
            registry=self.registry,
        )

        logger.info("Prometheus metrics initialized")

    def record_frame_processed(self, latency_ms: float):
        """Record processed frame."""
        if not self.enabled:
            return

        self.frames_processed.inc()
        self.processing_latency.observe(latency_ms)

    def record_frame_dropped(self):
        """Record dropped frame."""
        if not self.enabled:
            return

        self.frames_dropped.inc()

    def set_gpu_utilization(self, utilization_pct: float):
        """Set GPU utilization percentage."""
        if not self.enabled:
            return

        self.gpu_utilization.set(utilization_pct)

    def set_memory_usage(self, memory_mb: float):
        """Set memory usage."""
        if not self.enabled:
            return

        self.memory_usage.set(memory_mb)

    def set_disk_io(self, bytes_per_sec: float):
        """Set disk I/O rate."""
        if not self.enabled:
            return

        self.disk_io.set(bytes_per_sec)

    def set_queue_depth(self, depth: int):
        """Set queue depth."""
        if not self.enabled:
            return

        self.queue_depth.set(depth)

    def record_api_request(self, method: str, endpoint: str):
        """Record API request."""
        if not self.enabled:
            return

        self.api_requests.labels(method=method, endpoint=endpoint).inc()

    def record_api_error(self, method: str, endpoint: str, status_code: int):
        """Record API error."""
        if not self.enabled:
            return

        self.api_errors.labels(method=method, endpoint=endpoint, status_code=status_code).inc()

    def record_session_created(self):
        """Record session creation."""
        if not self.enabled:
            return

        self.sessions_created.inc()

    def set_active_sessions(self, count: int):
        """Set active session count."""
        if not self.enabled:
            return

        self.sessions_active.set(count)

    def get_registry(self):
        """Get Prometheus registry for exposition."""
        if not self.enabled:
            return None

        return self.registry

    def get_metrics(self) -> Optional[str]:
        """Get metrics as Prometheus exposition format."""
        if not self.enabled:
            return None

        try:
            from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

            return generate_latest(self.registry).decode("utf-8")
        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
            return None


class MetricsCollector:
    """High-level metrics collection."""

    def __init__(self):
        self.prometheus = PrometheusCollector()
        self.start_time = time.time()
        self.frame_count = 0
        self.drop_count = 0
        self.latencies = []
        self.gpu_samples = []
        self.memory_samples = []

    def record_frame(self, latency_ms: float, dropped: bool = False):
        """Record frame processing."""
        self.prometheus.record_frame_processed(latency_ms)
        self.frame_count += 1
        self.latencies.append(latency_ms)

        if dropped:
            self.prometheus.record_frame_dropped()
            self.drop_count += 1

        # Keep only recent samples
        if len(self.latencies) > 1000:
            self.latencies = self.latencies[-500:]

    def record_system_metrics(
        self,
        gpu_utilization: float,
        memory_mb: float,
        disk_io: float,
    ):
        """Record system resource metrics."""
        self.prometheus.set_gpu_utilization(gpu_utilization)
        self.prometheus.set_memory_usage(memory_mb)
        self.prometheus.set_disk_io(disk_io)

        self.gpu_samples.append(gpu_utilization)
        self.memory_samples.append(memory_mb)

        if len(self.gpu_samples) > 1000:
            self.gpu_samples = self.gpu_samples[-500:]
        if len(self.memory_samples) > 1000:
            self.memory_samples = self.memory_samples[-500:]

    def record_api_request(self, method: str, endpoint: str, status_code: int):
        """Record API request."""
        self.prometheus.record_api_request(method, endpoint)

        if status_code >= 400:
            self.prometheus.record_api_error(method, endpoint, status_code)

    def record_session(self, active_sessions: int):
        """Record session metric."""
        if active_sessions > 0:
            self.prometheus.record_session_created()
        self.prometheus.set_active_sessions(active_sessions)

    def get_snapshot(self) -> MetricSnapshot:
        """Get current metrics snapshot."""
        uptime_sec = time.time() - self.start_time
        avg_latency = (
            sum(self.latencies) / len(self.latencies) if self.latencies else 0.0
        )
        error_rate = (
            self.drop_count / self.frame_count if self.frame_count > 0 else 0.0
        )
        avg_gpu = sum(self.gpu_samples) / len(self.gpu_samples) if self.gpu_samples else 0.0
        avg_memory = (
            sum(self.memory_samples) / len(self.memory_samples)
            if self.memory_samples
            else 0.0
        )

        return MetricSnapshot(
            timestamp=datetime.now(timezone.utc),
            frames_processed=self.frame_count,
            frames_dropped=self.drop_count,
            api_requests=0,  # Would need to track separately
            average_latency_ms=avg_latency,
            gpu_utilization_pct=avg_gpu,
            memory_used_mb=avg_memory,
            queue_depth=0,  # Would need to get from session manager
            error_count=self.drop_count,
            error_rate=error_rate,
        )

    def get_prometheus_metrics(self) -> Optional[str]:
        """Get Prometheus-format metrics."""
        return self.prometheus.get_metrics()


# Global metrics collector
metrics_collector = MetricsCollector()
