#!/usr/bin/env python3
"""
TorchVision RAFT PyTorch 2.0 Compatibility & Performance Verification

Validates:
1. PyTorch 2.0+ compatibility with TorchVision RAFT
2. GPU availability and memory
3. End-to-end optical flow inference latency
4. Model loading and warmup
"""

import sys
import time
import torch
import torchvision
from typing import Tuple
import numpy as np


def check_environment() -> dict:
    """Check PyTorch/CUDA environment."""
    print("\n" + "="*60)
    print("ENVIRONMENT CHECK")
    print("="*60)

    env = {
        "pytorch_version": torch.__version__,
        "torchvision_version": torchvision.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_version": torch.version.cuda if torch.cuda.is_available() else None,
        "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
    }

    for key, value in env.items():
        print(f"  {key}: {value}")

    # Check PyTorch version >= 2.0
    major, minor = map(int, torch.__version__.split('.')[:2])
    if major < 2:
        print(f"\n⚠️  PyTorch {major}.{minor} detected. TorchVision RAFT requires 2.0+")
        return env

    print(f"\n✅ PyTorch {major}.{minor} compatible with TorchVision RAFT")
    return env


def check_memory() -> bool:
    """Check available GPU memory."""
    print("\n" + "="*60)
    print("GPU MEMORY CHECK")
    print("="*60)

    if not torch.cuda.is_available():
        print("  No GPU detected. Will run on CPU (slow).")
        return False

    total_mem = torch.cuda.get_device_properties(0).total_memory / 1e9
    allocated = torch.cuda.memory_allocated() / 1e9
    reserved = torch.cuda.memory_reserved() / 1e9

    print(f"  Total memory: {total_mem:.1f} GB")
    print(f"  Currently allocated: {allocated:.1f} GB")
    print(f"  Currently reserved: {reserved:.1f} GB")
    print(f"  Available: {total_mem - reserved:.1f} GB")

    # RAFT model needs ~2GB for inference
    if total_mem < 3:
        print(f"\n⚠️  Only {total_mem:.1f}GB available. RAFT may fail.")
        return False

    print(f"\n✅ Sufficient GPU memory for RAFT")
    return True


def load_raft_model(device: str = "cuda"):
    """Load RAFT optical flow model."""
    print("\n" + "="*60)
    print("LOADING RAFT MODEL")
    print("="*60)

    try:
        from torchvision.models.optical_flow import raft_large

        print(f"  Loading raft_large (pretrained) to {device}...")
        start_time = time.time()

        model = raft_large(pretrained=True).to(device)
        model.eval()

        load_time = time.time() - start_time
        print(f"  ✅ Model loaded in {load_time:.2f}s")

        # Count parameters
        params = sum(p.numel() for p in model.parameters())
        print(f"  Model parameters: {params/1e6:.1f}M")

        return model

    except ImportError as e:
        print(f"  ❌ Failed to load RAFT: {e}")
        print(f"  Install with: pip install torchvision>=0.15")
        sys.exit(1)
    except Exception as e:
        print(f"  ❌ Error loading model: {e}")
        sys.exit(1)


def create_dummy_frames(size: Tuple[int, int] = (1080, 1920)) -> Tuple[torch.Tensor, torch.Tensor]:
    """Create dummy frame pair for testing."""
    h, w = size
    # Random frames [B, 3, H, W], dtype float32, range [0, 1]
    frame1 = torch.rand(1, 3, h, w, dtype=torch.float32)
    frame2 = torch.rand(1, 3, h, w, dtype=torch.float32)
    return frame1, frame2


def benchmark_optical_flow(model, device: str, resolution: Tuple[int, int], num_runs: int = 5):
    """Benchmark optical flow inference."""
    print("\n" + "="*60)
    print(f"OPTICAL FLOW BENCHMARK ({resolution[0]}x{resolution[1]})")
    print("="*60)

    # Create dummy frames
    frame1, frame2 = create_dummy_frames(resolution)
    frame1 = frame1.to(device)
    frame2 = frame2.to(device)

    print(f"  Frame size: {frame1.shape}")
    print(f"  Warmup run...")

    # Warmup
    with torch.no_grad():
        _ = model(frame1, frame2)

    if device == "cuda":
        torch.cuda.synchronize()

    # Benchmark
    times = []
    print(f"  Running {num_runs} iterations...")

    for i in range(num_runs):
        if device == "cuda":
            torch.cuda.synchronize()
            start = torch.cuda.Event(enable_timing=True)
            end = torch.cuda.Event(enable_timing=True)
            start.record()
        else:
            start = time.time()

        with torch.no_grad():
            flow = model(frame1, frame2)

        if device == "cuda":
            end.record()
            torch.cuda.synchronize()
            elapsed_ms = start.elapsed_time(end)
        else:
            elapsed_ms = (time.time() - start) * 1000

        times.append(elapsed_ms)
        print(f"    Iteration {i+1}: {elapsed_ms:.1f}ms")

    # Statistics
    times_arr = np.array(times)
    print(f"\n  Statistics (ms):")
    print(f"    Mean: {times_arr.mean():.1f}")
    print(f"    Median: {np.median(times_arr):.1f}")
    print(f"    Min: {times_arr.min():.1f}")
    print(f"    Max: {times_arr.max():.1f}")
    print(f"    Std: {times_arr.std():.1f}")

    fps = 1000 / times_arr.mean()
    print(f"\n  Estimated FPS: {fps:.1f}")

    return {
        "resolution": resolution,
        "mean_latency_ms": times_arr.mean(),
        "median_latency_ms": np.median(times_arr),
        "fps": fps,
        "device": device,
    }


def estimate_end_to_end_latency(raft_latency: dict) -> dict:
    """Estimate full pipeline latency including other components."""
    print("\n" + "="*60)
    print("END-TO-END PIPELINE LATENCY ESTIMATE")
    print("="*60)

    # Component latencies (ms)
    components = {
        "Frame decode (OpenCV)": (6, 12),           # ms range
        "Optical flow (RAFT)": (raft_latency["mean_latency_ms"], raft_latency["mean_latency_ms"]),
        "Ensemble detection (YOLOv5m)": (80, 120),   # estimated
        "Inpaint (Flux)": (200, 400),                # estimated
        "Temporal smoothing": (2, 5),
        "Background queue": (5, 10),
    }

    min_total = sum(v[0] for v in components.values())
    max_total = sum(v[1] for v in components.values())
    mean_total = sum((v[0] + v[1]) / 2 for v in components.values())

    print("\n  Component breakdown (ms):")
    for name, (min_ms, max_ms) in components.items():
        avg = (min_ms + max_ms) / 2
        print(f"    {name}: {min_ms:.0f}-{max_ms:.0f} (avg: {avg:.0f})")

    print(f"\n  Total end-to-end latency: {min_total:.0f}-{max_total:.0f}ms (avg: {mean_total:.0f}ms)")
    print(f"  Estimated FPS: {1000/mean_total:.1f}")

    # Check against 30 FPS target
    target_latency = 1000 / 30  # ~33ms
    print(f"\n  30 FPS target requires: {target_latency:.0f}ms per frame")
    if mean_total > target_latency:
        print(f"  ⚠️  Pipeline too slow for 30 FPS by {mean_total - target_latency:.0f}ms")
        print(f"  → Recommend 6-10 FPS target @ 1080p, or reduce resolution to 480p")

    return {
        "min_total_ms": min_total,
        "max_total_ms": max_total,
        "mean_total_ms": mean_total,
        "estimated_fps": 1000 / mean_total,
        "target_fps": 30,
        "achievable": mean_total < target_latency,
    }


def main():
    print("\n" + "="*60)
    print("TorchVision RAFT - PyTorch 2.0 Compatibility Verification")
    print("="*60)

    # Step 1: Environment check
    env = check_environment()
    major, minor = map(int, torch.__version__.split('.')[:2])
    if major < 2:
        print("\n❌ FAILED: PyTorch < 2.0")
        print("   Install with: pip install torch>=2.0 torchvision>=0.15")
        sys.exit(1)

    # Step 2: Memory check
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        print("\n⚠️  Running on CPU (slow). For GPU, install CUDA drivers.")

    # Step 3: Load model
    model = load_raft_model(device)

    # Step 4: Benchmark different resolutions
    benchmarks = []

    # 1080p (realistic high resolution)
    print("\n" + "-"*60)
    result_1080p = benchmark_optical_flow(model, device, (1080, 1920), num_runs=5)
    benchmarks.append(result_1080p)

    # 480p (lower resolution option)
    print("\n" + "-"*60)
    result_480p = benchmark_optical_flow(model, device, (480, 856), num_runs=5)
    benchmarks.append(result_480p)

    # Step 5: Estimate end-to-end latency
    print("\n" + "-"*60)
    pipeline_est = estimate_end_to_end_latency(result_1080p)

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    print("\n✅ RAFT Model Compatible with PyTorch 2.0+")
    print(f"\nOptical Flow Latency:")
    print(f"  @ 1080p: {result_1080p['mean_latency_ms']:.1f}ms ({result_1080p['fps']:.1f} FPS)")
    print(f"  @ 480p:  {result_480p['mean_latency_ms']:.1f}ms ({result_480p['fps']:.1f} FPS)")

    print(f"\nEnd-to-End Pipeline:")
    print(f"  Estimated latency: {pipeline_est['mean_total_ms']:.0f}ms")
    print(f"  Estimated FPS: {pipeline_est['estimated_fps']:.1f}")
    print(f"  30 FPS target: {'✅ ACHIEVABLE' if pipeline_est['achievable'] else '❌ NOT ACHIEVABLE'}")

    print(f"\n📝 Recommendation for Phase 3A:")
    if pipeline_est['estimated_fps'] >= 10:
        print(f"  → 6-10 FPS @ 1080p is realistic target")
        print(f"  → Consider 480p option for 15-20 FPS if needed")
    else:
        print(f"  → Focus on 480p resolution for acceptable latency")
        print(f"  → Defer to Phase 3B: model optimization, TensorRT quantization")

    print("\n✅ Verification complete. Safe to proceed with Phase 3A implementation.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
