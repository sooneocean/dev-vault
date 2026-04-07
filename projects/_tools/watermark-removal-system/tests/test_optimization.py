"""
Tests for performance optimization subsystem.

Covers model optimization, pipeline parallelism, GPU optimization, and profiling.
"""

import pytest
import asyncio
from src.optimization import (
    # Model optimizer
    QuantizationType,
    PruningStrategy,
    QuantizationConfig,
    PruningConfig,
    ModelQuantizer,
    ModelPruner,
    KnowledgeDistiller,
    ModelOptimizer,
    get_model_optimizer,
    # Pipeline
    StageStatus,
    Pipeline,
    PipelineOrchestrator,
    get_orchestrator,
    # GPU optimizer
    GPUMemoryPool,
    GPUMemoryManager,
    CUDAKernelOptimizer,
    ComputeIOOverlapManager,
    GPUOptimizer,
    get_gpu_optimizer,
    # Profiler
    ProfileScope,
    ExecutionProfiler,
    MemoryProfiler,
    BottleneckAnalyzer,
    get_execution_profiler,
    get_bottleneck_analyzer,
)


# ============================================================================
# Model Quantizer Tests
# ============================================================================

class TestModelQuantizer:
    def test_quantizer_initialization(self):
        quantizer = ModelQuantizer()
        assert quantizer.config.quantization_type == QuantizationType.FP32
        assert quantizer.config.activation_bits == 8
        assert quantizer.config.weight_bits == 8

    def test_compute_quantization_stats(self):
        quantizer = ModelQuantizer()
        activations = [1.0, 2.0, 3.0, 4.0, 5.0]
        stats = quantizer.compute_quantization_stats(activations)

        assert stats["mean"] == 3.0
        assert stats["min"] == 1.0
        assert stats["max"] == 5.0
        assert stats["range"] == 4.0

    def test_quantize_weights_fp32(self):
        quantizer = ModelQuantizer()
        weights = [1.0, 2.0, 3.0, 4.0, 5.0]
        quantized, stats = quantizer.quantize_weights(weights)

        assert len(quantized) == len(weights)
        # For FP32, scale/zero_point not added, but stats should contain mean/std
        assert "mean" in stats
        assert "std" in stats

    def test_quantize_weights_int8(self):
        config = QuantizationConfig(quantization_type=QuantizationType.INT8)
        quantizer = ModelQuantizer(config)
        weights = [1.0, 2.0, 3.0, 4.0, 5.0]
        quantized, stats = quantizer.quantize_weights(weights)

        # INT8 quantized values should be in [-128, 127]
        assert all(-128 <= q <= 127 for q in quantized)

    def test_estimate_memory_savings(self):
        quantizer = ModelQuantizer()
        savings = quantizer.estimate_memory_savings(original_bits=32, quantized_bits=8)

        assert savings == 0.75  # 75% savings
        assert savings > 0


# ============================================================================
# Model Pruner Tests
# ============================================================================

class TestModelPruner:
    def test_pruner_initialization(self):
        pruner = ModelPruner()
        assert pruner.config.strategy == PruningStrategy.MAGNITUDE
        assert pruner.config.target_sparsity == 0.5

    def test_compute_magnitude_scores(self):
        pruner = ModelPruner()
        weights = [1.0, -2.0, 3.0, -4.0, 5.0]
        scores = pruner.compute_magnitude_scores(weights)

        assert scores == [1.0, 2.0, 3.0, 4.0, 5.0]

    def test_select_pruning_candidates(self):
        pruner = ModelPruner()
        scores = [5.0, 2.0, 8.0, 1.0, 3.0]
        candidates = pruner.select_pruning_candidates(scores)

        # Should prune 50% (2 out of 4 after 0.5 target)
        assert len(candidates) == 2
        assert 3 in candidates  # Index with score 1.0 (smallest)

    def test_prune_weights(self):
        pruner = ModelPruner()
        weights = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]  # 10 weights for even 50%
        pruned, stats = pruner.prune_weights(weights)

        assert len(pruned) == len(weights)
        assert sum(1 for w in pruned if w == 0.0) > 0  # Some pruned
        assert stats["sparsity"] == 0.5  # 50% with 10 weights


# ============================================================================
# Knowledge Distiller Tests
# ============================================================================

class TestKnowledgeDistiller:
    def test_distiller_initialization(self):
        distiller = KnowledgeDistiller()
        assert distiller.config.temperature == 3.0
        assert distiller.config.alpha == 0.5

    def test_compute_soft_targets(self):
        distiller = KnowledgeDistiller()
        logits = [1.0, 2.0, 3.0]
        soft_targets = distiller.compute_soft_targets(logits, temperature=1.0)

        assert len(soft_targets) == len(logits)
        assert all(0 <= t <= 1 for t in soft_targets)
        assert abs(sum(soft_targets) - 1.0) < 0.01  # Sum to approximately 1

    def test_compute_distillation_loss(self):
        distiller = KnowledgeDistiller()
        student_logits = [1.0, 2.0, 3.0]
        teacher_logits = [1.5, 2.5, 3.5]
        hard_targets = [0, 0, 1]

        loss = distiller.compute_distillation_loss(
            student_logits, teacher_logits, hard_targets
        )

        assert loss >= 0


# ============================================================================
# Model Optimizer Tests
# ============================================================================

class TestModelOptimizer:
    def test_optimizer_initialization(self):
        optimizer = ModelOptimizer()
        assert optimizer.quantizer is not None
        assert optimizer.pruner is not None
        assert optimizer.distiller is not None

    def test_optimize_model_with_quantization(self):
        optimizer = ModelOptimizer()
        config = QuantizationConfig(quantization_type=QuantizationType.INT8)

        result = optimizer.optimize_model(model_size_mb=100.0, quantization_config=config)

        assert result.original_size_mb == 100.0
        assert result.optimized_size_mb < 100.0
        assert result.compression_ratio > 1.0
        assert result.latency_improvement > 0

    def test_optimize_model_with_pruning(self):
        optimizer = ModelOptimizer()
        config = PruningConfig(target_sparsity=0.3)

        result = optimizer.optimize_model(model_size_mb=100.0, pruning_config=config)

        assert result.original_size_mb == 100.0
        assert result.optimized_size_mb < 100.0
        assert result.memory_improvement > 0

    def test_optimize_model_both(self):
        optimizer = ModelOptimizer()
        quant_config = QuantizationConfig(quantization_type=QuantizationType.FP16)
        prune_config = PruningConfig(target_sparsity=0.2)

        result = optimizer.optimize_model(
            model_size_mb=100.0,
            quantization_config=quant_config,
            pruning_config=prune_config,
        )

        assert result.optimized_size_mb < 100.0
        assert result.compression_ratio > 1.0

    def test_get_optimization_summary(self):
        optimizer = ModelOptimizer()
        optimizer.optimize_model(100.0, QuantizationConfig(QuantizationType.INT8))

        summary = optimizer.get_optimization_summary()
        assert summary["total_optimizations"] == 1
        assert summary["avg_compression_ratio"] > 1


# ============================================================================
# Pipeline Tests
# ============================================================================

class TestPipelineStage:
    @pytest.mark.asyncio
    async def test_stage_initialization(self):
        async def dummy_process(data):
            return data * 2

        stage = Pipeline.add_stage(Pipeline("test"), "double", dummy_process)
        assert stage.name == "double"
        assert stage.input_queue is not None

    @pytest.mark.asyncio
    async def test_stage_process_item(self):
        from src.optimization import PipelineTask

        async def double(data):
            return data * 2

        pipeline = Pipeline("test")
        stage = pipeline.add_stage("double", double)

        task = PipelineTask(task_id="test1", input_data=5)
        processed = await stage.process_item(task)

        assert processed.output_data == 10
        assert processed.completed_at is not None


class TestPipeline:
    @pytest.mark.asyncio
    async def test_pipeline_initialization(self):
        pipeline = Pipeline("test_pipeline")
        assert pipeline.name == "test_pipeline"
        assert len(pipeline.stages) == 0

    @pytest.mark.asyncio
    async def test_add_stage(self):
        pipeline = Pipeline("test")

        async def process(data):
            return data

        pipeline.add_stage("stage1", process)
        assert len(pipeline.stages) == 1

    @pytest.mark.asyncio
    async def test_submit_task(self):
        pipeline = Pipeline("test")

        def identity(x):
            return x

        pipeline.add_stage("identity", identity)
        task_id = await pipeline.submit_task("task1", 42)

        assert task_id == "task1"
        assert "task1" in pipeline.tasks

    @pytest.mark.asyncio
    async def test_get_metrics(self):
        pipeline = Pipeline("test")

        def add_one(x):
            return x + 1

        pipeline.add_stage("add_one", add_one)
        await pipeline.start()
        await pipeline.submit_task("task1", 1)

        # Let it process
        await asyncio.sleep(0.1)
        await pipeline.shutdown()

        metrics = pipeline.get_metrics()
        assert "add_one" in metrics


class TestPipelineOrchestrator:
    def test_orchestrator_initialization(self):
        orchestrator = PipelineOrchestrator()
        assert len(orchestrator.pipelines) == 0

    def test_create_pipeline(self):
        orchestrator = PipelineOrchestrator()
        pipeline = orchestrator.create_pipeline("test_pipeline")

        assert pipeline is not None
        assert orchestrator.get_pipeline("test_pipeline") is not None

    @pytest.mark.asyncio
    async def test_start_all(self):
        orchestrator = PipelineOrchestrator()
        p1 = orchestrator.create_pipeline("p1")
        p2 = orchestrator.create_pipeline("p2")

        def dummy(x):
            return x

        p1.add_stage("stage", dummy)
        p2.add_stage("stage", dummy)

        await orchestrator.start_all()

        # Verify pipelines are running
        assert p1.is_running
        assert p2.is_running

        await orchestrator.shutdown_all()


# ============================================================================
# GPU Memory Manager Tests
# ============================================================================

class TestGPUMemoryManager:
    def test_initialization(self):
        manager = GPUMemoryManager(total_memory_mb=2048.0)
        assert manager.total_memory_mb == 2048.0
        assert manager.allocated_mb == 0.0

    def test_allocate(self):
        manager = GPUMemoryManager(total_memory_mb=100.0)
        success, alloc_id = manager.allocate(50.0)

        assert success
        assert manager.allocated_mb == 50.0

    def test_allocate_exceeds_limit(self):
        manager = GPUMemoryManager(total_memory_mb=100.0)
        success, _ = manager.allocate(150.0)

        assert not success

    def test_deallocate(self):
        manager = GPUMemoryManager(total_memory_mb=100.0)
        _, alloc_id = manager.allocate(50.0)
        success = manager.deallocate(alloc_id)

        assert success
        assert manager.allocated_mb == 0.0

    def test_get_stats(self):
        manager = GPUMemoryManager(total_memory_mb=100.0)
        manager.allocate(40.0)

        stats = manager.get_stats()
        assert stats.total_memory_mb == 100.0
        assert stats.allocated_mb == 40.0
        assert stats.free_mb == 60.0
        assert stats.utilization_percent == 40.0


# ============================================================================
# CUDA Kernel Optimizer Tests
# ============================================================================

class TestCUDAKernelOptimizer:
    def test_initialization(self):
        optimizer = CUDAKernelOptimizer()
        assert len(optimizer.kernel_profiles) == 0

    def test_profile_kernel(self):
        optimizer = CUDAKernelOptimizer()
        optimizer.profile_kernel("matmul", 100.0)

        assert "matmul" in optimizer.kernel_profiles
        profile = optimizer.kernel_profiles["matmul"]
        assert profile.launch_count == 1
        assert profile.avg_time_ms == 100.0

    def test_get_bottleneck_kernels(self):
        optimizer = CUDAKernelOptimizer()
        optimizer.profile_kernel("kernel1", 50.0)
        optimizer.profile_kernel("kernel2", 150.0)
        optimizer.profile_kernel("kernel3", 100.0)

        bottlenecks = optimizer.get_bottleneck_kernels()
        assert bottlenecks[0][0] == "kernel2"  # Highest time


# ============================================================================
# Compute/IO Overlap Manager Tests
# ============================================================================

class TestComputeIOOverlapManager:
    def test_initialization(self):
        manager = ComputeIOOverlapManager(num_streams=4)
        assert len(manager.stream_workload) == 4

    def test_schedule_compute_io(self):
        manager = ComputeIOOverlapManager(num_streams=2)
        total_time, seq_time, efficiency = manager.schedule_compute_io(
            compute_time_ms=100.0, io_time_ms=50.0
        )

        assert seq_time == 150.0
        assert total_time <= seq_time  # Overlap achieved
        assert efficiency > 1.0  # Overlap ratio

    def test_get_utilization(self):
        manager = ComputeIOOverlapManager(num_streams=2)
        manager.schedule_compute_io(100.0, 100.0)

        util = manager.get_utilization()
        assert all(0 <= v <= 100 for v in util.values())


# ============================================================================
# GPU Optimizer Tests
# ============================================================================

class TestGPUOptimizer:
    def test_initialization(self):
        optimizer = GPUOptimizer()
        assert optimizer.memory_manager is not None
        assert optimizer.kernel_optimizer is not None

    def test_analyze_performance(self):
        optimizer = GPUOptimizer()
        report = optimizer.analyze_performance()

        assert "memory" in report
        assert "kernels" in report
        assert "io_overlap" in report

    def test_get_optimization_recommendations(self):
        optimizer = GPUOptimizer()
        # Allocate most of memory
        optimizer.memory_manager.allocate(1900.0)

        recommendations = optimizer.get_optimization_recommendations()
        # Should have memory optimization recommendation
        assert any(r["category"] == "MEMORY" for r in recommendations)


# ============================================================================
# Execution Profiler Tests
# ============================================================================

class TestExecutionProfiler:
    def test_initialization(self):
        profiler = ExecutionProfiler()
        assert len(profiler.stats) == 0

    def test_profile_block(self):
        profiler = ExecutionProfiler()

        with profiler.profile_block("test_block"):
            pass

        assert "test_block" in profiler.stats
        assert profiler.stats["test_block"].call_count == 1

    def test_profile_function_decorator(self):
        profiler = ExecutionProfiler()

        @profiler.profile_function
        def add(a, b):
            return a + b

        result = add(1, 2)
        assert result == 3
        assert "add" in profiler.stats

    def test_get_slowest_functions(self):
        profiler = ExecutionProfiler()

        with profiler.profile_block("slow"):
            pass

        with profiler.profile_block("fast"):
            pass

        slowest = profiler.get_slowest_functions()
        assert len(slowest) >= 1

    def test_get_report(self):
        profiler = ExecutionProfiler()

        with profiler.profile_block("test"):
            pass

        report = profiler.get_report()
        assert "total_calls" in report
        assert "total_time_ms" in report


# ============================================================================
# Memory Profiler Tests
# ============================================================================

class TestMemoryProfiler:
    def test_initialization(self):
        profiler = MemoryProfiler()
        assert profiler.peak_memory_mb == 0.0

    def test_record_allocation(self):
        profiler = MemoryProfiler()
        profiler.record_allocation("array1", 100.0)

        assert profiler.total_allocated_mb == 100.0
        assert profiler.peak_memory_mb == 100.0

    def test_get_allocation_stats(self):
        profiler = MemoryProfiler()
        profiler.record_allocation("array1", 50.0)
        profiler.record_allocation("array1", 60.0)

        stats = profiler.get_allocation_stats("array1")
        assert stats["count"] == 2
        assert stats["total_mb"] == 110.0

    def test_get_top_allocators(self):
        profiler = MemoryProfiler()
        profiler.record_allocation("a", 100.0)
        profiler.record_allocation("b", 200.0)
        profiler.record_allocation("c", 50.0)

        top = profiler.get_top_allocators(2)
        assert top[0][0] == "b"  # Highest allocation


# ============================================================================
# Bottleneck Analyzer Tests
# ============================================================================

class TestBottleneckAnalyzer:
    def test_initialization(self):
        analyzer = BottleneckAnalyzer()
        assert analyzer.execution_profiler is not None
        assert analyzer.memory_profiler is not None

    def test_analyze_execution_profile(self):
        analyzer = BottleneckAnalyzer()

        with analyzer.execution_profiler.profile_block("expensive"):
            pass

        bottlenecks = analyzer.analyze_execution_profile()
        assert isinstance(bottlenecks, list)

    def test_analyze_memory_profile(self):
        analyzer = BottleneckAnalyzer()
        analyzer.memory_profiler.record_allocation("huge_array", 500.0)

        bottlenecks = analyzer.analyze_memory_profile()
        assert any(b["type"] == "MEMORY_BOTTLENECK" for b in bottlenecks)

    def test_get_optimization_plan(self):
        analyzer = BottleneckAnalyzer()

        with analyzer.execution_profiler.profile_block("slow"):
            pass

        plan = analyzer.get_optimization_plan()
        assert "summary" in plan
        assert "bottlenecks" in plan


# ============================================================================
# Global Instance Tests
# ============================================================================

class TestGlobalInstances:
    def test_get_model_optimizer(self):
        optimizer = get_model_optimizer()
        assert optimizer is not None

    def test_get_orchestrator(self):
        orchestrator = get_orchestrator()
        assert orchestrator is not None

    def test_get_gpu_optimizer(self):
        optimizer = get_gpu_optimizer()
        assert optimizer is not None

    def test_get_execution_profiler(self):
        profiler = get_execution_profiler()
        assert profiler is not None

    def test_get_bottleneck_analyzer(self):
        analyzer = get_bottleneck_analyzer()
        assert analyzer is not None


# ============================================================================
# Integration Tests
# ============================================================================

class TestOptimizationIntegration:
    def test_end_to_end_model_optimization(self):
        """Test complete model optimization workflow."""
        optimizer = get_model_optimizer()
        original_size = 500.0

        # Apply quantization
        quant_config = QuantizationConfig(quantization_type=QuantizationType.INT8)
        result = optimizer.optimize_model(original_size, quantization_config=quant_config)

        assert result.original_size_mb == original_size
        assert result.optimized_size_mb < original_size
        assert result.compression_ratio > 1.0

    @pytest.mark.asyncio
    async def test_pipeline_with_profiler(self):
        """Test pipeline execution with profiling."""
        pipeline = Pipeline("profiled_pipeline")
        profiler = get_execution_profiler()

        def add_one(x):
            return x + 1

        pipeline.add_stage("add_one", add_one)

        # Profile the execution
        with profiler.profile_block("pipeline_test"):
            await pipeline.start()
            await pipeline.submit_task("task1", 10)
            await asyncio.sleep(0.05)
            await pipeline.shutdown()

        assert "pipeline_test" in profiler.stats

    def test_gpu_memory_and_kernel_optimization(self):
        """Test GPU memory and kernel optimization together."""
        gpu_opt = get_gpu_optimizer()

        # Allocate memory
        success, alloc_id = gpu_opt.memory_manager.allocate(512.0)
        assert success

        # Profile kernel
        gpu_opt.kernel_optimizer.profile_kernel("test_kernel", 50.0)
        gpu_opt.kernel_optimizer.profile_kernel("test_kernel", 55.0)

        # Get analysis
        report = gpu_opt.analyze_performance()
        assert report["memory"]["allocated_mb"] == 512.0
        assert report["kernels"]["total_profiled"] == 1

        # Get recommendations
        recommendations = gpu_opt.get_optimization_recommendations()
        assert isinstance(recommendations, list)

        gpu_opt.memory_manager.deallocate(alloc_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
