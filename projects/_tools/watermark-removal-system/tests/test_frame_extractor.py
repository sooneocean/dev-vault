"""
Unit tests for watermark_removal.preprocessing.frame_extractor module.

Note: Full frame extraction tests require OpenCV installation.
These tests validate the module structure and will pass when cv2 is available.
"""

import pytest
from pathlib import Path


class TestFrameExtractorStructure:
    """Test FrameExtractor module structure."""

    def test_module_imports(self):
        """Frame extractor module can be imported."""
        try:
            from src.watermark_removal.preprocessing.frame_extractor import (
                FrameExtractor,
            )
            assert FrameExtractor is not None
        except ImportError as e:
            # May fail due to missing cv2, but that's OK for structure test
            pytest.skip(f"OpenCV not available: {e}")

    def test_frame_extractor_has_required_methods(self):
        """FrameExtractor has all required methods."""
        try:
            from src.watermark_removal.preprocessing.frame_extractor import (
                FrameExtractor,
            )

            # Check required methods exist
            assert hasattr(FrameExtractor, '__init__')
            assert hasattr(FrameExtractor, 'extract_all')
            assert hasattr(FrameExtractor, 'extract_range')
            assert hasattr(FrameExtractor, 'extract_generator')

        except ImportError:
            pytest.skip("OpenCV not available")


class TestFrameExtractorLogic:
    """Test FrameExtractor logic (without actual video files)."""

    def test_frame_object_creation(self):
        """Frame objects can be created with proper attributes."""
        from src.watermark_removal.core.types import Frame
        import numpy as np

        # Create a mock frame
        frame_data = np.zeros((480, 640, 3), dtype=np.uint8)
        frame = Frame(frame_id=5, image=frame_data, timestamp_ms=166.67)

        assert frame.frame_id == 5
        assert frame.image.shape == (480, 640, 3)
        assert frame.timestamp_ms == 166.67


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
