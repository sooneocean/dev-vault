"""
Distributed processing subsystem for horizontal scaling and optimization.

Includes:
- Asynchronous task queues (Celery, RQ)
- Load balancing strategies (round-robin, least-busy, weighted, adaptive)
- Distributed state management (Redis, in-memory)
- Worker pool and management
- Advanced caching with multiple backends
- Frame deduplication and similarity detection
- Cost optimization and efficiency tracking
"""

from src.distributed.task_queue import (
    TaskStatus,
    TaskResult,
    TaskQueue,
    InMemoryQueue,
    CeleryQueue,
    RQQueue,
    TaskQueueFactory,
    init_task_queue,
    get_task_queue,
)

from src.distributed.load_balancer import (
    LoadBalancingStrategy,
    WorkerStats,
    LoadBalancer,
    RoundRobinBalancer,
    LeastBusyBalancer,
    WeightedBalancer,
    AdaptiveBalancer,
    LoadBalancerFactory,
    init_load_balancer,
    get_load_balancer,
)

from src.distributed.state_manager import (
    StateEntry,
    StateManager,
    InMemoryStateManager,
    RedisStateManager,
    DistributedSessionState,
    StateManagerFactory,
    init_state_manager,
    get_state_manager,
    get_session_state,
)

from src.distributed.worker import (
    WorkerStatus,
    WorkerConfig,
    Worker,
    WorkerPool,
    WorkerManager,
    init_worker_manager,
    get_worker_manager,
)

from src.distributed.cache import (
    CacheBackendType,
    EvictionPolicy,
    CacheEntry,
    CacheStats,
    CacheBackend,
    InMemoryCache,
    RedisCache,
    FilesystemCache,
    CacheManager,
    init_cache,
    get_cache,
)

from src.distributed.deduplication import (
    SimilarityMetric,
    DuplicateFrame,
    FrameDeduplicator,
    DeduplicationManager,
    init_deduplication,
    get_dedup_manager,
)

from src.distributed.cost_optimizer import (
    CostMetric,
    CostEstimate,
    ProcessingMetric,
    CostModel,
    OptimizationStrategy,
    CostOptimizer,
    init_cost_optimizer,
    get_cost_optimizer,
)

__all__ = [
    # Task queue
    "TaskStatus",
    "TaskResult",
    "TaskQueue",
    "InMemoryQueue",
    "CeleryQueue",
    "RQQueue",
    "TaskQueueFactory",
    "init_task_queue",
    "get_task_queue",
    # Load balancer
    "LoadBalancingStrategy",
    "WorkerStats",
    "LoadBalancer",
    "RoundRobinBalancer",
    "LeastBusyBalancer",
    "WeightedBalancer",
    "AdaptiveBalancer",
    "LoadBalancerFactory",
    "init_load_balancer",
    "get_load_balancer",
    # State manager
    "StateEntry",
    "StateManager",
    "InMemoryStateManager",
    "RedisStateManager",
    "DistributedSessionState",
    "StateManagerFactory",
    "init_state_manager",
    "get_state_manager",
    "get_session_state",
    # Worker
    "WorkerStatus",
    "WorkerConfig",
    "Worker",
    "WorkerPool",
    "WorkerManager",
    "init_worker_manager",
    "get_worker_manager",
    # Cache
    "CacheBackendType",
    "EvictionPolicy",
    "CacheEntry",
    "CacheStats",
    "CacheBackend",
    "InMemoryCache",
    "RedisCache",
    "FilesystemCache",
    "CacheManager",
    "init_cache",
    "get_cache",
    # Deduplication
    "SimilarityMetric",
    "DuplicateFrame",
    "FrameDeduplicator",
    "DeduplicationManager",
    "init_deduplication",
    "get_dedup_manager",
    # Cost optimizer
    "CostMetric",
    "CostEstimate",
    "ProcessingMetric",
    "CostModel",
    "OptimizationStrategy",
    "CostOptimizer",
    "init_cost_optimizer",
    "get_cost_optimizer",
]
