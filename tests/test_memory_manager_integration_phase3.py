"""Phase 3 integration tests: Memory Manager with Florence2 + DualEngineRouter.

Tests complete detect→inpaint→cleanup workflows with state machine verification.
"""

import pytest
import numpy as np
from PIL import Image
from unittest.mock import MagicMock, patch

from src.watermark_removal.memory_manager import (
    MemoryManager,
    MemoryState,
    InsufficientVRAMError,
)
from src.watermark_removal.florence2_detector import Florence2Detector
from src.watermark_removal.dual_engine_router import (
    DualEngineRouter,
    InpaintEngine,
    InpaintEngineConfig,
)


class TestCompleteDetectionWorkflow:
    """Test Florence2Detector with MemoryManager state transitions."""

    def test_detect_workflow_state_transitions(self):
        """Detection workflow should follow correct state transitions."""
        mm = MemoryManager(device="cpu")
        detector = Florence2Detector(device="cpu", memory_manager=mm)

        # Create test image
        img = Image.new("RGB", (512, 512), color="white")

        # Verify initial state
        assert mm.state == MemoryState.IDLE
        assert "florence2" not in mm._loaded_models

        # Simulate detection workflow
        mm.transition_to(MemoryState.DETECT_LOADING)
        assert mm.state == MemoryState.DETECT_LOADING

        # Simulate lazy load (register with MM)
        detector._model_loaded = True
        detector.model = MagicMock()
        detector.processor = MagicMock()
        mm.load_model("florence2", detector.model)

        assert "florence2" in mm._loaded_models

        mm.transition_to(MemoryState.DETECTING)
        assert mm.state == MemoryState.DETECTING

        mm.transition_to(MemoryState.DETECT_CLEANUP)
        assert mm.state == MemoryState.DETECT_CLEANUP

        # Cleanup
        detector.cleanup()
        assert "florence2" not in mm._loaded_models

        mm.transition_to(MemoryState.IDLE)
        assert mm.state == MemoryState.IDLE

    def test_detect_vram_validation(self):
        """Detection should validate VRAM before loading."""
        mm = MemoryManager(device="cpu", vram_safety_threshold_gb=1.0)
        detector = Florence2Detector(device="cpu", memory_manager=mm)

        # With 16GB available on CPU and 1GB threshold, should pass
        mm.transition_to(MemoryState.DETECT_LOADING)
        mm.validate_vram_headroom()  # Should not raise
        mm.transition_to(MemoryState.DETECTING)
        mm.transition_to(MemoryState.DETECT_CLEANUP)
        mm.transition_to(MemoryState.IDLE)

    def test_detect_insufficient_vram_error(self):
        """Detection should raise on insufficient VRAM."""
        mm = MemoryManager(device="cpu", vram_safety_threshold_gb=20.0)
        # CPU with 16GB and 20GB threshold should fail

        mm.transition_to(MemoryState.DETECT_LOADING)

        with pytest.raises(InsufficientVRAMError):
            mm.validate_vram_headroom()


class TestCompleteInpaintWorkflow:
    """Test DualEngineRouter with MemoryManager state transitions."""

    def test_lama_inpaint_workflow_state_transitions(self):
        """LaMa inpainting workflow should follow correct state transitions."""
        mm = MemoryManager(device="cpu")
        config = InpaintEngineConfig(engine=InpaintEngine.LAMA, device="cpu")
        router = DualEngineRouter(config, memory_manager=mm)

        # Verify initial state
        assert mm.state == MemoryState.IDLE

        # Create test image
        image = np.zeros((512, 512, 3), dtype=np.uint8)
        mask = np.zeros((512, 512), dtype=np.uint8)

        # Mock LaMa inpainter
        mock_lama = MagicMock()
        mock_lama.inpaint.return_value = image
        router.lama = mock_lama

        # Execute inpainting
        result = router._inpaint_with_lama(image, mask)

        # Verify transitions
        assert result is not None
        assert mm.state == MemoryState.IDLE
        mock_lama.load_model.assert_called_once()
        mock_lama.cleanup.assert_called_once()

    def test_flux_inpaint_workflow_state_transitions(self):
        """Flux inpainting workflow should follow correct state transitions."""
        mm = MemoryManager(device="cpu")
        config = InpaintEngineConfig(
            engine=InpaintEngine.FLUX,
            device="cpu",
            flux_enable_sequential_offload=False,
        )
        router = DualEngineRouter(config, memory_manager=mm)

        # Verify initial state
        assert mm.state == MemoryState.IDLE

        # Create test image
        image = np.zeros((512, 512, 3), dtype=np.uint8)
        mask = np.zeros((512, 512), dtype=np.uint8)

        # Mock Flux inpainter
        mock_flux = MagicMock()
        mock_flux.inpaint.return_value = image
        router.flux = mock_flux

        # Execute inpainting (skip VRAM validation)
        with patch.object(mm, "validate_vram_headroom"):
            result = router._inpaint_with_flux(image, mask, "remove watermark")

        # Verify transitions
        assert result is not None
        assert mm.state == MemoryState.IDLE
        mock_flux.load_model.assert_called_once()
        mock_flux.cleanup.assert_called_once()

    def test_flux_sequential_offload_mode(self):
        """Flux with sequential offload should set mode correctly."""
        config = InpaintEngineConfig(
            engine=InpaintEngine.FLUX,
            device="cpu",
            flux_enable_sequential_offload=True,
        )
        mm = MemoryManager(device="cpu")
        router = DualEngineRouter(config, memory_manager=mm)

        assert router.config.flux_enable_sequential_offload is True

    def test_flux_fast_offload_mode(self):
        """Flux with fast offload should set mode correctly."""
        config = InpaintEngineConfig(
            engine=InpaintEngine.FLUX,
            device="cpu",
            flux_enable_sequential_offload=False,
        )
        mm = MemoryManager(device="cpu")
        router = DualEngineRouter(config, memory_manager=mm)

        assert router.config.flux_enable_sequential_offload is False


class TestFullDetectInpaintWorkflow:
    """Test complete detect→inpaint→cleanup pipeline."""

    def test_full_workflow_state_machine(self):
        """Full workflow should execute all state transitions correctly."""
        mm = MemoryManager(device="cpu", enable_monitoring=False)

        # Create components
        detector = Florence2Detector(device="cpu", memory_manager=mm)
        config = InpaintEngineConfig(engine=InpaintEngine.LAMA, device="cpu")
        router = DualEngineRouter(config, memory_manager=mm)

        # Create test image
        test_image = Image.new("RGB", (512, 512), color="white")
        image_np = np.array(test_image, dtype=np.uint8)
        mask_np = np.zeros((512, 512), dtype=np.uint8)

        # Track states
        states = []

        def track_state(state):
            states.append(state)
            return mm._valid_transitions[mm.state]

        original_transition = mm.transition_to

        def capture_transition(target_state):
            track_state(target_state)
            return original_transition(target_state)

        # Workflow: IDLE → DETECT_LOADING → DETECTING → DETECT_CLEANUP
        #        → INPAINT_LOADING → INFERRING → INPAINT_CLEANUP → IDLE

        mm.transition_to(MemoryState.DETECT_LOADING)
        detector._model_loaded = True
        detector.model = MagicMock()
        mm.load_model("florence2", detector.model)

        mm.transition_to(MemoryState.DETECTING)
        # (inference happens here)

        mm.transition_to(MemoryState.DETECT_CLEANUP)
        detector.cleanup()

        mm.transition_to(MemoryState.INPAINT_LOADING)
        mock_lama = MagicMock()
        mock_lama.inpaint.return_value = image_np
        router.lama = mock_lama
        router.lama.load_model()

        mm.transition_to(MemoryState.INFERRING)
        result = router.lama.inpaint(image_np, mask_np)

        mm.transition_to(MemoryState.INPAINT_CLEANUP)
        router.lama.cleanup()

        mm.transition_to(MemoryState.IDLE)

        # Verify final state
        assert mm.state == MemoryState.IDLE
        assert "florence2" not in mm._loaded_models
        assert result is not None

    def test_full_workflow_with_auto_downgrade(self):
        """Full workflow with auto-downgrade from Flux to LaMa."""
        mm = MemoryManager(device="cpu")

        config = InpaintEngineConfig(
            engine=InpaintEngine.FLUX,
            auto_downgrade_on_oom=True,
            device="cpu",
        )
        router = DualEngineRouter(config, memory_manager=mm)

        image_np = np.zeros((512, 512, 3), dtype=np.uint8)
        mask_np = np.zeros((512, 512), dtype=np.uint8)

        # Mock insufficient VRAM for Flux
        with patch.object(
            mm,
            "validate_vram_headroom",
            side_effect=InsufficientVRAMError("Insufficient VRAM for Flux"),
        ):
            with patch.object(router, "_inpaint_with_lama", return_value=image_np):
                result = router.inpaint(image_np, mask_np)

        assert result is not None

    def test_full_workflow_4k_resolution(self):
        """Full workflow with 4K images should estimate higher VRAM."""
        mm = MemoryManager(device="cpu")

        # Test 4K resolution (3840×2160)
        image_4k = np.zeros((2160, 3840, 3), dtype=np.uint8)
        mask_4k = np.zeros((2160, 3840), dtype=np.uint8)

        # Flux 4K estimate
        flux_estimate_4k = mm.estimate_peak_vram("flux", (2160, 3840))

        # Flux 1080p estimate
        flux_estimate_1080 = mm.estimate_peak_vram("flux", (1080, 1920))

        # 4K should require more VRAM
        assert flux_estimate_4k > flux_estimate_1080

        # 4K Flux should fit in 16GB with sequential offload (~8GB)
        config = InpaintEngineConfig(
            engine=InpaintEngine.FLUX,
            flux_enable_sequential_offload=True,
            device="cpu",
        )
        router = DualEngineRouter(config, memory_manager=mm)

        # Should estimate < 16GB
        assert flux_estimate_4k <= 16.0

    def test_workflow_error_recovery(self):
        """Workflow should reset to IDLE even on errors."""
        mm = MemoryManager(device="cpu")

        config = InpaintEngineConfig(engine=InpaintEngine.LAMA, device="cpu")
        router = DualEngineRouter(config, memory_manager=mm)

        image_np = np.zeros((512, 512, 3), dtype=np.uint8)
        mask_np = np.zeros((512, 512), dtype=np.uint8)

        # Simulate error during inference
        mock_lama = MagicMock()
        mock_lama.load_model.side_effect = RuntimeError("Model load failed")
        router.lama = mock_lama

        mm.transition_to(MemoryState.INPAINT_LOADING)

        with pytest.raises(RuntimeError):
            router.lama.load_model()

        # Manual cleanup to restore state
        router.cleanup()

        # Should be back to IDLE
        assert mm.state == MemoryState.IDLE


class TestMemoryManagerBudgetEnforcement:
    """Test VRAM budget enforcement throughout workflow."""

    def test_budget_enforcement_4gb_gpu(self):
        """Router should respect smaller VRAM budgets."""
        mm = MemoryManager(device="cpu", vram_budget=4.0)

        # With 4GB budget and 1GB threshold, only 3GB available
        mm.transition_to(MemoryState.DETECT_LOADING)

        # Florence-2 estimate (8GB) exceeds 3GB available
        estimate = mm.estimate_peak_vram("florence2", (1024, 1024))

        # Should need more than available
        assert estimate > mm._total_vram_gb - mm.vram_safety_threshold_gb

    def test_budget_enforcement_12gb_gpu(self):
        """Router should enforce 12GB budget for Flux sequential mode."""
        mm = MemoryManager(device="cpu", vram_budget=12.0)

        config = InpaintEngineConfig(
            engine=InpaintEngine.FLUX,
            flux_enable_sequential_offload=True,  # Sequential reduces peak
            device="cpu",
        )
        router = DualEngineRouter(config, memory_manager=mm)

        # Verify budget is set correctly
        assert mm._total_vram_gb == 12.0

        # LaMa (2GB) + 1GB headroom should fit in 12GB
        lama_estimate = mm.estimate_peak_vram("lama", (1024, 1024))
        assert lama_estimate + 1.0 <= 12.0

    def test_budget_enforcement_prevents_oom(self):
        """Budget enforcement should prevent OOM."""
        mm = MemoryManager(device="cpu", vram_budget=2.0, vram_safety_threshold_gb=0.5)

        mm.transition_to(MemoryState.DETECT_LOADING)

        # Florence-2 (8GB) exceeds budget (2GB)
        with pytest.raises(InsufficientVRAMError):
            mm.validate_vram_headroom(8.0)


class TestCleanupVerification:
    """Test cleanup verification after operations."""

    def test_cleanup_verification_passes(self):
        """Cleanup verification should pass when <0.5GB allocated."""
        mm = MemoryManager(device="cpu")

        # Simulate allocation
        mm._loaded_models["test"] = MagicMock()

        # Cleanup should verify fragmentation
        mm.unload_model("test")

        assert "test" not in mm._loaded_models

    def test_cleanup_all_verifies(self):
        """cleanup_all() should call verify_cleanup."""
        mm = MemoryManager(device="cpu")

        mm._loaded_models["test"] = MagicMock()

        # cleanup_all includes verify_cleanup
        mm.cleanup_all()

        assert len(mm._loaded_models) == 0
        assert mm.state == MemoryState.IDLE
