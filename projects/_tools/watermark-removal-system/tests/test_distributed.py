"""
Tests for distributed processing subsystem.

Covers task queues, load balancing, state management, and worker pools.
"""

import pytest
import asyncio
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock

# Task queue tests
from src.distributed.task_queue import (
    TaskStatus,
    TaskResult,
    InMemoryQueue,
    TaskQueueFactory,
    init_task_queue,
    get_task_queue,
)

# Load balancer tests
from src.distributed.load_balancer import (
    LoadBalancingStrategy,
    WorkerStats,
    RoundRobinBalancer,
    LeastBusyBalancer,
    WeightedBalancer,
    AdaptiveBalancer,
    LoadBalancerFactory,
)

# State manager tests
from src.distributed.state_manager import (
    StateEntry,
    InMemoryStateManager,
    DistributedSessionState,
    StateManagerFactory,
)

# Worker tests
from src.distributed.worker import (
    WorkerStatus,
    WorkerConfig,
    Worker,
    WorkerPool,
    WorkerManager,
)


# ============================================================================
# TASK QUEUE TESTS
# ============================================================================


class TestInMemoryQueue:
    """Test in-memory task queue."""

    def test_init(self):
        """Test queue initialization."""
        queue = InMemoryQueue()
        assert len(queue.tasks) == 0
        assert len(queue.results) == 0
        assert len(queue.pending) == 0

    def test_enqueue(self):
        """Test enqueueing task."""
        queue = InMemoryQueue()
        task_id = queue.enqueue("process_frame", frame_data={"width": 640})
        assert task_id is not None
        assert task_id in queue.tasks
        assert task_id in queue.pending

    def test_get_result_pending(self):
        """Test getting result of pending task."""
        queue = InMemoryQueue()
        task_id = queue.enqueue("process_frame")
        result = queue.get_result(task_id)
        assert result is not None
        assert result.status == TaskStatus.PENDING

    def test_get_result_completed(self):
        """Test getting result of completed task."""
        queue = InMemoryQueue()
        task_id = queue.enqueue("process_frame")
        queue.simulate_task_execution(task_id, result={"frames": 10})
        result = queue.get_result(task_id)
        assert result.status == TaskStatus.COMPLETED
        assert result.result == {"frames": 10}

    def test_get_result_failed(self):
        """Test getting result of failed task."""
        queue = InMemoryQueue()
        task_id = queue.enqueue("process_frame")
        queue.simulate_task_execution(task_id, error="Frame decode error")
        result = queue.get_result(task_id)
        assert result.status == TaskStatus.FAILED
        assert "decode error" in result.error

    def test_cancel_task(self):
        """Test canceling pending task."""
        queue = InMemoryQueue()
        task_id = queue.enqueue("process_frame")
        assert queue.cancel_task(task_id) is True
        assert task_id not in queue.pending

    def test_cancel_non_existent(self):
        """Test canceling non-existent task."""
        queue = InMemoryQueue()
        assert queue.cancel_task("fake-id") is False

    def test_get_queue_stats(self):
        """Test getting queue statistics."""
        queue = InMemoryQueue()
        queue.enqueue("task1")
        queue.enqueue("task2")
        task_id = queue.enqueue("task3")
        queue.simulate_task_execution(task_id)

        stats = queue.get_queue_stats()
        assert stats["pending"] == 2
        assert stats["completed"] == 1
        assert stats["total_tasks"] == 3

    def test_multiple_enqueued_tasks(self):
        """Test enqueueing multiple tasks."""
        queue = InMemoryQueue()
        for i in range(5):
            queue.enqueue(f"task_{i}")

        assert len(queue.pending) == 5
        assert len(queue.tasks) == 5


class TestTaskQueueFactory:
    """Test task queue factory."""

    def test_create_memory_queue(self):
        """Test creating memory queue."""
        queue = TaskQueueFactory.create(queue_type="memory")
        assert isinstance(queue, InMemoryQueue)

    def test_create_auto_fallback(self):
        """Test auto mode falls back to memory."""
        queue = TaskQueueFactory.create(queue_type="auto")
        assert queue is not None  # Should return something

    def test_init_and_get_global(self):
        """Test global queue initialization."""
        init_task_queue("memory")
        queue = get_task_queue()
        assert queue is not None


# ============================================================================
# LOAD BALANCER TESTS
# ============================================================================


class TestRoundRobinBalancer:
    """Test round-robin load balancer."""

    def test_init(self):
        """Test balancer initialization."""
        workers = ["worker-1", "worker-2", "worker-3"]
        balancer = RoundRobinBalancer(workers)
        assert len(balancer.workers) == 3

    def test_round_robin_selection(self):
        """Test round-robin worker selection."""
        workers = ["worker-1", "worker-2", "worker-3"]
        balancer = RoundRobinBalancer(workers)

        selected = [balancer.select_worker() for _ in range(6)]
        assert selected == ["worker-1", "worker-2", "worker-3", "worker-1", "worker-2", "worker-3"]

    def test_add_remove_workers(self):
        """Test adding and removing workers."""
        balancer = RoundRobinBalancer(["worker-1"])
        balancer.remove_worker("worker-1")
        assert balancer.select_worker() is None

    def test_load_distribution(self):
        """Test load distribution is equal."""
        workers = ["worker-1", "worker-2", "worker-3"]
        balancer = RoundRobinBalancer(workers)
        dist = balancer.get_load_distribution()
        assert all(d == 1.0 / 3 for d in dist.values())


class TestLeastBusyBalancer:
    """Test least-busy load balancer."""

    def test_select_least_busy(self):
        """Test selecting least busy worker."""
        workers = ["worker-1", "worker-2", "worker-3"]
        balancer = LeastBusyBalancer(workers)

        # Update loads
        balancer.update_worker_stats("worker-1", WorkerStats("worker-1", current_load=5.0))
        balancer.update_worker_stats("worker-2", WorkerStats("worker-2", current_load=1.0))
        balancer.update_worker_stats("worker-3", WorkerStats("worker-3", current_load=3.0))

        selected = balancer.select_worker()
        assert selected == "worker-2"

    def test_dynamic_rebalancing(self):
        """Test rebalancing as loads change."""
        balancer = LeastBusyBalancer(["worker-1", "worker-2"])
        balancer.update_worker_stats("worker-1", WorkerStats("worker-1", current_load=10.0))
        balancer.update_worker_stats("worker-2", WorkerStats("worker-2", current_load=1.0))

        first = balancer.select_worker()
        assert first == "worker-2"

        # Swap loads
        balancer.update_worker_stats("worker-1", WorkerStats("worker-1", current_load=1.0))
        balancer.update_worker_stats("worker-2", WorkerStats("worker-2", current_load=10.0))

        second = balancer.select_worker()
        assert second == "worker-1"


class TestWeightedBalancer:
    """Test weighted load balancer."""

    def test_weighted_selection(self):
        """Test weighted worker selection."""
        workers = ["fast", "slow"]
        weights = {"fast": 2.0, "slow": 1.0}  # Fast worker gets 2x weight
        balancer = WeightedBalancer(workers, weights)

        # All workers idle, should select based on weights
        selected = [balancer.select_worker() for _ in range(3)]
        fast_count = sum(1 for w in selected if w == "fast")
        slow_count = sum(1 for w in selected if w == "slow")
        assert fast_count >= slow_count

    def test_capacity_aware(self):
        """Test capacity-aware selection."""
        balancer = WeightedBalancer(["worker-1", "worker-2"])

        # Worker-1 at capacity
        stats1 = WorkerStats("worker-1", task_count=10, capacity=10)
        stats2 = WorkerStats("worker-2", task_count=0, capacity=10)

        balancer.update_worker_stats("worker-1", stats1)
        balancer.update_worker_stats("worker-2", stats2)

        selected = balancer.select_worker()
        assert selected == "worker-2"


class TestAdaptiveBalancer:
    """Test adaptive load balancer."""

    def test_initial_strategy(self):
        """Test initial strategy."""
        balancer = AdaptiveBalancer(
            ["worker-1", "worker-2"],
            initial_strategy=LoadBalancingStrategy.LEAST_BUSY,
        )
        assert balancer.current_strategy == LoadBalancingStrategy.LEAST_BUSY

    def test_strategy_adaptation(self):
        """Test strategy adaptation based on variance."""
        balancer = AdaptiveBalancer(["w1", "w2", "w3", "w4"])

        # Create high variance (unbalanced)
        balancer.update_worker_stats("w1", WorkerStats("w1", current_load=10.0))
        balancer.update_worker_stats("w2", WorkerStats("w2", current_load=1.0))
        balancer.update_worker_stats("w3", WorkerStats("w3", current_load=9.0))
        balancer.update_worker_stats("w4", WorkerStats("w4", current_load=0.5))

        # Should adapt to LEAST_BUSY due to high variance
        assert balancer.current_strategy == LoadBalancingStrategy.LEAST_BUSY


# ============================================================================
# STATE MANAGER TESTS
# ============================================================================


class TestInMemoryStateManager:
    """Test in-memory state manager."""

    def test_set_get(self):
        """Test setting and getting state."""
        manager = InMemoryStateManager()
        manager.set("key1", {"data": "value"})
        value = manager.get("key1")
        assert value == {"data": "value"}

    def test_delete(self):
        """Test deleting state."""
        manager = InMemoryStateManager()
        manager.set("key1", "value")
        assert manager.delete("key1") is True
        assert manager.get("key1") is None

    def test_exists(self):
        """Test checking key existence."""
        manager = InMemoryStateManager()
        manager.set("key1", "value")
        assert manager.exists("key1") is True
        assert manager.exists("nonexistent") is False

    def test_increment(self):
        """Test incrementing numeric value."""
        manager = InMemoryStateManager()
        manager.set("counter", 0)
        result = manager.increment("counter", 5)
        assert result == 5
        assert manager.get("counter") == 5

    def test_ttl_expiration(self):
        """Test TTL-based expiration."""
        manager = InMemoryStateManager()
        manager.set("key1", "value", ttl_seconds=0.1)
        assert manager.get("key1") == "value"
        time.sleep(0.2)
        assert manager.get("key1") is None

    def test_get_all(self):
        """Test getting all entries."""
        manager = InMemoryStateManager()
        manager.set("user:1", {"name": "Alice"})
        manager.set("user:2", {"name": "Bob"})
        manager.set("config", {"setting": "value"})

        all_users = manager.get_all("user:*")
        assert len(all_users) == 2

    def test_no_ttl(self):
        """Test entries without TTL."""
        manager = InMemoryStateManager()
        manager.set("permanent", "data")
        time.sleep(0.1)
        assert manager.get("permanent") == "data"


class TestDistributedSessionState:
    """Test distributed session state."""

    def test_create_get_session(self):
        """Test creating and getting session."""
        manager = InMemoryStateManager()
        session_state = DistributedSessionState(manager)

        session_data = {"user_id": "123", "frames": 100}
        session_state.create_session("sess-1", session_data)

        retrieved = session_state.get_session("sess-1")
        assert retrieved == session_data

    def test_update_session(self):
        """Test updating session."""
        manager = InMemoryStateManager()
        session_state = DistributedSessionState(manager)

        session_state.create_session("sess-1", {"frames": 0})
        session_state.update_session("sess-1", {"frames": 100})

        retrieved = session_state.get_session("sess-1")
        assert retrieved["frames"] == 100

    def test_register_get_workers(self):
        """Test registering and retrieving workers."""
        manager = InMemoryStateManager()
        session_state = DistributedSessionState(manager)

        worker_info = {"cpu": 0.5, "memory": 512}
        session_state.register_worker("worker-1", worker_info)

        workers = session_state.get_workers()
        assert len(workers) > 0

    def test_task_progress(self):
        """Test tracking task progress."""
        manager = InMemoryStateManager()
        session_state = DistributedSessionState(manager)

        session_state.update_task_progress("task-1", 0.5, "running")
        progress = session_state.get_task_progress("task-1")

        assert progress["progress"] == 0.5
        assert progress["status"] == "running"


# ============================================================================
# WORKER TESTS
# ============================================================================


class TestWorker:
    """Test worker."""

    def test_init(self):
        """Test worker initialization."""
        config = WorkerConfig(worker_id="worker-1")
        worker = Worker(config)
        assert worker.status == WorkerStatus.IDLE
        assert worker.completed_count == 0

    @pytest.mark.asyncio
    async def test_process_task(self):
        """Test processing task."""
        config = WorkerConfig(worker_id="worker-1")
        worker = Worker(config)

        # Register handler
        async def dummy_handler(data):
            return {"result": "ok"}

        worker.register_task_handler("process", dummy_handler)

        # Process task
        result = await worker.process_task("task-1", "process", {})
        assert result == {"result": "ok"}
        assert worker.completed_count == 1

    @pytest.mark.asyncio
    async def test_task_timeout(self):
        """Test task timeout."""
        config = WorkerConfig(worker_id="worker-1", task_timeout_seconds=0.1)
        worker = Worker(config)

        # Register handler that takes too long
        async def slow_handler(data):
            await asyncio.sleep(1.0)
            return {"result": "ok"}

        worker.register_task_handler("slow", slow_handler)

        result = await worker.process_task("task-1", "slow", {})
        assert result is None
        assert worker.failed_count == 1

    @pytest.mark.asyncio
    async def test_concurrent_task_limit(self):
        """Test concurrent task limit."""
        config = WorkerConfig(worker_id="worker-1", max_concurrent_tasks=1)
        worker = Worker(config)

        async def fast_handler(data):
            await asyncio.sleep(0.01)
            return {"ok": True}

        worker.register_task_handler("task", fast_handler)

        # First task
        task1 = asyncio.create_task(worker.process_task("t1", "task", {}))
        await asyncio.sleep(0.001)  # Let task1 start

        # Second task should be rejected (at capacity)
        result2 = await worker.process_task("t2", "task", {})
        assert result2 is None

        await task1  # Wait for first task


class TestWorkerPool:
    """Test worker pool."""

    def test_init(self):
        """Test pool initialization."""
        pool = WorkerPool(size=4)
        assert len(pool.workers) == 4

    def test_register_handler(self):
        """Test registering handlers."""
        pool = WorkerPool(size=2)

        async def handler(data):
            return {"ok": True}

        pool.register_task_handler("process", handler)
        for worker in pool.workers.values():
            assert "process" in worker.task_handlers

    @pytest.mark.asyncio
    async def test_distribute_tasks(self):
        """Test task distribution across pool."""
        pool = WorkerPool(size=2)

        async def handler(data):
            return {"processed": True}

        pool.register_task_handler("task", handler)

        # Process multiple tasks
        results = []
        for i in range(4):
            result = await pool.process_task(f"task-{i}", "task", {})
            results.append(result)

        # All should succeed (2 workers, concurrent tasks allowed)
        assert all(r is not None for r in results)

    def test_get_pool_stats(self):
        """Test pool statistics."""
        pool = WorkerPool(size=2)
        stats = pool.get_pool_stats()

        assert "pool_size" in stats
        assert stats["pool_size"] == 2
        assert "total_completed" in stats
        assert "worker_utilization" in stats


class TestWorkerManager:
    """Test worker manager."""

    def test_init(self):
        """Test manager initialization."""
        manager = WorkerManager(pool_size=2)
        assert manager.pool.size == 2

    @pytest.mark.asyncio
    async def test_submit_task(self):
        """Test submitting task."""
        manager = WorkerManager(pool_size=1)

        async def handler(data):
            return {"done": True}

        manager.register_task_type("process", handler)
        task_id = await manager.submit_task("process", {})

        assert task_id is not None
        assert manager.get_task_status(task_id) in ["completed", "failed", "queued"]

    def test_get_manager_stats(self):
        """Test manager statistics."""
        manager = WorkerManager(pool_size=2)
        stats = manager.get_manager_stats()

        assert "pool_stats" in stats
        assert "total_submitted" in stats
        assert "completed" in stats
        assert "failed" in stats


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestDistributedIntegration:
    """Integration tests for distributed system."""

    def test_task_queue_with_state(self):
        """Test task queue integration with state manager."""
        queue = InMemoryQueue()
        state = InMemoryStateManager()

        # Enqueue task
        task_id = queue.enqueue("process_frame", frame_id=1)

        # Store task in state
        state.set(f"task:{task_id}", {"frame_id": 1, "status": "pending"})

        # Retrieve from both
        task = queue.get_result(task_id)
        task_state = state.get(f"task:{task_id}")

        assert task is not None
        assert task_state["frame_id"] == 1

    @pytest.mark.asyncio
    async def test_worker_with_load_balancer(self):
        """Test worker pool with load balancing."""
        pool = WorkerPool(size=3)
        balancer = LeastBusyBalancer([w for w in pool.workers.keys()])

        async def handler(data):
            await asyncio.sleep(0.01)
            return {"processed": True}

        pool.register_task_handler("task", handler)

        # Select worker using balancer
        selected = balancer.select_worker()
        assert selected in pool.workers

    def test_state_with_session_management(self):
        """Test state manager with session tracking."""
        state = InMemoryStateManager()
        session_mgr = DistributedSessionState(state)

        # Create session
        session_mgr.create_session("sess-1", {"user": "alice"})

        # Register workers for session
        session_mgr.register_worker("worker-1", {"status": "idle"})
        session_mgr.register_worker("worker-2", {"status": "idle"})

        # Get active workers
        workers = session_mgr.get_workers()
        assert len(workers) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
