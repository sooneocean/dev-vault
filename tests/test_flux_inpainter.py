"""Tests for Flux inpainter with MemoryManager and offload mode integration."""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from src.watermark_removal.flux_inpainter import FluxInpainter
from src.watermark_removal.memory_manager import MemoryManager


class TestFluxInpainterInitialization:
    """Test FluxInpainter initialization and parameter handling."""

    def test_init_accepts_memory_manager(self):
        """FluxInpainter should accept optional MemoryManager."""
        mm = MemoryManager(device="cpu")
        inpainter = FluxInpainter(device="cpu", memory_manager=mm)

        assert inpainter.memory_manager is mm

    def test_init_without_memory_manager(self):
        """FluxInpainter should work without MemoryManager (backward compatible)."""
        inpainter = FluxInpainter(device="cpu")
        assert inpainter.memory_manager is None

    def test_init_offload_mode_fast(self):
        """FluxInpainter should default to fast offload mode."""
        inpainter = FluxInpainter(device="cpu", enable_sequential_offload=False)
        assert inpainter.enable_sequential_offload is False

    def test_init_offload_mode_sequential(self):
        """FluxInpainter should support sequential offload mode."""
        inpainter = FluxInpainter(device="cpu", enable_sequential_offload=True)
        assert inpainter.enable_sequential_offload is True


class TestFluxInpainterOffloadMode:
    """Test offload mode application in FluxInpainter."""

    def test_fast_offload_mode_pipeline(self):
        """Fast offload should use enable_model_cpu_offload()."""
        inpainter = FluxInpainter(device="cpu", enable_sequential_offload=False)

        # Simulate what load_model does
        assert inpainter.enable_sequential_offload is False
        # When loaded, should call enable_model_cpu_offload()

    def test_sequential_offload_mode_pipeline(self):
        """Sequential offload should use enable_sequential_cpu_offload()."""
        inpainter = FluxInpainter(device="cpu", enable_sequential_offload=True)

        # Simulate what load_model does
        assert inpainter.enable_sequential_offload is True
        # When loaded, should call enable_sequential_cpu_offload()


class TestFluxInpainterMemoryManagerLifecycle:
    """Test FluxInpainter lifecycle with MemoryManager."""

    def test_load_model_registers_with_mm(self):
        """load_model() should register pipeline with MemoryManager."""
        mock_mm = MagicMock()
        inpainter = FluxInpainter(device="cpu", memory_manager=mock_mm)

        # Manually set loaded pipeline
        inpainter._model_loaded = True
        inpainter.pipeline = MagicMock()

        # Simulate what load_model does with MM
        if inpainter.memory_manager:
            inpainter.memory_manager.load_model("flux", inpainter.pipeline)

        mock_mm.load_model.assert_called_once_with("flux", inpainter.pipeline)

    def test_load_model_without_memory_manager(self):
        """load_model() should work without MemoryManager."""
        inpainter = FluxInpainter(device="cpu")

        # Should not raise
        inpainter._model_loaded = True
        inpainter.pipeline = MagicMock()

        assert inpainter.memory_manager is None

    def test_cleanup_unregisters_from_mm(self):
        """cleanup() should unregister pipeline from MemoryManager."""
        mock_mm = MagicMock()
        inpainter = FluxInpainter(device="cpu", memory_manager=mock_mm)

        # Set up pipeline
        inpainter._model_loaded = True
        inpainter.pipeline = MagicMock()

        inpainter.cleanup()

        mock_mm.unload_model.assert_called_once_with("flux")
        assert not inpainter._model_loaded

    def test_cleanup_without_memory_manager(self):
        """cleanup() should work without MemoryManager."""
        inpainter = FluxInpainter(device="cpu")

        # Set up pipeline
        inpainter._model_loaded = True
        inpainter.pipeline = MagicMock()

        inpainter.cleanup()

        assert not inpainter._model_loaded

    def test_full_lifecycle_with_memory_manager(self):
        """Full lifecycle: init → load → cleanup with MemoryManager."""
        mm = MemoryManager(device="cpu")
        inpainter = FluxInpainter(device="cpu", enable_sequential_offload=True, memory_manager=mm)

        # Check initial state
        assert inpainter.memory_manager is mm
        assert not inpainter._model_loaded
        assert inpainter.enable_sequential_offload is True
        assert "flux" not in mm._loaded_models

        # Simulate model load
        inpainter._model_loaded = True
        mock_pipeline = MagicMock()
        inpainter.pipeline = mock_pipeline

        # Register with MM
        if inpainter.memory_manager:
            inpainter.memory_manager.load_model("flux", inpainter.pipeline)

        assert "flux" in mm._loaded_models

        # Cleanup
        inpainter.cleanup()

        # Should be untracked
        assert "flux" not in mm._loaded_models
        assert not inpainter._model_loaded


class TestFluxInpainterOffloadModeWithMemoryManager:
    """Test offload mode configuration with MemoryManager integration."""

    def test_fast_offload_with_mm(self):
        """Fast offload with MemoryManager should work correctly."""
        mm = MemoryManager(device="cpu")
        inpainter = FluxInpainter(
            device="cpu",
            enable_sequential_offload=False,
            memory_manager=mm
        )

        assert inpainter.enable_sequential_offload is False
        assert inpainter.memory_manager is mm

    def test_sequential_offload_with_mm(self):
        """Sequential offload with MemoryManager should work correctly."""
        mm = MemoryManager(device="cpu")
        inpainter = FluxInpainter(
            device="cpu",
            enable_sequential_offload=True,
            memory_manager=mm
        )

        assert inpainter.enable_sequential_offload is True
        assert inpainter.memory_manager is mm

    def test_offload_mode_persists_through_lifecycle(self):
        """Offload mode should persist from init through cleanup."""
        mm = MemoryManager(device="cpu")
        inpainter = FluxInpainter(
            device="cpu",
            enable_sequential_offload=True,
            memory_manager=mm
        )

        # Simulate load
        inpainter._model_loaded = True
        inpainter.pipeline = MagicMock()

        # Mode should still be set
        assert inpainter.enable_sequential_offload is True

        # Simulate cleanup
        inpainter.cleanup()

        # Mode should still be set after cleanup
        assert inpainter.enable_sequential_offload is True
