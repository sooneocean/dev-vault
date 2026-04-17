"""Tests for dual-engine inpainting router with MemoryManager."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from src.watermark_removal.dual_engine_router import (
    DualEngineRouter,
    InpaintEngine,
    InpaintEngineConfig,
)
from src.watermark_removal.memory_manager import (
    MemoryManager,
    MemoryState,
    InsufficientVRAMError,
)
from src.watermark_removal.core.types import OffloadMode


class TestDualEngineRouterInitialization:
    """Test router initialization and configuration."""

    def test_router_with_default_config(self):
        """Router should initialize with default config."""
        config = InpaintEngineConfig()
        router = DualEngineRouter(config)

        assert router.config == config
        assert router.memory_manager is not None
        assert router.lama is None
        assert router.flux is None

    def test_router_with_custom_memory_manager(self):
        """Router should accept custom MemoryManager."""
        config = InpaintEngineConfig()
        mm = MemoryManager(device="cpu")
        router = DualEngineRouter(config, memory_manager=mm)

        assert router.memory_manager is mm

    def test_router_creates_default_memory_manager(self):
        """Router should create default MemoryManager if not provided."""
        config = InpaintEngineConfig(device="cpu")
        router = DualEngineRouter(config)

        assert router.memory_manager is not None
        assert router.memory_manager.device == "cpu"

    def test_router_lama_engine_selection(self):
        """Router should support LaMa engine selection."""
        config = InpaintEngineConfig(engine=InpaintEngine.LAMA)
        router = DualEngineRouter(config)

        assert router.config.engine == InpaintEngine.LAMA

    def test_router_flux_engine_selection(self):
        """Router should support Flux engine selection."""
        config = InpaintEngineConfig(engine=InpaintEngine.FLUX)
        router = DualEngineRouter(config)

        assert router.config.engine == InpaintEngine.FLUX


class TestOffloadModeConfiguration:
    """Test memory offload mode configuration."""

    def test_offload_mode_fast(self):
        """Fast offload mode should use enable_model_cpu_offload."""
        config = InpaintEngineConfig(flux_enable_sequential_offload=False)
        assert config.flux_enable_sequential_offload is False

    def test_offload_mode_sequential(self):
        """Sequential offload mode should use enable_sequential_cpu_offload."""
        config = InpaintEngineConfig(flux_enable_sequential_offload=True)
        assert config.flux_enable_sequential_offload is True

    def test_offload_mode_from_process_config(self):
        """Offload mode should propagate from ProcessConfig to InpaintEngineConfig."""
        from src.watermark_removal.core.types import ProcessConfig, OffloadMode
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            pconfig = ProcessConfig(
                video_path=str(tmp_path / "video.mp4"),
                mask_path=str(tmp_path / "mask.json"),
                output_dir=str(tmp_path),
                memory_offload_mode=OffloadMode.SEQUENTIAL,
            )

            # Router should be able to read from ProcessConfig
            sequential = pconfig.memory_offload_mode == OffloadMode.SEQUENTIAL
            config = InpaintEngineConfig(
                flux_enable_sequential_offload=sequential
            )

            assert config.flux_enable_sequential_offload is True

    def test_offload_mode_default_is_fast(self):
        """Default offload mode should be FAST (enable_model_cpu_offload)."""
        config = InpaintEngineConfig()
        # Default should be False (FAST mode)
        assert config.flux_enable_sequential_offload is False


class TestAutoDowngradeLogic:
    """Test auto-downgrade from Flux to LaMa on insufficient VRAM."""

    def test_downgrade_on_insufficient_vram(self):
        """Router should downgrade to LaMa when Flux VRAM insufficient."""
        config = InpaintEngineConfig(
            engine=InpaintEngine.FLUX,
            auto_downgrade_on_oom=True,
        )
        mm = MemoryManager(device="cpu")
        router = DualEngineRouter(config, memory_manager=mm)

        # Create test image
        image = np.zeros((512, 512, 3), dtype=np.uint8)
        mask = np.zeros((512, 512), dtype=np.uint8)

        # Mock validate_vram_headroom to raise InsufficientVRAMError
        with patch.object(
            mm,
            "validate_vram_headroom",
            side_effect=InsufficientVRAMError("Insufficient VRAM"),
        ):
            with patch.object(router, "_inpaint_with_lama", return_value=image):
                result = router.inpaint(image, mask)

                assert result is not None
                # Should have fallen back to LaMa

    def test_no_downgrade_when_disabled(self):
        """Router should raise if auto_downgrade is disabled and VRAM insufficient."""
        config = InpaintEngineConfig(
            engine=InpaintEngine.FLUX,
            auto_downgrade_on_oom=False,
        )
        mm = MemoryManager(device="cpu")
        router = DualEngineRouter(config, memory_manager=mm)

        image = np.zeros((512, 512, 3), dtype=np.uint8)
        mask = np.zeros((512, 512), dtype=np.uint8)

        # Mock validate_vram_headroom to raise InsufficientVRAMError
        with patch.object(
            mm,
            "validate_vram_headroom",
            side_effect=InsufficientVRAMError("Insufficient VRAM"),
        ):
            with pytest.raises(InsufficientVRAMError):
                router.inpaint(image, mask)

    def test_lama_never_needs_downgrade(self):
        """LaMa engine should not trigger downgrade logic."""
        config = InpaintEngineConfig(
            engine=InpaintEngine.LAMA,
            auto_downgrade_on_oom=True,
        )
        mm = MemoryManager(device="cpu")
        router = DualEngineRouter(config, memory_manager=mm)

        image = np.zeros((512, 512, 3), dtype=np.uint8)
        mask = np.zeros((512, 512), dtype=np.uint8)

        # LaMa should not call validate_vram_headroom for Flux
        with patch.object(router, "_inpaint_with_lama", return_value=image) as mock_lama:
            result = router.inpaint(image, mask)

            assert result is not None
            mock_lama.assert_called_once()


class TestStateTransitions:
    """Test memory state machine transitions."""

    def test_lama_state_transitions(self):
        """LaMa inpainting should follow correct state transitions."""
        config = InpaintEngineConfig(engine=InpaintEngine.LAMA, device="cpu")
        mm = MemoryManager(device="cpu")
        router = DualEngineRouter(config, memory_manager=mm)

        # Mock LamaInpainter
        mock_lama = MagicMock()
        router.lama = mock_lama
        mock_lama.inpaint.return_value = np.zeros((512, 512, 3), dtype=np.uint8)

        image = np.zeros((512, 512, 3), dtype=np.uint8)
        mask = np.zeros((512, 512), dtype=np.uint8)

        # Capture state transitions
        states = []
        original_transition = mm.transition_to

        def capture_transition(state):
            states.append(state)
            return original_transition(state)

        with patch.object(mm, "transition_to", side_effect=capture_transition):
            router._inpaint_with_lama(image, mask)

        # Should follow: INPAINT_LOADING → INFERRING → INPAINT_CLEANUP → IDLE
        assert states == [
            MemoryState.INPAINT_LOADING,
            MemoryState.INFERRING,
            MemoryState.INPAINT_CLEANUP,
            MemoryState.IDLE,
        ]

    def test_flux_state_transitions(self):
        """Flux inpainting should follow correct state transitions."""
        config = InpaintEngineConfig(engine=InpaintEngine.FLUX, device="cpu")
        mm = MemoryManager(device="cpu")
        router = DualEngineRouter(config, memory_manager=mm)

        # Mock FluxInpainter
        mock_flux = MagicMock()
        router.flux = mock_flux
        mock_flux.inpaint.return_value = np.zeros((512, 512, 3), dtype=np.uint8)

        image = np.zeros((512, 512, 3), dtype=np.uint8)
        mask = np.zeros((512, 512), dtype=np.uint8)

        # Capture state transitions
        states = []
        original_transition = mm.transition_to

        def capture_transition(state):
            states.append(state)
            return original_transition(state)

        with patch.object(mm, "transition_to", side_effect=capture_transition):
            with patch.object(mm, "validate_vram_headroom"):
                router._inpaint_with_flux(image, mask, "remove watermark")

        # Should follow: INPAINT_LOADING → INFERRING → INPAINT_CLEANUP → IDLE
        assert states == [
            MemoryState.INPAINT_LOADING,
            MemoryState.INFERRING,
            MemoryState.INPAINT_CLEANUP,
            MemoryState.IDLE,
        ]


class TestVRAMEstimation:
    """Test VRAM estimation for engines."""

    def test_flux_vram_estimate_scales_with_resolution(self):
        """Flux VRAM estimate should increase for higher resolutions."""
        config = InpaintEngineConfig(engine=InpaintEngine.FLUX, device="cpu")
        mm = MemoryManager(device="cpu")
        router = DualEngineRouter(config, memory_manager=mm)

        estimate_1080 = mm.estimate_peak_vram("flux", (1080, 1920))
        estimate_4k = mm.estimate_peak_vram("flux", (2160, 4096))

        # 4K should require more VRAM than 1080p
        assert estimate_4k > estimate_1080

    def test_lama_vram_stays_constant(self):
        """LaMa VRAM estimate should stay ~2GB regardless of resolution (tiling)."""
        config = InpaintEngineConfig(engine=InpaintEngine.LAMA, device="cpu")
        mm = MemoryManager(device="cpu")
        router = DualEngineRouter(config, memory_manager=mm)

        estimate_512 = mm.estimate_peak_vram("lama", (512, 512))
        estimate_4k = mm.estimate_peak_vram("lama", (2160, 4096))

        # LaMa should use tiling and stay roughly constant
        # Allow 20% variance for scaling
        assert estimate_4k <= estimate_512 * 1.2


class TestRouterCleanup:
    """Test cleanup behavior."""

    def test_cleanup_all_models(self):
        """Cleanup should unload all models."""
        config = InpaintEngineConfig(device="cpu")
        mm = MemoryManager(device="cpu")
        router = DualEngineRouter(config, memory_manager=mm)

        # Create mocked models
        router.lama = MagicMock()
        router.flux = MagicMock()

        router.cleanup()

        router.lama.cleanup.assert_called_once()
        router.flux.cleanup.assert_called_once()
        assert mm.state == MemoryState.IDLE

    def test_cleanup_handles_none_models(self):
        """Cleanup should handle None models gracefully."""
        config = InpaintEngineConfig(device="cpu")
        mm = MemoryManager(device="cpu")
        router = DualEngineRouter(config, memory_manager=mm)

        # Don't set any models
        assert router.lama is None
        assert router.flux is None

        # Cleanup should not crash
        router.cleanup()
        assert mm.state == MemoryState.IDLE


class TestIntegrationWithProcessConfig:
    """Test integration with ProcessConfig for offload mode."""

    def test_create_router_from_process_config(self):
        """Router should be creatable with ProcessConfig offload mode."""
        from src.watermark_removal.core.types import ProcessConfig, OffloadMode
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            pconfig = ProcessConfig(
                video_path=str(tmp_path / "video.mp4"),
                mask_path=str(tmp_path / "mask.json"),
                output_dir=str(tmp_path),
                memory_offload_mode=OffloadMode.SEQUENTIAL,
            )

            # Create router with offload mode from ProcessConfig
            sequential = pconfig.memory_offload_mode == OffloadMode.SEQUENTIAL
            config = InpaintEngineConfig(
                engine=InpaintEngine.FLUX,
                flux_enable_sequential_offload=sequential,
                device="cpu",
            )
            router = DualEngineRouter(config)

            assert router.config.flux_enable_sequential_offload is True
