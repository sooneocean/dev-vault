"""
Performance optimization subsystem for model and resource optimization.

Includes:
- Model optimization strategies (quantization, pruning, knowledge distillation)
- Pipeline parallelism with multi-stage processing
- GPU optimization with memory management and kernel profiling
- Execution profiling and bottleneck identification
"""

from src.optimization.model_optimizer import (
    QuantizationType,
    PruningStrategy,
    QuantizationConfig,
    PruningConfig,
    DistillationConfig,
    OptimizationResult,
    ModelQuantizer,
    ModelPruner,
    KnowledgeDistiller,
    ModelOptimizer,
    init_model_optimizer,
    get_model_optimizer,
)

from src.optimization.pipeline import (
    StageStatus,
    StageMetrics,
    PipelineTask,
    PipelineStage,
    Pipeline,
    PipelineOrchestrator,
    init_orchestrator,
    get_orchestrator,
)

from src.optimization.gpu_optimizer import (
    GPUMemoryPool,
    ComputeStrategy,
    GPUMemoryStats,
    KernelProfile,
    GPUMemoryManager,
    CUDAKernelOptimizer,
    ComputeIOOverlapManager,
    GPUOptimizer,
    init_gpu_optimizer,
    get_gpu_optimizer,
)

from src.optimization.profiler import (
    ProfileScope,
    ExecutionTrace,
    ProfileStats,
    ExecutionProfiler,
    MemoryProfiler,
    BottleneckAnalyzer,
    init_profilers,
    get_execution_profiler,
    get_bottleneck_analyzer,
)

__all__ = [
    # Model optimizer
    "QuantizationType",
    "PruningStrategy",
    "QuantizationConfig",
    "PruningConfig",
    "DistillationConfig",
    "OptimizationResult",
    "ModelQuantizer",
    "ModelPruner",
    "KnowledgeDistiller",
    "ModelOptimizer",
    "init_model_optimizer",
    "get_model_optimizer",
    # Pipeline
    "StageStatus",
    "StageMetrics",
    "PipelineTask",
    "PipelineStage",
    "Pipeline",
    "PipelineOrchestrator",
    "init_orchestrator",
    "get_orchestrator",
    # GPU optimizer
    "GPUMemoryPool",
    "ComputeStrategy",
    "GPUMemoryStats",
    "KernelProfile",
    "GPUMemoryManager",
    "CUDAKernelOptimizer",
    "ComputeIOOverlapManager",
    "GPUOptimizer",
    "init_gpu_optimizer",
    "get_gpu_optimizer",
    # Profiler
    "ProfileScope",
    "ExecutionTrace",
    "ProfileStats",
    "ExecutionProfiler",
    "MemoryProfiler",
    "BottleneckAnalyzer",
    "init_profilers",
    "get_execution_profiler",
    "get_bottleneck_analyzer",
]
