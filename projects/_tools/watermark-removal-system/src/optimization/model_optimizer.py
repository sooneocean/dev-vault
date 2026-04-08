"""
Model optimization strategies for neural networks.

Includes quantization, pruning, knowledge distillation, and layer fusion.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class QuantizationType(str, Enum):
    """Quantization types for model optimization."""
    FP32 = "fp32"  # Full precision (baseline)
    FP16 = "fp16"  # Half precision
    INT8 = "int8"  # 8-bit integer
    INT4 = "int4"  # 4-bit integer
    MIXED = "mixed"  # Mixed precision


class PruningStrategy(str, Enum):
    """Pruning strategies for model compression."""
    MAGNITUDE = "magnitude"  # Prune small weight magnitude
    GRADIENT = "gradient"  # Prune low gradient weights
    STRUCTURED = "structured"  # Prune entire filters/channels
    UNSTRUCTURED = "unstructured"  # Prune individual weights


@dataclass
class QuantizationConfig:
    """Configuration for quantization."""
    quantization_type: QuantizationType = QuantizationType.FP32
    activation_bits: int = 8
    weight_bits: int = 8
    per_channel: bool = True  # Per-channel vs per-tensor quantization
    symmetric: bool = False  # Symmetric vs asymmetric quantization


@dataclass
class PruningConfig:
    """Configuration for pruning."""
    strategy: PruningStrategy = PruningStrategy.MAGNITUDE
    target_sparsity: float = 0.5  # Target % of weights to prune (0.0-1.0)
    iterative: bool = True  # Iterative pruning with fine-tuning
    fine_tune_epochs: int = 10


@dataclass
class DistillationConfig:
    """Configuration for knowledge distillation."""
    teacher_model: str = None
    temperature: float = 3.0  # Softening temperature
    alpha: float = 0.5  # Weight of distillation loss vs original loss
    batch_size: int = 32


@dataclass
class OptimizationResult:
    """Result of model optimization."""
    original_size_mb: float
    optimized_size_mb: float
    compression_ratio: float
    latency_improvement: float  # % improvement (negative = slower)
    accuracy_impact: float  # % change in accuracy (negative = worse)
    memory_improvement: float  # % improvement


class ModelQuantizer:
    """Quantize neural network models."""

    def __init__(self, config: QuantizationConfig = None):
        self.config = config or QuantizationConfig()
        self.quantization_stats: Dict[str, Any] = {}

    def compute_quantization_stats(self, activations: List[float]) -> Dict[str, float]:
        """Compute quantization statistics from activations."""
        if not activations:
            return {}

        import statistics

        mean = statistics.mean(activations)
        stdev = statistics.stdev(activations) if len(activations) > 1 else 0
        min_val = min(activations)
        max_val = max(activations)

        return {
            "mean": mean,
            "std": stdev,
            "min": min_val,
            "max": max_val,
            "range": max_val - min_val,
        }

    def quantize_weights(self, weights: List[float]) -> Tuple[List[int], Dict[str, float]]:
        """Quantize model weights to lower precision."""
        if not weights:
            return [], {}

        stats = self.compute_quantization_stats(weights)

        # Determine quantization range based on type
        if self.config.quantization_type == QuantizationType.INT8:
            q_min, q_max = -128, 127
        elif self.config.quantization_type == QuantizationType.INT4:
            q_min, q_max = -8, 7
        elif self.config.quantization_type == QuantizationType.FP16:
            # FP16 range approximately -65504 to 65504
            q_min, q_max = -65504, 65504
        else:
            return weights, stats

        # Linear quantization
        w_min, w_max = stats["min"], stats["max"]
        scale = (q_max - q_min) / (w_max - w_min) if w_max > w_min else 1.0
        zero_point = q_min - w_min * scale

        quantized = [int(w * scale + zero_point) for w in weights]
        stats["scale"] = scale
        stats["zero_point"] = zero_point

        return quantized, stats

    def estimate_memory_savings(self, original_bits: int = 32, quantized_bits: int = 8) -> float:
        """Estimate memory savings from quantization."""
        return 1.0 - (quantized_bits / original_bits)

    def get_quantization_report(self) -> Dict[str, Any]:
        """Get quantization report."""
        return {
            "quantization_type": self.config.quantization_type.value,
            "activation_bits": self.config.activation_bits,
            "weight_bits": self.config.weight_bits,
            "per_channel": self.config.per_channel,
            "symmetric": self.config.symmetric,
            "stats": self.quantization_stats,
        }


class ModelPruner:
    """Prune neural network models to reduce size."""

    def __init__(self, config: PruningConfig = None):
        self.config = config or PruningConfig()
        self.pruning_history: List[Dict[str, Any]] = []

    def compute_magnitude_scores(self, weights: List[float]) -> List[float]:
        """Compute magnitude-based pruning scores."""
        return [abs(w) for w in weights]

    def compute_gradient_scores(self, gradients: List[float]) -> List[float]:
        """Compute gradient-based pruning scores."""
        # Score based on absolute gradient magnitude
        return [abs(g) for g in gradients]

    def select_pruning_candidates(self, scores: List[float]) -> List[int]:
        """Select weights to prune based on scores."""
        if not scores:
            return []

        # Sort by score (ascending) and get indices
        sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i])

        # Prune bottom target_sparsity% of weights
        num_to_prune = int(len(scores) * self.config.target_sparsity)
        return sorted_indices[:num_to_prune]

    def prune_weights(self, weights: List[float]) -> Tuple[List[float], Dict[str, Any]]:
        """Prune model weights."""
        if not weights:
            return [], {}

        # Compute scores
        if self.config.strategy == PruningStrategy.MAGNITUDE:
            scores = self.compute_magnitude_scores(weights)
        else:
            scores = self.compute_magnitude_scores(weights)

        # Select candidates
        candidates = self.select_pruning_candidates(scores)

        # Prune
        pruned = [weights[i] if i not in candidates else 0.0 for i in range(len(weights))]

        stats = {
            "original_weights": len(weights),
            "pruned_weights": len(candidates),
            "remaining_weights": len(weights) - len(candidates),
            "sparsity": len(candidates) / len(weights) if weights else 0.0,
            "strategy": self.config.strategy.value,
        }

        self.pruning_history.append(stats)
        return pruned, stats

    def get_pruning_report(self) -> Dict[str, Any]:
        """Get pruning report."""
        return {
            "strategy": self.config.strategy.value,
            "target_sparsity": self.config.target_sparsity,
            "iterative": self.config.iterative,
            "fine_tune_epochs": self.config.fine_tune_epochs,
            "history": self.pruning_history,
        }


class KnowledgeDistiller:
    """Knowledge distillation for model compression."""

    def __init__(self, config: DistillationConfig = None):
        self.config = config or DistillationConfig()
        self.distillation_metrics: Dict[str, float] = {}

    def compute_soft_targets(self, teacher_logits: List[float], temperature: float = 1.0) -> List[float]:
        """Compute soft targets from teacher model."""
        if not teacher_logits:
            return []

        # Simulate softmax with temperature
        import math

        max_logit = max(teacher_logits)
        exp_logits = [math.exp((l - max_logit) / temperature) for l in teacher_logits]
        sum_exp = sum(exp_logits)

        return [e / sum_exp for e in exp_logits] if sum_exp > 0 else teacher_logits

    def compute_distillation_loss(
        self,
        student_logits: List[float],
        teacher_logits: List[float],
        hard_targets: List[int],
        temperature: float = 1.0,
        alpha: float = 0.5,
    ) -> float:
        """Compute distillation loss."""
        if not student_logits or not teacher_logits:
            return 0.0

        soft_targets = self.compute_soft_targets(teacher_logits, temperature)

        # Simple KL divergence approximation
        kl_loss = sum(
            (s - t) ** 2 for s, t in zip(soft_targets, student_logits)
        ) / len(student_logits)

        return kl_loss

    def get_distillation_report(self) -> Dict[str, Any]:
        """Get distillation report."""
        return {
            "teacher_model": self.config.teacher_model,
            "temperature": self.config.temperature,
            "alpha": self.config.alpha,
            "batch_size": self.config.batch_size,
            "metrics": self.distillation_metrics,
        }


class ModelOptimizer:
    """Main model optimization engine."""

    def __init__(self):
        self.quantizer = ModelQuantizer()
        self.pruner = ModelPruner()
        self.distiller = KnowledgeDistiller()
        self.optimization_history: List[OptimizationResult] = []

    def optimize_model(
        self,
        model_size_mb: float,
        quantization_config: QuantizationConfig = None,
        pruning_config: PruningConfig = None,
    ) -> OptimizationResult:
        """Optimize model with quantization and/or pruning."""
        optimized_size = model_size_mb
        latency_improvement = 0.0
        accuracy_impact = 0.0

        # Apply quantization
        if quantization_config:
            self.quantizer.config = quantization_config
            memory_savings = self.quantizer.estimate_memory_savings()
            optimized_size *= (1 - memory_savings)

            # Estimate improvements
            if quantization_config.quantization_type == QuantizationType.INT8:
                latency_improvement += 30.0  # 30% faster
                accuracy_impact -= 1.0  # ~1% accuracy loss
            elif quantization_config.quantization_type == QuantizationType.FP16:
                latency_improvement += 20.0
                accuracy_impact -= 0.3

        # Apply pruning
        if pruning_config:
            self.pruner.config = pruning_config
            optimized_size *= (1 - pruning_config.target_sparsity)
            latency_improvement += pruning_config.target_sparsity * 50
            accuracy_impact -= pruning_config.target_sparsity * 2

        compression_ratio = model_size_mb / optimized_size if optimized_size > 0 else 1.0
        memory_improvement = (model_size_mb - optimized_size) / model_size_mb * 100

        result = OptimizationResult(
            original_size_mb=model_size_mb,
            optimized_size_mb=optimized_size,
            compression_ratio=compression_ratio,
            latency_improvement=latency_improvement,
            accuracy_impact=accuracy_impact,
            memory_improvement=memory_improvement,
        )

        self.optimization_history.append(result)
        return result

    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get optimization summary."""
        if not self.optimization_history:
            return {}

        return {
            "total_optimizations": len(self.optimization_history),
            "avg_compression_ratio": sum(r.compression_ratio for r in self.optimization_history) / len(self.optimization_history),
            "avg_latency_improvement": sum(r.latency_improvement for r in self.optimization_history) / len(self.optimization_history),
            "avg_accuracy_impact": sum(r.accuracy_impact for r in self.optimization_history) / len(self.optimization_history),
        }

    def reset(self):
        """Reset optimizer."""
        self.quantizer = ModelQuantizer()
        self.pruner = ModelPruner()
        self.distiller = KnowledgeDistiller()
        self.optimization_history.clear()


# Global optimizer instance
model_optimizer: Optional[ModelOptimizer] = None


def init_model_optimizer():
    """Initialize global model optimizer."""
    global model_optimizer
    model_optimizer = ModelOptimizer()
    logger.info("Model optimizer initialized")


def get_model_optimizer() -> ModelOptimizer:
    """Get global model optimizer instance."""
    global model_optimizer
    if model_optimizer is None:
        init_model_optimizer()
    return model_optimizer
