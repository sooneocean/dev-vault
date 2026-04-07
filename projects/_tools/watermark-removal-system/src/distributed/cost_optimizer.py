"""
Cost optimization for compute resources.

Tracks and optimizes GPU memory usage, compute costs, and processing efficiency.
"""

import logging
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class CostMetric(str, Enum):
    """Cost metrics to track."""
    GPU_MEMORY = "gpu_memory"  # MB
    GPU_TIME = "gpu_time"  # milliseconds
    COMPUTE_COST = "compute_cost"  # Arbitrary cost units
    THROUGHPUT = "throughput"  # Frames per second


@dataclass
class CostEstimate:
    """Estimated cost for a processing operation."""
    operation: str
    estimated_memory_mb: float
    estimated_time_ms: float
    estimated_cost_units: float
    confidence: float  # 0.0 to 1.0


@dataclass
class ProcessingMetric:
    """Metric for a processing operation."""
    operation: str
    frames_processed: int = 0
    total_memory_mb: float = 0.0
    total_time_ms: float = 0.0
    total_cost_units: float = 0.0
    recorded_at: datetime = None

    def __post_init__(self):
        if self.recorded_at is None:
            self.recorded_at = datetime.now(timezone.utc)


class CostModel:
    """Model for estimating processing costs."""

    def __init__(self):
        self.operation_costs: Dict[str, ProcessingMetric] = {}
        self.frame_resolution_factor = 1.0

    def estimate_cost(self, operation: str, frames: int = 1, resolution: Tuple[int, int] = None) -> CostEstimate:
        """Estimate cost for operation."""
        # Get historical data if available
        if operation in self.operation_costs:
            metric = self.operation_costs[operation]
            avg_memory = metric.total_memory_mb / max(metric.frames_processed, 1)
            avg_time = metric.total_time_ms / max(metric.frames_processed, 1)
            avg_cost = metric.total_cost_units / max(metric.frames_processed, 1)
            confidence = min(1.0, metric.frames_processed / 100.0)
        else:
            # Use default estimates
            avg_memory = 256.0  # 256 MB per frame
            avg_time = 50.0  # 50 ms per frame
            avg_cost = 1.0
            confidence = 0.1

        # Adjust for resolution
        if resolution:
            width, height = resolution
            pixels = width * height
            resolution_factor = pixels / (1920 * 1080)  # Normalize to 1080p
            avg_memory *= resolution_factor
            avg_time *= resolution_factor
            avg_cost *= resolution_factor

        return CostEstimate(
            operation=operation,
            estimated_memory_mb=avg_memory * frames,
            estimated_time_ms=avg_time * frames,
            estimated_cost_units=avg_cost * frames,
            confidence=confidence,
        )

    def record_cost(
        self,
        operation: str,
        frames: int,
        memory_mb: float,
        time_ms: float,
        cost_units: float = None,
    ):
        """Record actual cost for operation."""
        if cost_units is None:
            cost_units = (memory_mb / 256.0) * (time_ms / 50.0)

        if operation not in self.operation_costs:
            self.operation_costs[operation] = ProcessingMetric(
                operation=operation,
                frames_processed=0,
                total_memory_mb=0.0,
                total_time_ms=0.0,
                total_cost_units=0.0,
            )

        metric = self.operation_costs[operation]
        metric.frames_processed += frames
        metric.total_memory_mb += memory_mb
        metric.total_time_ms += time_ms
        metric.total_cost_units += cost_units
        metric.recorded_at = datetime.now(timezone.utc)

        logger.debug(f"Recorded {operation}: {frames}f, {memory_mb:.0f}MB, {time_ms:.0f}ms")

    def get_operation_stats(self, operation: str) -> Optional[Dict[str, Any]]:
        """Get statistics for operation."""
        if operation not in self.operation_costs:
            return None

        metric = self.operation_costs[operation]
        return {
            "operation": operation,
            "frames_processed": metric.frames_processed,
            "avg_memory_mb": metric.total_memory_mb / max(metric.frames_processed, 1),
            "avg_time_ms": metric.total_time_ms / max(metric.frames_processed, 1),
            "avg_cost_units": metric.total_cost_units / max(metric.frames_processed, 1),
            "total_cost_units": metric.total_cost_units,
        }

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all operations."""
        return {
            op: self.get_operation_stats(op)
            for op in self.operation_costs.keys()
        }


class OptimizationStrategy:
    """Strategy for optimizing processing."""

    def __init__(self, cost_model: CostModel):
        self.cost_model = cost_model
        self.optimizations: List[str] = []

    def suggest_optimizations(self, operations: List[str]) -> List[Dict[str, Any]]:
        """Suggest optimizations for operations."""
        suggestions = []

        for op in operations:
            stats = self.cost_model.get_operation_stats(op)
            if not stats:
                continue

            avg_cost = stats["avg_cost_units"]
            avg_time = stats["avg_time_ms"]
            avg_memory = stats["avg_memory_mb"]

            # High memory usage
            if avg_memory > 1024:  # > 1GB per frame
                suggestions.append({
                    "operation": op,
                    "issue": "HIGH_MEMORY",
                    "metric": avg_memory,
                    "recommendation": "Consider model quantization or batch reduction",
                    "potential_savings": "20-40%",
                })

            # High latency
            if avg_time > 200:  # > 200ms per frame
                suggestions.append({
                    "operation": op,
                    "issue": "HIGH_LATENCY",
                    "metric": avg_time,
                    "recommendation": "Consider GPU optimization or parallel processing",
                    "potential_savings": "15-30%",
                })

            # Inefficient cost ratio
            if avg_cost > 5.0:
                suggestions.append({
                    "operation": op,
                    "issue": "INEFFICIENT",
                    "metric": avg_cost,
                    "recommendation": "Consider faster algorithm or hardware",
                    "potential_savings": "25-50%",
                })

        return suggestions

    def apply_optimization(self, optimization: str) -> bool:
        """Apply optimization."""
        self.optimizations.append(optimization)
        logger.info(f"Applied optimization: {optimization}")
        return True

    def get_recommendations(self) -> List[Dict[str, str]]:
        """Get optimization recommendations."""
        return [
            {
                "id": "batch_processing",
                "title": "Enable batch processing",
                "description": "Process multiple frames together to reduce overhead",
                "impact": "High",
            },
            {
                "id": "early_exit",
                "title": "Implement early exit",
                "description": "Skip frames with high confidence scores",
                "impact": "Medium",
            },
            {
                "id": "model_quantization",
                "title": "Use quantized models",
                "description": "Use INT8 or FP16 instead of FP32 models",
                "impact": "High",
            },
            {
                "id": "async_processing",
                "title": "Enable async processing",
                "description": "Process frames asynchronously for better throughput",
                "impact": "Medium",
            },
            {
                "id": "caching",
                "title": "Enable frame caching",
                "description": "Cache results of similar frames",
                "impact": "Medium",
            },
        ]


class CostOptimizer:
    """Main cost optimization engine."""

    def __init__(self):
        self.cost_model = CostModel()
        self.strategy = OptimizationStrategy(self.cost_model)
        self.active_optimizations: List[str] = []
        self.optimization_history: List[Dict[str, Any]] = []

    def estimate_operation_cost(
        self,
        operation: str,
        frames: int = 1,
        resolution: tuple = None,
    ) -> CostEstimate:
        """Estimate cost for operation."""
        return self.cost_model.estimate_cost(operation, frames, resolution)

    def record_operation(
        self,
        operation: str,
        frames: int,
        memory_mb: float,
        time_ms: float,
    ):
        """Record actual operation metrics."""
        self.cost_model.record_cost(operation, frames, memory_mb, time_ms)

    def get_cost_report(self) -> Dict[str, Any]:
        """Get comprehensive cost report."""
        stats = self.cost_model.get_all_stats()

        total_frames = sum(s.get("frames_processed", 0) for s in stats.values())
        total_cost = sum(s.get("total_cost_units", 0) for s in stats.values())

        return {
            "total_frames_processed": total_frames,
            "total_cost_units": total_cost,
            "avg_cost_per_frame": total_cost / max(total_frames, 1),
            "operations": stats,
            "active_optimizations": self.active_optimizations,
        }

    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """Get optimization suggestions."""
        operations = list(self.cost_model.operation_costs.keys())
        return self.strategy.suggest_optimizations(operations)

    def enable_optimization(self, optimization_id: str) -> bool:
        """Enable optimization."""
        if optimization_id not in self.active_optimizations:
            self.active_optimizations.append(optimization_id)
            self.optimization_history.append({
                "optimization": optimization_id,
                "enabled_at": datetime.now(timezone.utc).isoformat(),
            })
            logger.info(f"Enabled optimization: {optimization_id}")
            return True
        return False

    def disable_optimization(self, optimization_id: str) -> bool:
        """Disable optimization."""
        if optimization_id in self.active_optimizations:
            self.active_optimizations.remove(optimization_id)
            self.optimization_history.append({
                "optimization": optimization_id,
                "disabled_at": datetime.now(timezone.utc).isoformat(),
            })
            logger.info(f"Disabled optimization: {optimization_id}")
            return True
        return False

    def get_efficiency_score(self) -> float:
        """Calculate overall efficiency score (0.0 to 1.0)."""
        stats = self.cost_model.get_all_stats()
        if not stats:
            return 0.5  # Neutral score

        # Score based on cost per frame
        costs = [s.get("avg_cost_units", 1.0) for s in stats.values()]
        avg_cost = sum(costs) / len(costs)

        # Normalize: lower is better
        # Assume 1.0 is ideal, 10.0 is poor
        score = max(0.0, 1.0 - (avg_cost - 1.0) / 9.0)
        return min(1.0, score)

    def reset(self):
        """Reset optimizer."""
        self.cost_model = CostModel()
        self.active_optimizations.clear()


# Global cost optimizer instance
cost_optimizer: Optional[CostOptimizer] = None


def init_cost_optimizer():
    """Initialize global cost optimizer."""
    global cost_optimizer
    cost_optimizer = CostOptimizer()
    logger.info("Cost optimizer initialized")


def get_cost_optimizer() -> CostOptimizer:
    """Get global cost optimizer instance."""
    global cost_optimizer
    if cost_optimizer is None:
        init_cost_optimizer()
    return cost_optimizer
