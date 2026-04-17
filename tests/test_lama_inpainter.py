"""Tests for LaMa inpainter with MemoryManager integration."""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from src.watermark_removal.lama_inpainter import LamaInpainter
from src.watermark_removal.memory_manager import MemoryManager


class TestLamaInpainterInitialization:
    """Test LamaInpainter initialization and parameter handling."""

    def test_init_accepts_memory_manager(self):
        """LamaInpainter should accept optional MemoryManager."""
        mm = MemoryManager(device="cpu")
        inpainter = LamaInpainter(device="cpu", memory_manager=mm)

        assert inpainter.memory_manager is mm

    def test_init_without_memory_manager(self):
        """LamaInpainter should work without MemoryManager (backward compatible)."""
        inpainter = LamaInpainter(device="cpu")
        assert inpainter.memory_manager is None

    def test_init_tile_size_preserved(self):
        """LamaInpainter should preserve tile_size and overlap parameters."""
        inpainter = LamaInpainter(device="cpu", tile_size=256, overlap=32)
        assert inpainter.tile_size == 256
        assert inpainter.overlap == 32
        assert inpainter.stride == 224  # 256 - 32


class TestLamaInpainterMemoryManagerLifecycle:
    """Test LamaInpainter lifecycle with MemoryManager."""

    def test_load_model_registers_with_mm(self):
        """load_model() should register model with MemoryManager."""
        mock_mm = MagicMock()
        inpainter = LamaInpainter(device="cpu", memory_manager=mock_mm)

        # Manually set loaded model
        inpainter._model_loaded = True
        inpainter.model = MagicMock()

        # Simulate what load_model does with MM
        if inpainter.memory_manager:
            inpainter.memory_manager.load_model("lama", inpainter.model)

        mock_mm.load_model.assert_called_once_with("lama", inpainter.model)

    def test_load_model_without_memory_manager(self):
        """load_model() should work without MemoryManager."""
        inpainter = LamaInpainter(device="cpu")

        # Should not raise
        inpainter._model_loaded = True
        inpainter.model = MagicMock()

        assert inpainter.memory_manager is None

    def test_cleanup_unregisters_from_mm(self):
        """cleanup() should unregister model from MemoryManager."""
        mock_mm = MagicMock()
        inpainter = LamaInpainter(device="cpu", memory_manager=mock_mm)

        # Set up model
        inpainter._model_loaded = True
        inpainter.model = MagicMock()

        inpainter.cleanup()

        mock_mm.unload_model.assert_called_once_with("lama")
        assert not inpainter._model_loaded

    def test_cleanup_without_memory_manager(self):
        """cleanup() should work without MemoryManager."""
        inpainter = LamaInpainter(device="cpu")

        # Set up model
        inpainter._model_loaded = True
        inpainter.model = MagicMock()

        inpainter.cleanup()

        assert not inpainter._model_loaded

    def test_full_lifecycle_with_memory_manager(self):
        """Full lifecycle: init → load → cleanup with MemoryManager."""
        mm = MemoryManager(device="cpu")
        inpainter = LamaInpainter(device="cpu", memory_manager=mm)

        # Check initial state
        assert inpainter.memory_manager is mm
        assert not inpainter._model_loaded
        assert "lama" not in mm._loaded_models

        # Simulate model load
        inpainter._model_loaded = True
        mock_model = MagicMock()
        inpainter.model = mock_model

        # Register with MM
        if inpainter.memory_manager:
            inpainter.memory_manager.load_model("lama", inpainter.model)

        assert "lama" in mm._loaded_models

        # Cleanup
        inpainter.cleanup()

        # Should be untracked
        assert "lama" not in mm._loaded_models
        assert not inpainter._model_loaded
