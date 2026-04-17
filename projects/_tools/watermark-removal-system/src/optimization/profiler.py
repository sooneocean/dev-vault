"""
Performance profiling and bottleneck identification.

Tracks execution time, memory usage, and identifies optimization opportunities.
"""

import logging
import time
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class ProfileScope(str, Enum):
    """Profiling scope levels."""
    FUNCTION = "function"
    BLOCK = "block"
    STAGE = "stage"


@dataclass
class ExecutionTrace:
    """Execution trace for a function/block."""
    name: str
    scope: ProfileScope
    start_time: float
    end_time: float = 0.0
    duration_ms: float = 0.0
    memory_before_mb: float = 0.0
    memory_after_mb: float = 0.0
    memory_delta_mb: float = 0.0
    call_count: int = 0
    error: Optional[str] = None


@dataclass
class ProfileStats:
    """Statistics for a profiled entity."""
    name: str
    call_count: int = 0
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    min_time_ms: float = float("inf")
    max_time_ms: float = 0.0
    memory_delta_mb: float = 0.0
    error_count: int = 0


class ExecutionProfiler:
    """Profile function and block execution."""

    def __init__(self):
        self.traces: List[ExecutionTrace] = []
        self.stats: Dict[str, ProfileStats] = {}
        self.is_profiling = False

    def _get_memory_mb(self) -> float:
        """Get current memory usage (simulated)."""
        # In real implementation, use psutil.Process().memory_info().rss / 1024 / 1024
        return 0.0

    @contextmanager
    def profile_block(self, name: str, scope: ProfileScope = ProfileScope.BLOCK):
        """Context manager for profiling a code block."""
        start_time = time.time()
        mem_before = self._get_memory_mb()

        try:
            yield
            error = None
        except Exception as e:
            error = str(e)
            raise
        finally:
            end_time = time.time()
            mem_after = self._get_memory_mb()

            duration_ms = (end_time - start_time) * 1000
            memory_delta = mem_after - mem_before

            trace = ExecutionTrace(
                name=name,
                scope=scope,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                memory_before_mb=mem_before,
                memory_after_mb=mem_after,
                memory_delta_mb=memory_delta,
                error=error,
            )

            self.traces.append(trace)
            self._update_stats(name, duration_ms, memory_delta, error is not None)

    def profile_function(self, func: Callable) -> Callable:
        """Decorator for profiling function execution."""
        def wrapper(*args, **kwargs):
            with self.profile_block(func.__name__, ProfileScope.FUNCTION):
                return func(*args, **kwargs)

        return wrapper

    def _update_stats(self, name: str, duration_ms: float, memory_delta: float, had_error: bool):
        """Update statistics for a profiled entity."""
        if name not in self.stats:
            self.stats[name] = ProfileStats(name=name)

        stat = self.stats[name]
        stat.call_count += 1
        stat.total_time_ms += duration_ms
        stat.avg_time_ms = stat.total_time_ms / stat.call_count
        stat.min_time_ms = min(stat.min_time_ms, duration_ms)
        stat.max_time_ms = max(stat.max_time_ms, duration_ms)
        stat.memory_delta_mb += memory_delta
        if had_error:
            stat.error_count += 1

    def get_stats(self, name: str = None) -> Optional[ProfileStats]:
        """Get statistics for a profiled entity."""
        if name:
            return self.stats.get(name)
        return None

    def get_all_stats(self) -> Dict[str, ProfileStats]:
        """Get all statistics."""
        return self.stats.copy()

    def get_slowest_functions(self, limit: int = 10) -> List[Tuple[str, float]]:
        """Get slowest functions by total time."""
        return sorted(
            [(name, stat.total_time_ms) for name, stat in self.stats.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:limit]

    def get_memory_heavy_functions(self, limit: int = 10) -> List[Tuple[str, float]]:
        """Get functions with highest memory usage."""
        return sorted(
            [(name, stat.memory_delta_mb) for name, stat in self.stats.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:limit]

    def reset(self):
        """Reset profiler."""
        self.traces.clear()
        self.stats.clear()

    def get_report(self) -> Dict[str, Any]:
        """Get comprehensive profiling report."""
        if not self.stats:
            return {}

        total_time = sum(s.total_time_ms for s in self.stats.values())
        total_memory = sum(s.memory_delta_mb for s in self.stats.values())

        return {
            "total_calls": sum(s.call_count for s in self.stats.values()),
            "total_time_ms": total_time,
            "total_memory_mb": total_memory,
            "functions": len(self.stats),
            "slowest": self.get_slowest_functions(5),
            "memory_heavy": self.get_memory_heavy_functions(5),
            "errors": sum(s.error_count for s in self.stats.values()),
        }


class MemoryProfiler:
    """Profile memory usage patterns."""

    def __init__(self):
        self.allocations: Dict[str, List[float]] = {}  # name -> sizes
        self.peak_memory_mb = 0.0
        self.total_allocated_mb = 0.0

    def record_allocation(self, name: str, size_mb: float):
        """Record memory allocation."""
        if name not in self.allocations:
            self.allocations[name] = []

        self.allocations[name].append(size_mb)
        self.total_allocated_mb += size_mb
        self.peak_memory_mb = max(self.peak_memory_mb, sum(self.allocations[name]))

    def get_allocation_stats(self, name: str) -> Optional[Dict[str, float]]:
        """Get allocation statistics."""
        if name not in self.allocations:
            return None

        sizes = self.allocations[name]
        return {
            "count": len(sizes),
            "total_mb": sum(sizes),
            "avg_mb": sum(sizes) / len(sizes) if sizes else 0.0,
            "min_mb": min(sizes) if sizes else 0.0,
            "max_mb": max(sizes) if sizes else 0.0,
        }

    def get_top_allocators(self, limit: int = 10) -> List[Tuple[str, float]]:
        """Get allocations by total size."""
        return sorted(
            [(name, sum(sizes)) for name, sizes in self.allocations.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:limit]

    def reset(self):
        """Reset profiler."""
        self.allocations.clear()
        self.peak_memory_mb = 0.0
        self.total_allocated_mb = 0.0

    def get_report(self) -> Dict[str, Any]:
        """Get memory profiling report."""
        return {
            "peak_memory_mb": self.peak_memory_mb,
            "total_allocated_mb": self.total_allocated_mb,
            "allocation_sites": len(self.allocations),
            "top_allocators": self.get_top_allocators(5),
        }


class BottleneckAnalyzer:
    """Identify performance bottlenecks."""

    def __init__(self):
        self.execution_profiler = ExecutionProfiler()
        self.memory_profiler = MemoryProfiler()
        self.bottlenecks: List[Dict[str, Any]] = []

    def analyze_execution_profile(self) -> List[Dict[str, Any]]:
        """Analyze execution profile for bottlenecks."""
        bottlenecks = []

        stats = self.execution_profiler.get_all_stats()
        if not stats:
            return bottlenecks

        total_time = sum(s.total_time_ms for s in stats.values())

        for name, stat in stats.items():
            # High time consumption
            if stat.total_time_ms > total_time * 0.3:  # >30% of total time
                bottlenecks.append({
                    "type": "TIME_BOTTLENECK",
                    "name": name,
                    "metric": f"{stat.total_time_ms:.1f}ms ({stat.total_time_ms / total_time * 100:.1f}%)",
                    "recommendation": "Optimize algorithm or parallelize",
                    "potential_improvement": "20-50%",
                })

            # High variability
            if stat.max_time_ms > stat.min_time_ms * 2.0:
                bottlenecks.append({
                    "type": "VARIANCE_BOTTLENECK",
                    "name": name,
                    "metric": f"{stat.max_time_ms / stat.min_time_ms:.1f}x variance",
                    "recommendation": "Investigate irregular execution patterns",
                    "potential_improvement": "10-30%",
                })

            # High error rate
            if stat.error_count > 0 and stat.call_count > 0:
                error_rate = stat.error_count / stat.call_count * 100
                if error_rate > 5:
                    bottlenecks.append({
                        "type": "ERROR_BOTTLENECK",
                        "name": name,
                        "metric": f"{error_rate:.1f}% error rate",
                        "recommendation": "Fix error handling or input validation",
                        "potential_improvement": "Variable",
                    })

        self.bottlenecks.extend(bottlenecks)
        return bottlenecks

    def analyze_memory_profile(self) -> List[Dict[str, Any]]:
        """Analyze memory profile for bottlenecks."""
        bottlenecks = []

        for allocator, total_mb in self.memory_profiler.get_top_allocators(5):
            if total_mb > 256:  # >256MB
                bottlenecks.append({
                    "type": "MEMORY_BOTTLENECK",
                    "name": allocator,
                    "metric": f"{total_mb:.1f}MB",
                    "recommendation": "Reduce memory footprint or use streaming",
                    "potential_improvement": "30-60%",
                })

        self.bottlenecks.extend(bottlenecks)
        return bottlenecks

    def get_optimization_plan(self) -> Dict[str, Any]:
        """Generate optimization plan based on analysis."""
        exec_bottlenecks = self.analyze_execution_profile()
        mem_bottlenecks = self.analyze_memory_profile()

        plan = {
            "summary": {
                "total_bottlenecks": len(exec_bottlenecks) + len(mem_bottlenecks),
                "execution_issues": len(exec_bottlenecks),
                "memory_issues": len(mem_bottlenecks),
            },
            "bottlenecks": self.bottlenecks,
            "priority_order": sorted(
                self.bottlenecks,
                key=lambda x: x.get("metric", ""),
                reverse=True,
            ),
        }

        return plan

    def reset(self):
        """Reset analyzer."""
        self.execution_profiler.reset()
        self.memory_profiler.reset()
        self.bottlenecks.clear()


# Global profiler instances
execution_profiler: Optional[ExecutionProfiler] = None
bottleneck_analyzer: Optional[BottleneckAnalyzer] = None


def init_profilers():
    """Initialize global profilers."""
    global execution_profiler, bottleneck_analyzer
    execution_profiler = ExecutionProfiler()
    bottleneck_analyzer = BottleneckAnalyzer()
    logger.info("Performance profilers initialized")


def get_execution_profiler() -> ExecutionProfiler:
    """Get global execution profiler."""
    global execution_profiler
    if execution_profiler is None:
        init_profilers()
    return execution_profiler


def get_bottleneck_analyzer() -> BottleneckAnalyzer:
    """Get global bottleneck analyzer."""
    global bottleneck_analyzer
    if bottleneck_analyzer is None:
        init_profilers()
    return bottleneck_analyzer
