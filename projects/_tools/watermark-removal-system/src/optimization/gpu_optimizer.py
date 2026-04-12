"""
GPU optimization for accelerated processing.

Includes memory pooling, CUDA kernel optimization, and compute/IO overlap.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class GPUMemoryPool(str, Enum):
    """GPU memory pool types."""
    DEFAULT = "default"
    MANAGED = "managed"  # Unified memory
    PINNED = "pinned"  # Host pinned memory


class ComputeStrategy(str, Enum):
    """Compute strategies."""
    SYNC = "sync"  # Synchronous computation
    ASYNC = "async"  # Asynchronous with overlapping
    STREAM = "stream"  # Multiple CUDA streams


@dataclass
class GPUMemoryStats:
    """GPU memory statistics."""
    total_memory_mb: float
    allocated_mb: float
    free_mb: float
    reserved_mb: float
    utilization_percent: float


@dataclass
class KernelProfile:
    """CUDA kernel profiling data."""
    kernel_name: str
    launch_count: int = 0
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    min_time_ms: float = float("inf")
    max_time_ms: float = 0.0
    registers_per_thread: int = 0
    shared_memory_bytes: int = 0


class GPUMemoryManager:
    """Manage GPU memory allocation and pooling."""

    def __init__(
        self,
        pool_type: GPUMemoryPool = GPUMemoryPool.DEFAULT,
        total_memory_mb: float = 2048.0,
    ):
        self.pool_type = pool_type
        self.total_memory_mb = total_memory_mb
        self.allocated_mb = 0.0
        self.allocations: Dict[str, float] = {}  # allocation_id -> size
        self.fragmentation_ratio = 0.0

    def allocate(self, size_mb: float, allocation_id: str = None) -> Tuple[bool, str]:
        """Allocate GPU memory."""
        if allocation_id is None:
            allocation_id = f"alloc_{len(self.allocations)}"

        if self.allocated_mb + size_mb > self.total_memory_mb:
            return False, f"Insufficient memory: need {size_mb}MB, have {self.total_memory_mb - self.allocated_mb}MB"

        self.allocations[allocation_id] = size_mb
        self.allocated_mb += size_mb
        self.fragmentation_ratio = self._compute_fragmentation()

        logger.debug(f"Allocated {size_mb}MB ({allocation_id}), used {self.allocated_mb}/{self.total_memory_mb}MB")
        return True, allocation_id

    def deallocate(self, allocation_id: str) -> bool:
        """Deallocate GPU memory."""
        if allocation_id not in self.allocations:
            return False

        size = self.allocations.pop(allocation_id)
        self.allocated_mb -= size
        self.fragmentation_ratio = self._compute_fragmentation()

        logger.debug(f"Deallocated {size}MB ({allocation_id}), used {self.allocated_mb}/{self.total_memory_mb}MB")
        return True

    def _compute_fragmentation(self) -> float:
        """Compute fragmentation ratio."""
        if not self.allocations:
            return 0.0

        # Simple fragmentation metric: ratio of free holes
        free_mb = self.total_memory_mb - self.allocated_mb
        return free_mb / self.total_memory_mb if self.total_memory_mb > 0 else 0.0

    def compact(self) -> bool:
        """Compact memory (simulated)."""
        # In real CUDA, this would involve data migration
        self.fragmentation_ratio = 0.0
        logger.info("Memory compaction complete")
        return True

    def get_stats(self) -> GPUMemoryStats:
        """Get memory statistics."""
        free_mb = self.total_memory_mb - self.allocated_mb
        utilization = (self.allocated_mb / self.total_memory_mb * 100) if self.total_memory_mb > 0 else 0.0

        return GPUMemoryStats(
            total_memory_mb=self.total_memory_mb,
            allocated_mb=self.allocated_mb,
            free_mb=free_mb,
            reserved_mb=self.allocated_mb,
            utilization_percent=utilization,
        )

    def clear(self):
        """Clear all allocations."""
        self.allocations.clear()
        self.allocated_mb = 0.0
        self.fragmentation_ratio = 0.0


class CUDAKernelOptimizer:
    """Optimize CUDA kernel execution."""

    def __init__(self):
        self.kernel_profiles: Dict[str, KernelProfile] = {}
        self.optimization_suggestions: List[Dict[str, Any]] = []

    def profile_kernel(
        self,
        kernel_name: str,
        execution_time_ms: float,
        registers_per_thread: int = 32,
        shared_memory_bytes: int = 0,
    ):
        """Profile kernel execution."""
        if kernel_name not in self.kernel_profiles:
            self.kernel_profiles[kernel_name] = KernelProfile(
                kernel_name=kernel_name,
                registers_per_thread=registers_per_thread,
                shared_memory_bytes=shared_memory_bytes,
            )

        profile = self.kernel_profiles[kernel_name]
        profile.launch_count += 1
        profile.total_time_ms += execution_time_ms
        profile.avg_time_ms = profile.total_time_ms / profile.launch_count
        profile.min_time_ms = min(profile.min_time_ms, execution_time_ms)
        profile.max_time_ms = max(profile.max_time_ms, execution_time_ms)

    def get_bottleneck_kernels(self) -> List[Tuple[str, float]]:
        """Get kernels consuming most time."""
        return sorted(
            [(k, p.total_time_ms) for k, p in self.kernel_profiles.items()],
            key=lambda x: x[1],
            reverse=True,
        )

    def optimize_kernel(self, kernel_name: str) -> Dict[str, Any]:
        """Get optimization suggestions for kernel."""
        if kernel_name not in self.kernel_profiles:
            return {}

        profile = self.kernel_profiles[kernel_name]
        suggestions = []

        # Register pressure
        if profile.registers_per_thread > 63:
            suggestions.append({
                "issue": "HIGH_REGISTER_PRESSURE",
                "current": profile.registers_per_thread,
                "recommendation": "Reduce register usage via loop unrolling reduction or data reordering",
                "potential_improvement": "10-20%",
            })

        # Shared memory usage
        if profile.shared_memory_bytes > 48000:
            suggestions.append({
                "issue": "HIGH_SHARED_MEMORY",
                "current": profile.shared_memory_bytes,
                "recommendation": "Use global memory with caching or reduce workgroup size",
                "potential_improvement": "15-30%",
            })

        # Execution variance
        if profile.max_time_ms > profile.min_time_ms * 1.5:
            suggestions.append({
                "issue": "HIGH_VARIANCE",
                "current": f"{profile.max_time_ms / profile.min_time_ms:.2f}x variation",
                "recommendation": "Add synchronization or balance workload distribution",
                "potential_improvement": "5-15%",
            })

        return {
            "kernel": kernel_name,
            "profile": {
                "launch_count": profile.launch_count,
                "avg_time_ms": profile.avg_time_ms,
                "min_time_ms": profile.min_time_ms,
                "max_time_ms": profile.max_time_ms,
            },
            "suggestions": suggestions,
        }

    def reset(self):
        """Reset optimizer."""
        self.kernel_profiles.clear()
        self.optimization_suggestions.clear()


class ComputeIOOverlapManager:
    """Manage overlapping of compute and IO operations."""

    def __init__(self, num_streams: int = 4):
        self.num_streams = num_streams
        self.stream_workload: List[List[str]] = [[] for _ in range(num_streams)]
        self.stream_busy_time: List[float] = [0.0] * num_streams
        self.total_time_ms = 0.0

    def schedule_compute_io(
        self,
        compute_time_ms: float,
        io_time_ms: float,
    ) -> Tuple[float, float, float]:
        """Schedule compute and IO for overlap."""
        # Find stream with least busy time
        min_stream = min(range(self.num_streams), key=lambda i: self.stream_busy_time[i])

        # Schedule compute on stream
        self.stream_busy_time[min_stream] += compute_time_ms
        self.stream_workload[min_stream].append(f"compute({compute_time_ms}ms)")

        # Schedule IO on different stream (for overlap)
        io_stream = (min_stream + 1) % self.num_streams
        self.stream_busy_time[io_stream] += io_time_ms
        self.stream_workload[io_stream].append(f"io({io_time_ms}ms)")

        # Total time is max of all streams (overlapped execution)
        total_time = max(self.stream_busy_time)
        sequential_time = compute_time_ms + io_time_ms
        overlap_efficiency = (sequential_time / total_time) if total_time > 0 else 1.0

        return total_time, sequential_time, overlap_efficiency

    def get_utilization(self) -> Dict[int, float]:
        """Get stream utilization."""
        if not self.stream_busy_time:
            return {}

        max_time = max(self.stream_busy_time)
        return {
            i: (time / max_time * 100) if max_time > 0 else 0.0
            for i, time in enumerate(self.stream_busy_time)
        }

    def reset(self):
        """Reset manager."""
        self.stream_workload = [[] for _ in range(self.num_streams)]
        self.stream_busy_time = [0.0] * self.num_streams
        self.total_time_ms = 0.0


class GPUOptimizer:
    """Main GPU optimization engine."""

    def __init__(
        self,
        total_memory_mb: float = 2048.0,
        num_streams: int = 4,
    ):
        self.memory_manager = GPUMemoryManager(total_memory_mb=total_memory_mb)
        self.kernel_optimizer = CUDAKernelOptimizer()
        self.io_overlap_manager = ComputeIOOverlapManager(num_streams)

    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze GPU performance."""
        memory_stats = self.memory_manager.get_stats()
        bottleneck_kernels = self.kernel_optimizer.get_bottleneck_kernels()
        stream_utilization = self.io_overlap_manager.get_utilization()

        return {
            "memory": {
                "total_mb": memory_stats.total_memory_mb,
                "allocated_mb": memory_stats.allocated_mb,
                "utilization_percent": memory_stats.utilization_percent,
                "fragmentation_ratio": self.memory_manager.fragmentation_ratio,
            },
            "kernels": {
                "bottlenecks": bottleneck_kernels[:5],
                "total_profiled": len(self.kernel_optimizer.kernel_profiles),
            },
            "io_overlap": {
                "streams": len(self.io_overlap_manager.stream_workload),
                "utilization": stream_utilization,
            },
        }

    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get optimization recommendations."""
        recommendations = []

        # Memory optimization
        memory_stats = self.memory_manager.get_stats()
        if memory_stats.utilization_percent > 80:
            recommendations.append({
                "category": "MEMORY",
                "issue": "HIGH_UTILIZATION",
                "current": f"{memory_stats.utilization_percent:.1f}%",
                "recommendation": "Consider memory pooling or data streaming",
                "potential_savings": "20-40%",
            })

        # Kernel optimization
        if self.kernel_optimizer.kernel_profiles:
            slowest = self.kernel_optimizer.get_bottleneck_kernels()[0]
            recommendations.append({
                "category": "KERNEL",
                "kernel": slowest[0],
                "time_ms": slowest[1],
                "recommendation": "Profile and optimize slowest kernel",
                "potential_savings": "15-30%",
            })

        # IO overlap
        min_util = min(self.io_overlap_manager.get_utilization().values()) if self.io_overlap_manager.get_utilization() else 0.0
        if min_util < 50:
            recommendations.append({
                "category": "IO_OVERLAP",
                "issue": "LOW_STREAM_UTILIZATION",
                "current": f"{min_util:.1f}%",
                "recommendation": "Improve compute/IO overlap with better scheduling",
                "potential_savings": "10-25%",
            })

        return recommendations

    def reset(self):
        """Reset optimizer."""
        self.memory_manager.clear()
        self.kernel_optimizer.reset()
        self.io_overlap_manager.reset()


# Global optimizer instance
gpu_optimizer: Optional[GPUOptimizer] = None


def init_gpu_optimizer(total_memory_mb: float = 2048.0):
    """Initialize global GPU optimizer."""
    global gpu_optimizer
    gpu_optimizer = GPUOptimizer(total_memory_mb=total_memory_mb)
    logger.info(f"GPU optimizer initialized with {total_memory_mb}MB")


def get_gpu_optimizer() -> GPUOptimizer:
    """Get global GPU optimizer instance."""
    global gpu_optimizer
    if gpu_optimizer is None:
        init_gpu_optimizer()
    return gpu_optimizer
