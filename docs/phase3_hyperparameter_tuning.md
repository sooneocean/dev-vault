---
title: Phase 3: Hyperparameter Tuning Guide
type: project
tags: [project, active]
created: 2026-04-03
updated: 2026-04-03
status: active
maturity: growing
domain: knowledge-management
summary: ""
---

# Phase 3: Hyperparameter Tuning Guide

## Overview

The Phase 3 Optuna integration enables systematic hyperparameter optimization for the watermark removal pipeline. This guide covers Optuna study creation, search space definition, trial execution, pruning strategies, result analysis, and integration with production pipelines.

## Architecture

```
Optuna Study Manager
├─→ Trial 1: (batch_size=2, crf=20)  ─→ Evaluation  ─→ Score
├─→ Trial 2: (batch_size=4, crf=22)  ─→ Evaluation  ─→ Score
├─→ Trial 3: (batch_size=3, crf=21)  ─→ Evaluation  ─→ Score
└─→ [Pruning & Sampling]             ─→ Best config ─→ Deploy

Metrics tracked:
  - Processing time per frame
  - Memory usage (peak)
  - Quality (LPIPS, SSIM)
  - Boundary smoothness
```

## Optuna Study Creation

### 1. Basic Study Setup

```python
import optuna
from optuna.samplers import TPESampler
from optuna.pruners import PercentilePruner

# Create study
study = optuna.create_study(
    study_name="watermark_removal_phase3",
    direction="minimize",  # Minimize processing time
    sampler=TPESampler(seed=42),
    pruner=PercentilePruner(
        percentile=25,  # Prune bottom 25%
        n_startup_trials=10,  # Wait for 10 trials before pruning
        n_warmup_steps=5
    ),
    storage="sqlite:///optuna_phase3.db",
    load_if_exists=True
)
```

**Study directions**:
- `minimize` — Optimize for speed/cost (processing time, memory)
- `maximize` — Optimize for quality (LPIPS, temporal consistency)

### 2. Study Storage Options

```python
# Option A: SQLite (local, persistent)
study = optuna.create_study(
    storage="sqlite:///studies/phase3.db"
)

# Option B: PostgreSQL (distributed)
study = optuna.create_study(
    storage="postgresql://user:password@localhost/optuna"
)

# Option C: In-memory (development only)
study = optuna.create_study()  # Default
```

### 3. Study Configuration

```python
# Configure sampler
sampler = optuna.samplers.TPESampler(
    n_startup_trials=10,  # Pure random first 10
    n_ei_candidates=24,   # Evaluate 24 candidates each step
    seed=42
)

# Configure pruner
pruner = optuna.pruners.PercentilePruner(
    percentile=25,        # Prune bottom 25% of trials
    n_startup_trials=10,  # Wait before pruning
    n_warmup_steps=5
)

study = optuna.create_study(
    study_name="phase3_tuning",
    direction="minimize",
    sampler=sampler,
    pruner=pruner,
    storage="sqlite:///optuna.db",
    load_if_exists=True
)
```

## Search Space Definition

### 1. Simple Search Space

Basic parameter bounds:

```python
def objective(trial):
    # Suggest hyperparameters
    batch_size = trial.suggest_int("batch_size", 1, 8)
    inpaint_steps = trial.suggest_int("inpaint_steps", 10, 50)
    cfg_scale = trial.suggest_float("cfg_scale", 1.0, 15.0)

    # Create config
    config = ProcessConfig(
        video_path=test_video,
        mask_path=test_mask,
        output_dir=temp_dir,
        batch_size=batch_size,
        inpaint_steps=inpaint_steps,
        cfg_scale=cfg_scale
    )

    # Run evaluation
    score = evaluate_pipeline(config)
    return score

# Optimize
study.optimize(objective, n_trials=100)
```

### 2. Advanced Search Space with Constraints

```python
def objective_advanced(trial):
    # Preprocessing
    frame_scale = trial.suggest_categorical(
        "frame_scale",
        [0.5, 1.0, 1.5]  # 50%, 100%, 150% resolution
    )

    # Inpainting
    batch_size = trial.suggest_int("batch_size", 1, 8)
    inpaint_steps = trial.suggest_int("inpaint_steps", 10, 50, step=5)
    cfg_scale = trial.suggest_float("cfg_scale", 1.0, 20.0)
    sampler_name = trial.suggest_categorical(
        "sampler",
        ["euler", "dpmpp", "kdpm2"]
    )

    # Phase 3 features
    optical_flow_enabled = trial.suggest_categorical(
        "optical_flow_enabled",
        [True, False]
    )
    if optical_flow_enabled:
        optical_flow_weight = trial.suggest_float(
            "optical_flow_weight",
            0.1, 0.9, step=0.1
        )
    else:
        optical_flow_weight = 0.0

    ensemble_detection = trial.suggest_categorical(
        "ensemble_detection_enabled",
        [True, False]
    )

    # Postprocessing
    output_crf = trial.suggest_int("output_crf", 18, 28)
    edge_feather_width = trial.suggest_int(
        "edge_feather_width",
        5, 50, step=5
    )

    # Constraints
    # If using low steps, allow higher CFG
    if inpaint_steps < 20:
        trial.suggest(optuna.trial.suggest_float(
            "cfg_scale", 7.0, 15.0
        ))

    # Memory constraint: high res + large batch = OOM
    if frame_scale > 1.0 and batch_size > 4:
        raise optuna.exceptions.TrialPruned()

    # Create config
    config = ProcessConfig(
        video_path=test_video,
        mask_path=test_mask,
        output_dir=temp_dir,
        frame_scale=frame_scale,
        batch_size=batch_size,
        inpaint_steps=inpaint_steps,
        cfg_scale=cfg_scale,
        sampler_name=sampler_name,
        optical_flow_enabled=optical_flow_enabled,
        optical_flow_weight=optical_flow_weight,
        ensemble_detection_enabled=ensemble_detection,
        output_crf=output_crf,
        edge_feather_width=edge_feather_width
    )

    # Evaluate
    score = evaluate_pipeline(config)
    return score
```

## Trial Execution and Monitoring

### 1. Basic Trial Execution

```python
# Run optimization
study.optimize(objective, n_trials=100, n_jobs=1)

# View results
print(f"Best trial: {study.best_trial.number}")
print(f"Best value: {study.best_value}")
print(f"Best params: {study.best_params}")
```

### 2. Parallel Trial Execution

```python
# Multi-process execution
study.optimize(objective, n_trials=100, n_jobs=4)

# Distributed execution (requires RDB storage)
# Node 1:
study.optimize(objective, n_trials=25, n_jobs=1)

# Node 2:
study.optimize(objective, n_trials=25, n_jobs=1)

# Node 3:
study.optimize(objective, n_trials=25, n_jobs=1)

# Node 4:
study.optimize(objective, n_trials=25, n_jobs=1)

# All nodes contribute to same study
```

### 3. Progress Monitoring

```python
import logging

# Enable logging
logging.basicConfig(level=logging.INFO)

# Custom callback for progress
def callback(study, trial):
    if trial.state == optuna.trial.TrialState.COMPLETE:
        print(f"Trial {trial.number}: value={trial.value:.4f}")
        if trial.value == study.best_value:
            print("  ^ New best!")

study.optimize(objective, n_trials=100, callbacks=[callback])
```

### 4. Early Stopping with Hyperband Pruning

```python
pruner = optuna.pruners.HyperbandPruner(
    min_resource=1,
    max_resource=100,
    reduction_factor=3
)

study = optuna.create_study(
    direction="minimize",
    pruner=pruner,
    storage="sqlite:///optuna.db"
)

def objective_with_pruning(trial):
    config = create_config_from_trial(trial)

    # Evaluate in stages
    for step in range(1, 11):  # 10 stages
        score = evaluate_pipeline(config, max_frames=10*step)

        # Report intermediate value
        trial.report(score, step)

        # Check for pruning
        if trial.should_prune():
            raise optuna.exceptions.TrialPruned()

    return score

study.optimize(objective_with_pruning, n_trials=100)
```

## Result Analysis and Visualization

### 1. Best Trial Analysis

```python
best_trial = study.best_trial

print("=" * 60)
print("BEST TRIAL RESULTS")
print("=" * 60)
print(f"Trial #{best_trial.number}")
print(f"Score: {best_trial.value:.4f}")
print(f"Duration: {best_trial.duration.total_seconds():.1f}s")
print("\nBest Parameters:")
for key, value in best_trial.params.items():
    print(f"  {key}: {value}")
```

### 2. Parameter Importance Analysis

```python
from optuna.visualization import plot_param_importances

# Get importance
importances = optuna.importance.get_param_importances(study)

print("Parameter Importances (by permutation):")
for param, importance in importances.items():
    print(f"  {param}: {importance:.4f}")

# Visualize (requires plotly)
fig = plot_param_importances(study)
fig.show()
```

### 3. Trial History Visualization

```python
import pandas as pd
import matplotlib.pyplot as plt

# Extract trial data
trials_df = study.trials_dataframe()

# Plot convergence
plt.figure(figsize=(12, 6))
plt.subplot(1, 2, 1)
plt.plot(trials_df["number"], trials_df["value"])
plt.axhline(y=study.best_value, color='r', linestyle='--', label='Best')
plt.xlabel("Trial")
plt.ylabel("Score")
plt.title("Trial Convergence")
plt.legend()

# Plot parameters
plt.subplot(1, 2, 2)
for param in ["batch_size", "inpaint_steps", "cfg_scale"]:
    if param in trials_df.columns:
        plt.scatter(trials_df[param], trials_df["value"], label=param, alpha=0.5)
plt.xlabel("Parameter Value")
plt.ylabel("Score")
plt.title("Parameter vs Score")
plt.legend()
plt.tight_layout()
plt.savefig("optimization_results.png")
```

### 4. Export Results

```python
# Export to CSV
trials_df = study.trials_dataframe()
trials_df.to_csv("optimization_trials.csv", index=False)

# Export best config as YAML
import yaml

best_config = {
    "study_name": study.study_name,
    "best_value": study.best_value,
    "n_trials": len(study.trials),
    "parameters": study.best_params
}

with open("best_config.yaml", "w") as f:
    yaml.dump(best_config, f)
```

## Integration with Production Pipelines

### 1. Load Optimized Config

```python
import yaml
from watermark_removal.core.types import ProcessConfig

# Load best config from optimization
with open("best_config.yaml") as f:
    config_dict = yaml.safe_load(f)

# Create production config
config = ProcessConfig(
    video_path="/path/to/input.mp4",
    mask_path="/path/to/mask.json",
    output_dir="/path/to/output",
    **config_dict["parameters"]  # Apply optimized parameters
)

# Run pipeline
pipeline = Pipeline(config)
pipeline.run()
```

### 2. A/B Testing

Compare old vs optimized config:

```python
from watermark_removal.metrics import ProcessMetrics

# Old config (baseline)
old_config = ProcessConfig(...)
old_metrics = evaluate_config(old_config, test_frames)

# Optimized config
optimized_config = ProcessConfig(...)
optimized_metrics = evaluate_config(optimized_config, test_frames)

# Compare
improvement = (old_metrics.processing_time_ms - optimized_metrics.processing_time_ms) / old_metrics.processing_time_ms
print(f"Improvement: {improvement * 100:.1f}% faster")

# Verify quality preserved
quality_delta = abs(old_metrics.quality - optimized_metrics.quality)
if quality_delta < 0.05:
    print("Quality maintained!")
    # Deploy optimized config
```

### 3. Continuous Monitoring

Track performance in production:

```python
import json
from datetime import datetime, timedelta

# Load production baseline
with open("production_baseline.json") as f:
    baseline = json.load(f)

# Monitor recent batches
current_metrics = collect_recent_metrics(days=1)

# Compare
degradation = (current_metrics.processing_time_ms - baseline["processing_time_ms"]) / baseline["processing_time_ms"]

if degradation > 0.1:
    print("WARNING: Performance degraded 10%+")
    # Re-optimize or investigate

# Update baseline if improved
if degradation < -0.05:
    print("Performance improved! Updating baseline...")
    baseline["processing_time_ms"] = current_metrics.processing_time_ms
    with open("production_baseline.json", "w") as f:
        json.dump(baseline, f)
```

## Distributed Tuning Considerations

### 1. Multi-Machine Setup

```python
# Shared RDB storage (PostgreSQL)
storage = "postgresql://user:pass@db.example.com/optuna"

# Machine 1
study = optuna.load_study(
    study_name="phase3_distributed",
    storage=storage
)
study.optimize(objective, n_trials=50, n_jobs=4)

# Machine 2 (can run simultaneously)
study = optuna.load_study(
    study_name="phase3_distributed",
    storage=storage
)
study.optimize(objective, n_trials=50, n_jobs=4)

# Machines sync through shared DB
```

### 2. Resource Allocation

```python
# Allocate trials based on machine capability
def objective_with_resource_awareness(trial):
    # Fast machines get longer trials
    max_frames = trial.suggest_int("max_frames", 100, 1000)

    # Slow machines (or CPU-only) get shorter trials
    if not gpu_available:
        max_frames = min(max_frames, 100)

    score = evaluate_pipeline(config, max_frames=max_frames)
    return score
```

### 3. Checkpoint and Resume

```python
# Save optimization state
import pickle

# Periodic checkpoint
if trial_number % 10 == 0:
    with open(f"optimization_checkpoint_{trial_number}.pkl", "wb") as f:
        pickle.dump(study, f)

# If interrupted, resume
if os.path.exists("optimization_checkpoint_latest.pkl"):
    with open("optimization_checkpoint_latest.pkl", "rb") as f:
        study = pickle.load(f)
    print(f"Resumed from trial {len(study.trials)}")
```

## Best Practices

1. **Start with broad search**
   - Large parameter ranges initially
   - Identify high-impact parameters
   - Narrow ranges in second round

2. **Use constraints to avoid invalid configs**
   ```python
   if batch_size > 4 and resolution_scale > 1.0:
       raise optuna.exceptions.TrialPruned()
   ```

3. **Validate on held-out test set**
   - Optimize on validation frames
   - Test final config on unseen video
   - Monitor for overfitting

4. **Log all relevant metrics**
   - Processing time
   - Memory usage
   - Quality metrics (LPIPS, SSIM)
   - Resource utilization

5. **Set realistic trial budgets**
   - 100-200 trials for simple problems
   - 500-1000+ for complex multi-parameter
   - Factor in evaluation time

6. **Document assumptions**
   - Test video characteristics
   - Hardware (GPU model, VRAM)
   - Batch size constraints
   - Quality thresholds

## Troubleshooting

### Issue: Optimization converges to local optimum

**Solution**: Increase n_startup_trials and sampler diversity
```python
sampler = optuna.samplers.TPESampler(
    n_startup_trials=20,  # More exploration
    n_ei_candidates=48    # More candidates
)
```

### Issue: Very slow trial execution

**Solution**: Reduce evaluation scope
```python
def objective(trial):
    # Evaluate on subset of frames
    score = evaluate_pipeline(config, max_frames=50)  # Not 1000+
    return score
```

### Issue: Memory errors during optimization

**Solution**: Run trials sequentially
```python
study.optimize(objective, n_trials=100, n_jobs=1)  # Not 4+
```

### Issue: Inconsistent trial scores

**Solution**: Fix random seeds
```python
import numpy as np
import torch

np.random.seed(42)
torch.manual_seed(42)

study = optuna.create_study(
    sampler=optuna.samplers.TPESampler(seed=42)
)
```

## Example: Complete Optimization Script

```python
#!/usr/bin/env python
"""
Complete Phase 3 hyperparameter optimization script.
"""

import optuna
import tempfile
from pathlib import Path
from watermark_removal.core.pipeline import Pipeline
from watermark_removal.core.types import ProcessConfig
from watermark_removal.metrics import ProcessMetrics

# Test data
TEST_VIDEO = Path("/data/test_video_1080p.mp4")
TEST_MASK = Path("/data/test_mask.json")

def evaluate_pipeline(config: ProcessConfig) -> float:
    """Evaluate config and return score (lower is better)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config.output_dir = Path(tmpdir)
        pipeline = Pipeline(config)
        metrics = pipeline.run()

        # Score = processing time (primary) + quality penalty
        score = metrics.processing_time_ms * 0.001  # seconds
        if metrics.quality < 0.8:
            score += 100  # Penalize low quality
        return score

def objective(trial):
    """Define search space and trial."""
    # Suggest parameters
    batch_size = trial.suggest_int("batch_size", 1, 8)
    inpaint_steps = trial.suggest_int("inpaint_steps", 15, 50)
    cfg_scale = trial.suggest_float("cfg_scale", 5.0, 15.0)
    optical_flow_weight = trial.suggest_float("optical_flow_weight", 0.2, 0.8)

    config = ProcessConfig(
        video_path=TEST_VIDEO,
        mask_path=TEST_MASK,
        output_dir=Path("/tmp/phase3_opt"),
        batch_size=batch_size,
        inpaint_steps=inpaint_steps,
        cfg_scale=cfg_scale,
        optical_flow_enabled=True,
        optical_flow_weight=optical_flow_weight,
        ensemble_detection_enabled=True
    )

    score = evaluate_pipeline(config)
    return score

if __name__ == "__main__":
    # Create study
    study = optuna.create_study(
        study_name="phase3_optimization",
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=42),
        pruner=optuna.pruners.PercentilePruner(percentile=25),
        storage="sqlite:///optuna_phase3.db",
        load_if_exists=True
    )

    # Optimize
    print("Starting Phase 3 hyperparameter optimization...")
    study.optimize(objective, n_trials=100, n_jobs=1)

    # Results
    print("\n" + "=" * 60)
    print("OPTIMIZATION COMPLETE")
    print("=" * 60)
    print(f"Best trial: #{study.best_trial.number}")
    print(f"Best score: {study.best_value:.4f} seconds")
    print("Best parameters:")
    for key, value in study.best_params.items():
        print(f"  {key}: {value}")

    # Save config
    import yaml
    with open("best_config.yaml", "w") as f:
        yaml.dump(study.best_params, f)
    print("\nConfig saved to best_config.yaml")
```

## Further Reading

- Optuna Documentation: https://optuna.readthedocs.io
- Hyperparameter Tuning: https://arxiv.org/abs/1810.13243
- Bayesian Optimization: https://arxiv.org/abs/1807.02811
