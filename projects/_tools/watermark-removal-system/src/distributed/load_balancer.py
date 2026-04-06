"""
Load balancing strategies for distributing work across workers.

Implements round-robin, least-busy, and weighted distribution strategies.
"""

import logging
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime, timezone
from abc import ABC, abstractmethod
from enum import Enum

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(str, Enum):
    """Load balancing strategy types."""
    ROUND_ROBIN = "round_robin"
    LEAST_BUSY = "least_busy"
    WEIGHTED = "weighted"
    RANDOM = "random"


@dataclass
class WorkerStats:
    """Statistics for a worker."""
    worker_id: str
    task_count: int = 0
    completed_count: int = 0
    failed_count: int = 0
    avg_latency_ms: float = 0.0
    current_load: float = 0.0
    status: str = "idle"
    last_heartbeat: Optional[datetime] = None
    capacity: int = 10  # Tasks per worker


class LoadBalancer(ABC):
    """Abstract base class for load balancers."""

    @abstractmethod
    def select_worker(self) -> Optional[str]:
        """Select worker for task assignment."""
        pass

    @abstractmethod
    def update_worker_stats(self, worker_id: str, stats: WorkerStats):
        """Update worker statistics."""
        pass

    @abstractmethod
    def remove_worker(self, worker_id: str) -> bool:
        """Remove worker from pool."""
        pass

    @abstractmethod
    def get_load_distribution(self) -> Dict[str, float]:
        """Get current load distribution across workers."""
        pass


class RoundRobinBalancer(LoadBalancer):
    """Round-robin load balancer."""

    def __init__(self, workers: List[str] = None):
        self.workers = workers or []
        self.current_index = 0
        self.worker_stats: Dict[str, WorkerStats] = {
            w: WorkerStats(worker_id=w) for w in self.workers
        }

    def select_worker(self) -> Optional[str]:
        """Select next worker in round-robin fashion."""
        if not self.workers:
            return None

        worker = self.workers[self.current_index % len(self.workers)]
        self.current_index += 1
        return worker

    def update_worker_stats(self, worker_id: str, stats: WorkerStats):
        """Update worker statistics."""
        self.worker_stats[worker_id] = stats

    def remove_worker(self, worker_id: str) -> bool:
        """Remove worker."""
        if worker_id in self.workers:
            self.workers.remove(worker_id)
            del self.worker_stats[worker_id]
            return True
        return False

    def get_load_distribution(self) -> Dict[str, float]:
        """Get load distribution."""
        if not self.workers:
            return {}
        return {w: 1.0 / len(self.workers) for w in self.workers}


class LeastBusyBalancer(LoadBalancer):
    """Least-busy load balancer (select worker with lowest load)."""

    def __init__(self, workers: List[str] = None):
        self.workers = workers or []
        self.worker_stats: Dict[str, WorkerStats] = {
            w: WorkerStats(worker_id=w) for w in self.workers
        }

    def select_worker(self) -> Optional[str]:
        """Select least busy worker."""
        if not self.workers:
            return None

        least_busy = min(
            self.workers,
            key=lambda w: self.worker_stats[w].current_load,
        )
        return least_busy

    def update_worker_stats(self, worker_id: str, stats: WorkerStats):
        """Update worker statistics."""
        self.worker_stats[worker_id] = stats

    def remove_worker(self, worker_id: str) -> bool:
        """Remove worker."""
        if worker_id in self.workers:
            self.workers.remove(worker_id)
            del self.worker_stats[worker_id]
            return True
        return False

    def get_load_distribution(self) -> Dict[str, float]:
        """Get load distribution (inverse of current load)."""
        if not self.workers:
            return {}

        total_load = sum(s.current_load for s in self.worker_stats.values())
        if total_load == 0:
            return {w: 1.0 / len(self.workers) for w in self.workers}

        return {
            w: 1.0 - (self.worker_stats[w].current_load / total_load)
            for w in self.workers
        }


class WeightedBalancer(LoadBalancer):
    """Weighted load balancer (consider capacity and performance)."""

    def __init__(self, workers: List[str] = None, weights: Dict[str, float] = None):
        self.workers = workers or []
        self.weights = weights or {w: 1.0 for w in self.workers}
        self.worker_stats: Dict[str, WorkerStats] = {
            w: WorkerStats(worker_id=w) for w in self.workers
        }

    def select_worker(self) -> Optional[str]:
        """Select worker based on weighted score."""
        if not self.workers:
            return None

        scores = {}
        for worker in self.workers:
            stats = self.worker_stats[worker]
            weight = self.weights.get(worker, 1.0)

            # Score = (remaining_capacity / total_capacity) * weight
            utilization = stats.task_count / stats.capacity
            remaining = max(0, 1.0 - utilization)
            scores[worker] = remaining * weight

        # Select worker with highest score
        best_worker = max(scores.items(), key=lambda x: x[1])[0]
        return best_worker

    def update_worker_stats(self, worker_id: str, stats: WorkerStats):
        """Update worker statistics."""
        self.worker_stats[worker_id] = stats

    def remove_worker(self, worker_id: str) -> bool:
        """Remove worker."""
        if worker_id in self.workers:
            self.workers.remove(worker_id)
            del self.worker_stats[worker_id]
            if worker_id in self.weights:
                del self.weights[worker_id]
            return True
        return False

    def get_load_distribution(self) -> Dict[str, float]:
        """Get load distribution."""
        if not self.workers:
            return {}

        scores = {}
        for worker in self.workers:
            stats = self.worker_stats[worker]
            weight = self.weights.get(worker, 1.0)
            utilization = stats.task_count / stats.capacity
            remaining = max(0, 1.0 - utilization)
            scores[worker] = remaining * weight

        total_score = sum(scores.values())
        if total_score == 0:
            return {w: 1.0 / len(self.workers) for w in self.workers}

        return {w: scores[w] / total_score for w in self.workers}


class AdaptiveBalancer(LoadBalancer):
    """Adaptive balancer that switches strategy based on conditions."""

    def __init__(self, workers: List[str] = None, initial_strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_BUSY):
        self.workers = workers or []
        self.worker_stats: Dict[str, WorkerStats] = {
            w: WorkerStats(worker_id=w) for w in self.workers
        }
        self.current_strategy = initial_strategy
        self.balancers = {
            LoadBalancingStrategy.ROUND_ROBIN: RoundRobinBalancer(workers),
            LoadBalancingStrategy.LEAST_BUSY: LeastBusyBalancer(workers),
            LoadBalancingStrategy.WEIGHTED: WeightedBalancer(workers),
        }

    def select_worker(self) -> Optional[str]:
        """Select worker using current strategy."""
        return self.balancers[self.current_strategy].select_worker()

    def update_worker_stats(self, worker_id: str, stats: WorkerStats):
        """Update worker statistics and adapt strategy if needed."""
        self.worker_stats[worker_id] = stats

        # Update all balancers
        for balancer in self.balancers.values():
            balancer.update_worker_stats(worker_id, stats)

        # Switch strategy based on conditions
        self._adapt_strategy()

    def remove_worker(self, worker_id: str) -> bool:
        """Remove worker."""
        if worker_id in self.workers:
            self.workers.remove(worker_id)
            del self.worker_stats[worker_id]
            for balancer in self.balancers.values():
                balancer.remove_worker(worker_id)
            return True
        return False

    def get_load_distribution(self) -> Dict[str, float]:
        """Get load distribution."""
        return self.balancers[self.current_strategy].get_load_distribution()

    def _adapt_strategy(self):
        """Adapt strategy based on current load."""
        if not self.workers:
            return

        # Calculate load variance
        loads = [s.current_load for s in self.worker_stats.values()]
        if not loads:
            return

        avg_load = sum(loads) / len(loads)
        variance = sum((l - avg_load) ** 2 for l in loads) / len(loads)
        std_dev = variance ** 0.5

        # Switch to LEAST_BUSY if variance is high (unbalanced)
        if std_dev > avg_load * 0.5:
            self.current_strategy = LoadBalancingStrategy.LEAST_BUSY
        # Switch to ROUND_ROBIN if variance is low (balanced)
        elif std_dev < avg_load * 0.1:
            self.current_strategy = LoadBalancingStrategy.ROUND_ROBIN
        # Use WEIGHTED for normal conditions
        else:
            self.current_strategy = LoadBalancingStrategy.WEIGHTED


class LoadBalancerFactory:
    """Factory for creating load balancers."""

    @staticmethod
    def create(
        strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_BUSY,
        workers: List[str] = None,
        **kwargs,
    ) -> LoadBalancer:
        """
        Create load balancer.

        Args:
            strategy: Load balancing strategy
            workers: List of worker IDs
            **kwargs: Additional arguments

        Returns:
            Configured LoadBalancer instance
        """
        workers = workers or []

        if strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return RoundRobinBalancer(workers)
        elif strategy == LoadBalancingStrategy.LEAST_BUSY:
            return LeastBusyBalancer(workers)
        elif strategy == LoadBalancingStrategy.WEIGHTED:
            weights = kwargs.get("weights", {w: 1.0 for w in workers})
            return WeightedBalancer(workers, weights)
        else:
            return AdaptiveBalancer(workers, initial_strategy=strategy)


# Global load balancer instance
load_balancer: Optional[LoadBalancer] = None


def init_load_balancer(
    strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_BUSY,
    workers: List[str] = None,
    **kwargs,
):
    """Initialize global load balancer."""
    global load_balancer
    load_balancer = LoadBalancerFactory.create(strategy, workers, **kwargs)
    logger.info(f"Load balancer initialized: {strategy}")


def get_load_balancer() -> LoadBalancer:
    """Get global load balancer instance."""
    global load_balancer
    if load_balancer is None:
        init_load_balancer()
    return load_balancer
