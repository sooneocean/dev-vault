"""Tests for GPU memory lifecycle management."""

import pytest
import torch
from unittest.mock import Mock, patch, MagicMock

from src.watermark_removal.memory_manager import (
    MemoryManager,
    MemoryState,
    InsufficientVRAMError,
    VRAMSnapshot,
)


class TestMemoryManagerStates:
    """Test state machine transitions."""

    def test_initial_state_is_idle(self):
        """New MemoryManager should start in IDLE state."""
        mm = MemoryManager(device="cpu")
        assert mm.state == MemoryState.IDLE

    def test_valid_transitions(self):
        """Test valid state transitions."""
        mm = MemoryManager(device="cpu")

        # IDLE → DETECT_LOADING (valid)
        mm.transition_to(MemoryState.DETECT_LOADING)
        assert mm.state == MemoryState.DETECT_LOADING

        # DETECT_LOADING → DETECTING (valid)
        mm.transition_to(MemoryState.DETECTING)
        assert mm.state == MemoryState.DETECTING

        # DETECTING → DETECT_CLEANUP (valid)
        mm.transition_to(MemoryState.DETECT_CLEANUP)
        assert mm.state == MemoryState.DETECT_CLEANUP

        # DETECT_CLEANUP → IDLE (valid)
        mm.transition_to(MemoryState.IDLE)
        assert mm.state == MemoryState.IDLE

    def test_invalid_transitions_raise_error(self):
        """Test that invalid transitions raise ValueError."""
        mm = MemoryManager(device="cpu")

        # IDLE → INFERRING (invalid, must go through INPAINT_LOADING first)
        with pytest.raises(ValueError, match="Invalid transition"):
            mm.transition_to(MemoryState.INFERRING)

    def test_error_state_resets(self):
        """Error state should allow reset to IDLE."""
        mm = MemoryManager(device="cpu")
        mm.transition_to(MemoryState.DETECT_LOADING)
        mm.transition_to(MemoryState.ERROR)
        mm.transition_to(MemoryState.IDLE)
        assert mm.state == MemoryState.IDLE


class TestMemoryManagerVRAM:
    """Test VRAM monitoring and validation."""

    def test_vram_snapshot_cpu_device(self):
        """CPU device should report 16GB available."""
        mm = MemoryManager(device="cpu")
        snapshot = mm._get_vram_snapshot()

        assert snapshot.allocated_gb == 0.0
        assert snapshot.reserved_gb == 0.0
        assert snapshot.available_gb == 16.0
        assert snapshot.state == MemoryState.IDLE

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_vram_snapshot_cuda_device(self):
        """CUDA device should report real VRAM utilization."""
        mm = MemoryManager(device="cuda")
        snapshot = mm._get_vram_snapshot()

        assert 0 <= snapshot.allocated_gb <= 16.0
        assert 0 <= snapshot.reserved_gb <= 16.0
        assert 0 <= snapshot.available_gb <= 16.0
        assert snapshot.state == MemoryState.IDLE

    def test_validate_vram_headroom_sufficient(self):
        """Should pass validation when headroom sufficient."""
        mm = MemoryManager(device="cpu", vram_safety_threshold_gb=1.0)
        # CPU device reports 16GB available, 1GB threshold should pass
        assert mm.validate_vram_headroom() is True

    def test_validate_vram_headroom_insufficient(self):
        """Should raise error when headroom insufficient."""
        mm = MemoryManager(device="cpu", vram_safety_threshold_gb=1.0)

        with patch.object(mm, "_get_vram_snapshot") as mock_snapshot:
            mock_snapshot.return_value = VRAMSnapshot(
                allocated_gb=15.0,
                reserved_gb=15.0,
                available_gb=0.5,  # Less than 1.0GB threshold
                state=MemoryState.IDLE,
            )

            with pytest.raises(
                InsufficientVRAMError, match="Insufficient VRAM"
            ):
                mm.validate_vram_headroom()


class TestMemoryManagerEstimation:
    """Test VRAM estimation for operations."""

    def test_estimate_peak_vram_florence2(self):
        """Florence-2 estimate should be ~8GB."""
        mm = MemoryManager(device="cpu")
        estimate = mm.estimate_peak_vram("florence2", (1024, 1024))
        assert estimate == 8.0

    def test_estimate_peak_vram_lama(self):
        """LaMa estimate should be ~2GB."""
        mm = MemoryManager(device="cpu")
        estimate = mm.estimate_peak_vram("lama", (1024, 1024))
        assert estimate == 2.0

    def test_estimate_peak_vram_flux(self):
        """Flux estimate should be ~12GB."""
        mm = MemoryManager(device="cpu")
        estimate = mm.estimate_peak_vram("flux", (1024, 1024))
        assert estimate == 12.0

    def test_estimate_scales_with_resolution(self):
        """Estimate should increase for >4K resolution."""
        mm = MemoryManager(device="cpu")

        estimate_1080 = mm.estimate_peak_vram("lama", (1080, 1920))
        estimate_4k = mm.estimate_peak_vram("lama", (2160, 4096))

        assert estimate_4k > estimate_1080  # 4K should require more VRAM

    def test_estimate_scales_down_for_small_images(self):
        """Estimate should decrease for <512×512 resolution."""
        mm = MemoryManager(device="cpu")

        estimate_1024 = mm.estimate_peak_vram("lama", (1024, 1024))
        estimate_256 = mm.estimate_peak_vram("lama", (256, 256))

        assert estimate_256 < estimate_1024  # Smaller should require less VRAM


class TestMemoryManagerModelTracking:
    """Test model load/unload and cleanup."""

    def test_load_model_registers_for_cleanup(self):
        """Loading model should register it for tracking."""
        mm = MemoryManager(device="cpu")
        mock_model = MagicMock()

        mm.load_model("lama", mock_model)

        assert "lama" in mm._loaded_models
        assert mm._loaded_models["lama"] is mock_model

    def test_unload_model_removes_tracking(self):
        """Unloading model should remove from tracking."""
        mm = MemoryManager(device="cpu")
        mock_model = MagicMock()

        mm.load_model("lama", mock_model)
        assert "lama" in mm._loaded_models

        result = mm.unload_model("lama")
        assert result is True
        assert "lama" not in mm._loaded_models

    def test_unload_nonexistent_model_returns_false(self):
        """Unloading non-loaded model should return False."""
        mm = MemoryManager(device="cpu")
        result = mm.unload_model("nonexistent")
        assert result is False

    def test_cleanup_all_clears_models(self):
        """Cleanup should remove all loaded models."""
        mm = MemoryManager(device="cpu")
        mock_model1 = MagicMock()
        mock_model2 = MagicMock()

        mm.load_model("lama", mock_model1)
        mm.load_model("flux", mock_model2)

        assert len(mm._loaded_models) == 2

        mm.cleanup_all()

        assert len(mm._loaded_models) == 0
        assert mm.state == MemoryState.IDLE

    def test_cleanup_all_resets_state(self):
        """Cleanup should reset state to IDLE."""
        mm = MemoryManager(device="cpu")
        mm.transition_to(MemoryState.DETECT_LOADING)

        mm.cleanup_all()

        assert mm.state == MemoryState.IDLE


class TestMemoryManagerStatus:
    """Test status reporting."""

    def test_get_status_reports_state(self):
        """Status should include current state."""
        mm = MemoryManager(device="cpu")
        mm.transition_to(MemoryState.DETECT_LOADING)

        status = mm.get_status()

        assert status["state"] == "detect_loading"
        assert status["device"] == "cpu"
        assert "allocated_gb" in status
        assert "reserved_gb" in status
        assert "available_gb" in status
        assert "loaded_models" in status

    def test_get_status_includes_loaded_models(self):
        """Status should list loaded models."""
        mm = MemoryManager(device="cpu")
        mock_model = MagicMock()

        mm.load_model("lama", mock_model)

        status = mm.get_status()
        assert "lama" in status["loaded_models"]


class TestMemoryManagerDeviceDetection:
    """Test device auto-detection."""

    def test_device_auto_defaults_to_cuda_if_available(self):
        """device='auto' should use CUDA if available."""
        mm = MemoryManager(device="auto")

        if torch.cuda.is_available():
            assert mm.device == "cuda"
        else:
            assert mm.device == "cpu"

    def test_device_explicit_cpu(self):
        """device='cpu' should force CPU."""
        mm = MemoryManager(device="cpu")
        assert mm.device == "cpu"

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_device_explicit_cuda(self):
        """device='cuda' should use GPU."""
        mm = MemoryManager(device="cuda")
        assert mm.device == "cuda"


class TestMemoryManagerIntegration:
    """Integration tests for full workflow."""

    def test_full_detection_workflow(self):
        """Test complete detection state transitions."""
        mm = MemoryManager(device="cpu", enable_monitoring=True)
        mock_model = MagicMock()

        # Workflow: IDLE → DETECT_LOADING → DETECTING → DETECT_CLEANUP → IDLE
        mm.transition_to(MemoryState.DETECT_LOADING)
        mm.validate_vram_headroom()  # Should pass
        mm.load_model("florence2", mock_model)

        mm.transition_to(MemoryState.DETECTING)
        # (simulated inference)

        mm.transition_to(MemoryState.DETECT_CLEANUP)
        mm.unload_model("florence2")

        mm.transition_to(MemoryState.IDLE)
        assert mm.state == MemoryState.IDLE
        assert len(mm._loaded_models) == 0

    def test_full_inpaint_workflow(self):
        """Test complete inpainting state transitions."""
        mm = MemoryManager(device="cpu", enable_monitoring=False)
        mock_lama = MagicMock()

        # Workflow: IDLE → INPAINT_LOADING → INFERRING → INPAINT_CLEANUP → IDLE
        mm.transition_to(MemoryState.INPAINT_LOADING)
        mm.load_model("lama", mock_lama)

        mm.transition_to(MemoryState.INFERRING)
        # (simulated inference)

        mm.transition_to(MemoryState.INPAINT_CLEANUP)
        mm.unload_model("lama")

        mm.transition_to(MemoryState.IDLE)
        assert mm.state == MemoryState.IDLE
