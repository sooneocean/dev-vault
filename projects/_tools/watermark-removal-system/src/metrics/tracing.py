"""
Distributed tracing for request flow analysis and debugging.

Supports OpenTelemetry with Jaeger/Zipkin exporters.
"""

import logging
import uuid
import time
from typing import Optional, Dict, Any
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Try to import OpenTelemetry
try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    HAS_OTEL = True
except ImportError:
    HAS_OTEL = False
    logger.warning("OpenTelemetry not available, tracing disabled")


@dataclass
class TraceSpan:
    """A trace span for a single operation."""
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: Optional[float]
    attributes: Dict[str, Any]
    status: str  # "ok", "error", "canceled"


class SimpleTracer:
    """Simple fallback tracer when OpenTelemetry not available."""

    def __init__(self, service_name: str = "watermark-removal"):
        self.service_name = service_name
        self.spans: list[TraceSpan] = []
        self.current_trace_id = None

    def start_span(
        self,
        operation_name: str,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> TraceSpan:
        """Start a new trace span."""
        if self.current_trace_id is None:
            self.current_trace_id = str(uuid.uuid4())

        span = TraceSpan(
            span_id=str(uuid.uuid4()),
            trace_id=self.current_trace_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_time=datetime.now(timezone.utc),
            end_time=None,
            duration_ms=None,
            attributes=attributes or {},
            status="ok",
        )

        self.spans.append(span)
        logger.debug(f"Started span: {operation_name} ({span.span_id})")
        return span

    def end_span(self, span: TraceSpan, status: str = "ok"):
        """End a trace span."""
        span.end_time = datetime.now(timezone.utc)
        span.duration_ms = (span.end_time - span.start_time).total_seconds() * 1000
        span.status = status
        logger.debug(
            f"Ended span: {span.operation_name} ({span.span_id}) - {span.duration_ms:.2f}ms"
        )

    def get_spans(self, trace_id: Optional[str] = None) -> list[TraceSpan]:
        """Get spans for a trace."""
        if trace_id is None:
            trace_id = self.current_trace_id

        return [s for s in self.spans if s.trace_id == trace_id]

    def clear_old_spans(self, max_spans: int = 10000):
        """Clear old spans to avoid memory overflow."""
        if len(self.spans) > max_spans:
            self.spans = self.spans[-max_spans // 2 :]


class OTelTracer:
    """OpenTelemetry tracer wrapper."""

    def __init__(
        self,
        service_name: str = "watermark-removal",
        jaeger_host: str = "localhost",
        jaeger_port: int = 6831,
    ):
        self.service_name = service_name

        if HAS_OTEL:
            try:
                jaeger_exporter = JaegerExporter(
                    agent_host_name=jaeger_host,
                    agent_port=jaeger_port,
                )
                trace.set_tracer_provider(TracerProvider())
                trace.get_tracer_provider().add_span_processor(
                    BatchSpanProcessor(jaeger_exporter)
                )
                self.tracer = trace.get_tracer(__name__)
                self.enabled = True
                logger.info(f"OpenTelemetry tracer initialized (Jaeger: {jaeger_host}:{jaeger_port})")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenTelemetry: {e}")
                self.enabled = False
        else:
            self.enabled = False
            logger.warning("OpenTelemetry not available")

    @contextmanager
    def trace_operation(
        self,
        operation_name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """Context manager for tracing an operation."""
        if not self.enabled:
            yield None
            return

        with self.tracer.start_as_current_span(operation_name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)

            try:
                yield span
            except Exception as e:
                span.record_exception(e)
                span.set_attribute("error", True)
                raise


class DistributedTracer:
    """High-level distributed tracing."""

    def __init__(self, service_name: str = "watermark-removal"):
        self.service_name = service_name

        # Use OTel if available, otherwise fallback to simple tracer
        if HAS_OTEL:
            self.otel_tracer = OTelTracer(service_name)
            self.simple_tracer = None
        else:
            self.otel_tracer = None
            self.simple_tracer = SimpleTracer(service_name)

    @contextmanager
    def trace_request(self, request_id: str, endpoint: str):
        """Trace an API request."""
        if self.otel_tracer and self.otel_tracer.enabled:
            with self.otel_tracer.trace_operation(
                f"http.request {endpoint}",
                attributes={
                    "request_id": request_id,
                    "endpoint": endpoint,
                    "service": self.service_name,
                },
            ) as span:
                yield span
        else:
            span = self.simple_tracer.start_span(
                f"http.request {endpoint}",
                attributes={"request_id": request_id, "endpoint": endpoint},
            )
            try:
                yield span
            finally:
                self.simple_tracer.end_span(span)

    @contextmanager
    def trace_stage(
        self,
        stage_name: str,
        parent_span_id: Optional[str] = None,
    ):
        """Trace a processing stage."""
        if self.otel_tracer and self.otel_tracer.enabled:
            with self.otel_tracer.trace_operation(
                f"process.stage {stage_name}",
                attributes={"stage": stage_name},
            ) as span:
                yield span
        else:
            span = self.simple_tracer.start_span(
                f"process.stage {stage_name}",
                parent_span_id=parent_span_id,
                attributes={"stage": stage_name},
            )
            try:
                yield span
            finally:
                self.simple_tracer.end_span(span)

    def get_trace_summary(self, trace_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get summary of a trace."""
        if self.simple_tracer is None:
            return None

        spans = self.simple_tracer.get_spans(trace_id)
        if not spans:
            return None

        total_duration = sum(s.duration_ms for s in spans if s.duration_ms)
        stages = [s for s in spans if "process.stage" in s.operation_name]
        stage_breakdown = {s.operation_name: s.duration_ms for s in stages if s.duration_ms}

        return {
            "trace_id": spans[0].trace_id,
            "total_spans": len(spans),
            "total_duration_ms": total_duration,
            "stages": stage_breakdown,
            "status": spans[-1].status if spans else "unknown",
        }


# Global distributed tracer
distributed_tracer = DistributedTracer()
