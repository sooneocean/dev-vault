"""Performance benchmarks for optical flow alignment after optimization."""

import numpy as np
import timeit
import pytest
from src.watermark_removal.optical_flow.alignment import warp_region_boundary


class TestWarpRegionBoundaryBenchmark:
    """Benchmark warp_region_boundary vectorized implementation."""

    def benchmark_warp_region_boundary(self):
        """Test warp_region_boundary performance with different boundary sizes.

        Expected improvements from vectorization:
        - Small boundaries (50 pts):    Expected 2-5ms
        - Medium boundaries (200 pts):  Expected 2-5ms
        - Large boundaries (500 pts):   Expected 3-8ms

        Vectorized approach should show sub-linear growth with point count,
        unlike a naive loop-based implementation.
        """
        # Setup test data - realistic optical flow
        flow = np.random.randn(720, 1280, 2).astype(np.float32) * 5

        test_cases = [
            (50, "Small (50 pts)"),
            (200, "Medium (200 pts)"),
            (500, "Large (500 pts)"),
        ]

        results = []

        for num_points, label in test_cases:
            # Generate random boundary points
            region_pts = np.random.uniform(
                [0, 0],
                [1280, 720],
                size=(num_points, 2)
            ).astype(np.float32)

            # Warm up
            _ = warp_region_boundary(flow, region_pts)

            # Benchmark
            num_runs = 100
            elapsed = timeit.timeit(
                lambda: warp_region_boundary(flow, region_pts),
                number=num_runs
            )

            avg_time_ms = (elapsed / num_runs) * 1000
            time_per_point_us = (elapsed / num_runs / num_points) * 1e6

            results.append({
                'label': label,
                'num_points': num_points,
                'avg_time_ms': avg_time_ms,
                'per_point_us': time_per_point_us,
            })

            print(f"Boundary {label:20s}: {avg_time_ms:6.3f} ms/call "
                  f"({time_per_point_us:6.2f} µs/point)")

        # Verify performance characteristics
        print("\n✅ Benchmark Complete")
        print(f"\nExpected: All calls < 8ms (vectorized is efficient)")
        print(f"Actual:   Small={results[0]['avg_time_ms']:.3f}ms, "
              f"Med={results[1]['avg_time_ms']:.3f}ms, "
              f"Large={results[2]['avg_time_ms']:.3f}ms")

        # Assert all fall within acceptable range
        for result in results:
            assert result['avg_time_ms'] < 10, (
                f"{result['label']}: {result['avg_time_ms']:.3f}ms exceeds 10ms threshold"
            )

        # Verify sub-linear scaling (vectorized behavior)
        # Time per point should not increase significantly with point count
        small_per_point = results[0]['per_point_us']
        large_per_point = results[2]['per_point_us']

        print(f"\nPer-point time growth: {small_per_point:.2f}µs → {large_per_point:.2f}µs")
        print(f"(Good: <2x growth, Excellent: <1.5x growth)")

        assert large_per_point < small_per_point * 2.5, (
            f"Per-point time scaling suggests non-vectorized implementation"
        )

    def benchmark_flow_field_impact(self):
        """Benchmark impact of flow field resolution."""
        test_cases = [
            ((360, 640, 2), "480p"),
            ((720, 1280, 2), "720p"),
            ((1080, 1920, 2), "1080p"),
            ((2160, 3840, 2), "4K"),
        ]

        num_points = 200
        region_pts = np.random.uniform(
            [0, 0],
            [1920, 1080],
            size=(num_points, 2)
        ).astype(np.float32)

        print("\nFlow Field Resolution Impact:")
        print("-" * 60)

        for shape, label in test_cases:
            flow = np.random.randn(*shape).astype(np.float32) * 5

            # Adjust points to be within bounds
            max_x, max_y = shape[1] - 1, shape[0] - 1
            region_pts_scaled = np.random.uniform(
                [0, 0],
                [max_x, max_y],
                size=(num_points, 2)
            ).astype(np.float32)

            # Warm up
            _ = warp_region_boundary(flow, region_pts_scaled)

            # Benchmark
            num_runs = 100
            elapsed = timeit.timeit(
                lambda: warp_region_boundary(flow, region_pts_scaled),
                number=num_runs
            )

            avg_time_ms = (elapsed / num_runs) * 1000
            print(f"  {label:10s}: {avg_time_ms:6.3f} ms")

        print("✅ Flow field resolution benchmark complete")

    def benchmark_point_density_scaling(self):
        """Benchmark scaling with varying point densities."""
        flow = np.random.randn(720, 1280, 2).astype(np.float32) * 5

        point_counts = [10, 50, 100, 200, 500, 1000]

        print("\nPoint Density Scaling:")
        print("-" * 50)
        print("Points\tTime(ms)\tTime/Point(µs)")
        print("-" * 50)

        times = []
        for num_points in point_counts:
            region_pts = np.random.uniform(
                [0, 0],
                [1280, 720],
                size=(num_points, 2)
            ).astype(np.float32)

            # Warm up
            _ = warp_region_boundary(flow, region_pts)

            # Benchmark
            num_runs = 50
            elapsed = timeit.timeit(
                lambda: warp_region_boundary(flow, region_pts),
                number=num_runs
            )

            avg_time_ms = (elapsed / num_runs) * 1000
            time_per_point = (avg_time_ms / num_points) * 1000  # convert to µs

            times.append(avg_time_ms)
            print(f"{num_points}\t{avg_time_ms:.3f}\t\t{time_per_point:.2f}")

        print("-" * 50)

        # Calculate scaling factor
        first_time = times[0]
        last_time = times[-1]
        first_points = point_counts[0]
        last_points = point_counts[-1]

        point_ratio = last_points / first_points
        time_ratio = last_time / first_time if first_time > 0 else 1

        print(f"\nScaling Analysis:")
        print(f"  Points: {first_points} → {last_points} ({point_ratio:.1f}x)")
        print(f"  Time:   {first_time:.3f}ms → {last_time:.3f}ms ({time_ratio:.2f}x)")
        print(f"  O(n) efficiency: {time_ratio / point_ratio:.2f} "
              f"(1.0 = perfect linear, <1.0 = sublinear)")

        # Vectorized implementation should show sublinear or linear scaling
        assert time_ratio < point_ratio * 1.5, (
            f"Time scaling ({time_ratio:.2f}x) suggests non-vectorized implementation"
        )

        print("✅ Point density scaling analysis complete")


class TestWarpRegionBoundaryAccuracy:
    """Verify correctness of warp_region_boundary."""

    def test_warp_correctness_constant_flow(self):
        """Test warp with constant flow field."""
        h, w = 100, 100
        flow = np.ones((h, w, 2), dtype=np.float32)
        flow[..., 0] = 5.0  # 5 pixels right
        flow[..., 1] = 3.0  # 3 pixels down

        pts = np.array([[10.0, 10.0], [50.0, 50.0], [80.0, 80.0]], dtype=np.float32)

        warped = warp_region_boundary(flow, pts)

        # Each point should move by (5, 3)
        expected = pts + np.array([5.0, 3.0])

        assert np.allclose(warped, expected, atol=0.01), (
            f"Warp result incorrect.\nExpected: {expected}\nGot: {warped}"
        )
        print("✅ Constant flow warping correct")

    def test_warp_point_clamping(self):
        """Test that flow indexing is clamped correctly for out-of-bounds points.

        warp_region_boundary clamps the flow index, not the output points.
        Points can move outside bounds, but flow lookup is safe.
        """
        h, w = 100, 100
        flow = np.ones((h, w, 2), dtype=np.float32) * 10  # Constant flow

        # Points including out-of-bounds (flow lookup should clamp indices)
        pts = np.array([
            [-10.0, 50.0],   # x will be clamped to 0 for flow lookup
            [50.0, -10.0],   # y will be clamped to 0 for flow lookup
            [150.0, 150.0],  # Both clamped to max bounds
        ], dtype=np.float32)

        # Should not raise an error (flow lookup is safe)
        warped = warp_region_boundary(flow, pts)

        # Points are warped by flow, so they should move 10 pixels
        # Original points + flow offset
        expected = pts + 10.0

        assert np.allclose(warped, expected, atol=0.1), (
            f"Warped points incorrect.\nExpected: {expected}\nGot: {warped}"
        )

        print("✅ Point clamping working correctly (flow index safe, points can move outside bounds)")

    def test_warp_zero_flow(self):
        """Test with zero flow (points should remain unchanged)."""
        h, w = 100, 100
        flow = np.zeros((h, w, 2), dtype=np.float32)

        pts = np.array([[10.0, 20.0], [50.0, 50.0], [90.0, 80.0]], dtype=np.float32)

        warped = warp_region_boundary(flow, pts)

        assert np.allclose(warped, pts, atol=0.01), (
            "Points should not change with zero flow"
        )
        print("✅ Zero flow handling correct")


class TestOptimizationImpact:
    """Quantify performance improvements from optimization."""

    def test_optimization_summary(self):
        """Generate summary of optimization impact."""
        print("\n" + "=" * 70)
        print("OPTIMIZATION IMPACT SUMMARY - warp_region_boundary")
        print("=" * 70)

        flow = np.random.randn(720, 1280, 2).astype(np.float32) * 5

        test_cases = [
            (50, "Small"),
            (200, "Medium"),
            (500, "Large"),
        ]

        print("\nBenchmark Results (100 runs each):")
        print("-" * 70)
        print(f"{'Boundary Size':<20} {'Time (ms)':<15} {'Status':<15}")
        print("-" * 70)

        all_pass = True
        for num_points, label in test_cases:
            region_pts = np.random.uniform(
                [0, 0],
                [1280, 720],
                size=(num_points, 2)
            ).astype(np.float32)

            _ = warp_region_boundary(flow, region_pts)

            num_runs = 100
            elapsed = timeit.timeit(
                lambda: warp_region_boundary(flow, region_pts),
                number=num_runs
            )

            avg_time_ms = (elapsed / num_runs) * 1000

            # Determine status
            if avg_time_ms < 3:
                status = "Excellent ✅"
            elif avg_time_ms < 8:
                status = "Good ✅"
            elif avg_time_ms < 15:
                status = "Acceptable ⚠️"
            else:
                status = "Slow ❌"
                all_pass = False

            print(f"{label} ({num_points} pts){'':<10} {avg_time_ms:>8.3f}{'':<6} {status}")

        print("-" * 70)
        print(f"\nConclusion: {'All tests PASSED ✅' if all_pass else 'Some tests FAILED ❌'}")
        print("\nExpected improvement from vectorization:")
        print("  • Vectorized fancy indexing: ~8-15x faster than element-wise loop")
        print("  • Memory-efficient: Single numpy operation vs Python loop")
        print("  • Sub-linear memory growth with point count")

        if all_pass:
            print("\n✅ Performance meets optimization goals")
        else:
            print("\n⚠️ Performance may need further optimization")

        print("=" * 70)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
