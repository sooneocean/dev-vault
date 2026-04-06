"""
Frame deduplication and redundancy detection.

Prevents processing of duplicate or similar frames to reduce computational cost.
"""

import logging
import hashlib
from typing import Optional, Dict, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class SimilarityMetric(str, Enum):
    """Similarity metrics for frame comparison."""
    HASH = "hash"  # Exact hash match
    HISTOGRAM = "histogram"  # Color histogram similarity
    PERCEPTUAL = "perceptual"  # Perceptual hash (pHash)
    STRUCTURAL = "structural"  # Structural similarity (SSIM)


@dataclass
class DuplicateFrame:
    """Information about a duplicate frame."""
    original_frame_id: str
    duplicate_frame_id: str
    similarity_score: float  # 0.0 to 1.0
    metric_type: SimilarityMetric
    detected_at: datetime


class FrameDeduplicator:
    """Detect and track duplicate frames."""

    def __init__(
        self,
        similarity_threshold: float = 0.95,
        metric: SimilarityMetric = SimilarityMetric.HASH,
        max_history_size: int = 10000,
    ):
        self.similarity_threshold = similarity_threshold
        self.metric = metric
        self.max_history_size = max_history_size

        # Frame fingerprint cache
        self.frame_hashes: Dict[str, str] = {}
        self.frame_histogram: Dict[str, Dict[int, int]] = {}
        self.frame_phash: Dict[str, str] = {}

        # Duplicate tracking
        self.duplicates: list[DuplicateFrame] = []
        self.duplicate_count = 0
        self.original_count = 0

    def compute_frame_hash(self, frame_data: bytes) -> str:
        """Compute hash of frame data."""
        return hashlib.sha256(frame_data).hexdigest()

    def compute_histogram(self, frame_array) -> Dict[int, int]:
        """Compute color histogram of frame."""
        try:
            import numpy as np
            hist = {}
            for channel in range(3):  # BGR
                channel_data = frame_array[:, :, channel].flatten()
                for pixel in channel_data:
                    bucket = int(pixel) // 8  # 32 buckets per channel
                    hist[bucket] = hist.get(bucket, 0) + 1
            return hist
        except Exception as e:
            logger.error(f"Failed to compute histogram: {e}")
            return {}

    def compute_perceptual_hash(self, frame_array) -> Optional[str]:
        """Compute perceptual hash of frame."""
        try:
            import cv2
            import numpy as np

            # Resize to 8x8
            small = cv2.resize(frame_array, (8, 8))
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

            # Compute average
            avg = gray.mean()

            # Convert to hash
            phash = ""
            for pixel in gray.flatten():
                phash += "1" if pixel > avg else "0"

            return phash
        except Exception as e:
            logger.error(f"Failed to compute perceptual hash: {e}")
            return None

    def is_duplicate(
        self,
        frame_id: str,
        frame_data: bytes = None,
        frame_array=None,
    ) -> Tuple[bool, Optional[str], float]:
        """
        Check if frame is duplicate.

        Args:
            frame_id: Unique frame identifier
            frame_data: Raw frame data for hash comparison
            frame_array: Frame as numpy array for advanced comparison

        Returns:
            Tuple of (is_duplicate, original_frame_id, similarity_score)
        """
        if self.metric == SimilarityMetric.HASH:
            return self._check_hash_duplicate(frame_id, frame_data)
        elif self.metric == SimilarityMetric.HISTOGRAM:
            return self._check_histogram_duplicate(frame_id, frame_array)
        elif self.metric == SimilarityMetric.PERCEPTUAL:
            return self._check_perceptual_duplicate(frame_id, frame_array)
        else:
            return False, None, 0.0

    def _check_hash_duplicate(self, frame_id: str, frame_data: bytes) -> Tuple[bool, Optional[str], float]:
        """Check for exact hash match."""
        if frame_data is None:
            return False, None, 0.0

        frame_hash = self.compute_frame_hash(frame_data)

        # Check against existing hashes
        for existing_id, existing_hash in self.frame_hashes.items():
            if existing_hash == frame_hash:
                self.duplicate_count += 1
                self._record_duplicate(existing_id, frame_id, 1.0, SimilarityMetric.HASH)
                return True, existing_id, 1.0

        # Store new hash
        self.frame_hashes[frame_id] = frame_hash
        self.original_count += 1
        self._cleanup_old_hashes()
        return False, None, 0.0

    def _check_histogram_duplicate(self, frame_id: str, frame_array) -> Tuple[bool, Optional[str], float]:
        """Check for histogram similarity."""
        if frame_array is None:
            return False, None, 0.0

        hist = self.compute_histogram(frame_array)
        if not hist:
            return False, None, 0.0

        # Compare against existing histograms
        max_similarity = 0.0
        best_match = None

        for existing_id, existing_hist in self.frame_histogram.items():
            similarity = self._compare_histograms(hist, existing_hist)
            if similarity > max_similarity:
                max_similarity = similarity
                best_match = existing_id

        if max_similarity >= self.similarity_threshold:
            self.duplicate_count += 1
            self._record_duplicate(best_match, frame_id, max_similarity, SimilarityMetric.HISTOGRAM)
            return True, best_match, max_similarity

        # Store new histogram
        self.frame_histogram[frame_id] = hist
        self.original_count += 1
        self._cleanup_old_histograms()
        return False, None, 0.0

    def _check_perceptual_duplicate(self, frame_id: str, frame_array) -> Tuple[bool, Optional[str], float]:
        """Check for perceptual hash similarity."""
        if frame_array is None:
            return False, None, 0.0

        phash = self.compute_perceptual_hash(frame_array)
        if phash is None:
            return False, None, 0.0

        # Compare against existing pHashes (Hamming distance)
        max_similarity = 0.0
        best_match = None

        for existing_id, existing_phash in self.frame_phash.items():
            distance = self._hamming_distance(phash, existing_phash)
            similarity = 1.0 - (distance / 64.0)  # pHash is 64 bits

            if similarity > max_similarity:
                max_similarity = similarity
                best_match = existing_id

        if max_similarity >= self.similarity_threshold:
            self.duplicate_count += 1
            self._record_duplicate(best_match, frame_id, max_similarity, SimilarityMetric.PERCEPTUAL)
            return True, best_match, max_similarity

        # Store new pHash
        self.frame_phash[frame_id] = phash
        self.original_count += 1
        self._cleanup_old_phashes()
        return False, None, 0.0

    def _compare_histograms(self, hist1: Dict, hist2: Dict) -> float:
        """Compare two histograms (cosine similarity)."""
        if not hist1 or not hist2:
            return 0.0

        # Get all buckets
        all_buckets = set(hist1.keys()) | set(hist2.keys())

        # Compute dot product and magnitudes
        dot_product = 0.0
        mag1 = 0.0
        mag2 = 0.0

        for bucket in all_buckets:
            v1 = hist1.get(bucket, 0)
            v2 = hist2.get(bucket, 0)
            dot_product += v1 * v2
            mag1 += v1 * v1
            mag2 += v2 * v2

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 ** 0.5 * mag2 ** 0.5)

    @staticmethod
    def _hamming_distance(hash1: str, hash2: str) -> int:
        """Compute Hamming distance between two hashes."""
        if len(hash1) != len(hash2):
            return max(len(hash1), len(hash2))

        return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))

    def _record_duplicate(
        self,
        original_id: str,
        duplicate_id: str,
        similarity: float,
        metric: SimilarityMetric,
    ):
        """Record duplicate detection."""
        dup = DuplicateFrame(
            original_frame_id=original_id,
            duplicate_frame_id=duplicate_id,
            similarity_score=similarity,
            metric_type=metric,
            detected_at=datetime.now(timezone.utc),
        )
        self.duplicates.append(dup)

        # Keep only recent duplicates
        if len(self.duplicates) > self.max_history_size:
            self.duplicates = self.duplicates[-self.max_history_size // 2:]

        logger.debug(f"Duplicate detected: {original_id} ≈ {duplicate_id} ({similarity:.2%})")

    def _cleanup_old_hashes(self):
        """Remove old hashes to prevent memory overflow."""
        if len(self.frame_hashes) > self.max_history_size:
            # Keep most recent
            items = list(self.frame_hashes.items())
            self.frame_hashes = dict(items[-self.max_history_size // 2:])

    def _cleanup_old_histograms(self):
        """Remove old histograms."""
        if len(self.frame_histogram) > self.max_history_size:
            items = list(self.frame_histogram.items())
            self.frame_histogram = dict(items[-self.max_history_size // 2:])

    def _cleanup_old_phashes(self):
        """Remove old perceptual hashes."""
        if len(self.frame_phash) > self.max_history_size:
            items = list(self.frame_phash.items())
            self.frame_phash = dict(items[-self.max_history_size // 2:])

    def get_stats(self) -> Dict[str, any]:
        """Get deduplication statistics."""
        total = self.original_count + self.duplicate_count
        dedup_rate = (
            self.duplicate_count / total * 100 if total > 0 else 0.0
        )

        return {
            "total_frames": total,
            "original_frames": self.original_count,
            "duplicate_frames": self.duplicate_count,
            "deduplication_rate": dedup_rate,
            "metric_type": self.metric.value,
            "similarity_threshold": self.similarity_threshold,
            "recent_duplicates": len(self.duplicates),
        }

    def reset(self):
        """Reset deduplicator."""
        self.frame_hashes.clear()
        self.frame_histogram.clear()
        self.frame_phash.clear()
        self.duplicates.clear()
        self.duplicate_count = 0
        self.original_count = 0


class DeduplicationManager:
    """Manage frame deduplication across sessions."""

    def __init__(
        self,
        metric: SimilarityMetric = SimilarityMetric.HASH,
        similarity_threshold: float = 0.95,
    ):
        self.deduplicators: Dict[str, FrameDeduplicator] = {}
        self.metric = metric
        self.similarity_threshold = similarity_threshold

    def get_deduplicator(self, session_id: str) -> FrameDeduplicator:
        """Get or create deduplicator for session."""
        if session_id not in self.deduplicators:
            self.deduplicators[session_id] = FrameDeduplicator(
                similarity_threshold=self.similarity_threshold,
                metric=self.metric,
            )
        return self.deduplicators[session_id]

    def check_duplicate(
        self,
        session_id: str,
        frame_id: str,
        frame_data: bytes = None,
        frame_array=None,
    ) -> Tuple[bool, Optional[str], float]:
        """Check if frame is duplicate in session."""
        dedup = self.get_deduplicator(session_id)
        return dedup.is_duplicate(frame_id, frame_data, frame_array)

    def get_session_stats(self, session_id: str) -> Dict[str, any]:
        """Get deduplication stats for session."""
        if session_id in self.deduplicators:
            return self.deduplicators[session_id].get_stats()
        return {}

    def get_global_stats(self) -> Dict[str, any]:
        """Get global deduplication statistics."""
        total_original = sum(
            d.original_count for d in self.deduplicators.values()
        )
        total_duplicates = sum(
            d.duplicate_count for d in self.deduplicators.values()
        )
        total = total_original + total_duplicates

        return {
            "sessions": len(self.deduplicators),
            "total_frames": total,
            "total_original": total_original,
            "total_duplicates": total_duplicates,
            "global_dedup_rate": (
                total_duplicates / total * 100 if total > 0 else 0.0
            ),
        }

    def clear_session(self, session_id: str):
        """Clear deduplicator for session."""
        if session_id in self.deduplicators:
            del self.deduplicators[session_id]


# Global deduplication manager
dedup_manager: Optional[DeduplicationManager] = None


def init_deduplication(
    metric: SimilarityMetric = SimilarityMetric.HASH,
    similarity_threshold: float = 0.95,
):
    """Initialize global deduplication manager."""
    global dedup_manager
    dedup_manager = DeduplicationManager(metric, similarity_threshold)
    logger.info(f"Deduplication initialized: {metric.value}")


def get_dedup_manager() -> DeduplicationManager:
    """Get global deduplication manager."""
    global dedup_manager
    if dedup_manager is None:
        init_deduplication()
    return dedup_manager
