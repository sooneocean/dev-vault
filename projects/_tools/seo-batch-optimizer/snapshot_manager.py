"""
Snapshot Manager - Version control for WordPress.com posts
Provides git-like backup/restore capability for rollback safety
"""

import json
import os
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class SnapshotManager:
    """
    Manages post snapshots for rollback capability.
    Stores snapshots in .snapshots/ directory with metadata.
    """

    def __init__(self, snapshot_dir: str = ".snapshots"):
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(exist_ok=True)
        self.index_file = self.snapshot_dir / "index.json"
        self._load_index()

    def _load_index(self) -> None:
        """Load snapshot index from disk"""
        if self.index_file.exists():
            with open(self.index_file, "r", encoding="utf-8") as f:
                self.index = json.load(f)
        else:
            self.index = {}

    def _save_index(self) -> None:
        """Persist snapshot index to disk"""
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)

    def _compute_hash(self, data: Dict) -> str:
        """Compute SHA256 hash of post data for integrity check"""
        json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def create_snapshot(
        self,
        post_id: int,
        post_data: Dict,
        batch_id: str = None,
        description: str = None,
    ) -> str:
        """
        Create a snapshot of a post before modification.

        Args:
            post_id: WordPress post ID
            post_data: Full post data dict (title, excerpt, content, etc)
            batch_id: Optional batch identifier (e.g., "batch-001")
            description: Optional snapshot description

        Returns:
            snapshot_id: Unique snapshot identifier
        """
        timestamp = datetime.utcnow().isoformat()
        snapshot_id = f"post-{post_id}-{timestamp.replace(':', '').replace('.', '')}"

        snapshot_data = {
            "post_id": post_id,
            "snapshot_id": snapshot_id,
            "timestamp": timestamp,
            "batch_id": batch_id,
            "description": description,
            "hash": self._compute_hash(post_data),
            "data": {
                "id": post_data.get("id"),
                "title": post_data.get("title"),
                "excerpt": post_data.get("excerpt"),
                "content": post_data.get("content"),
                "featured_image": post_data.get("featured_image"),
                "meta": post_data.get("meta", {}),
                "categories": post_data.get("categories", []),
                "tags": post_data.get("tags", []),
            },
        }

        # Save snapshot file
        snapshot_file = self.snapshot_dir / f"{snapshot_id}.json"
        with open(snapshot_file, "w", encoding="utf-8") as f:
            json.dump(snapshot_data, f, indent=2, ensure_ascii=False)

        # Update index
        self.index[snapshot_id] = {
            "post_id": post_id,
            "batch_id": batch_id,
            "timestamp": timestamp,
            "hash": snapshot_data["hash"],
            "status": "created",
        }
        self._save_index()

        logger.info(f"Created snapshot: {snapshot_id} for post {post_id}")
        return snapshot_id

    def create_batch_snapshots(
        self, posts: List[Dict], batch_id: str = None
    ) -> List[str]:
        """
        Create snapshots for multiple posts in a batch.

        Args:
            posts: List of post data dicts
            batch_id: Batch identifier

        Returns:
            List of snapshot IDs
        """
        snapshot_ids = []
        for post in posts:
            snapshot_id = self.create_snapshot(
                post_id=post.get("id"),
                post_data=post,
                batch_id=batch_id,
                description=f"Pre-batch snapshot",
            )
            snapshot_ids.append(snapshot_id)
        return snapshot_ids

    def restore_snapshot(self, snapshot_id: str, verify_hash: bool = True) -> Dict:
        """
        Restore post data from a snapshot.

        Args:
            snapshot_id: Snapshot identifier
            verify_hash: Verify data integrity using stored hash

        Returns:
            Restored post data dict

        Raises:
            FileNotFoundError: Snapshot not found
            ValueError: Hash mismatch (data corruption detected)
        """
        snapshot_file = self.snapshot_dir / f"{snapshot_id}.json"

        if not snapshot_file.exists():
            raise FileNotFoundError(f"Snapshot not found: {snapshot_id}")

        with open(snapshot_file, "r", encoding="utf-8") as f:
            snapshot_data = json.load(f)

        # Verify integrity
        if verify_hash:
            current_hash = self._compute_hash(snapshot_data["data"])
            if current_hash != snapshot_data["hash"]:
                raise ValueError(
                    f"Snapshot integrity check failed: {snapshot_id}. "
                    f"Data may be corrupted."
                )

        # Update index
        self.index[snapshot_id]["status"] = "restored"
        self._save_index()

        logger.info(f"Restored snapshot: {snapshot_id}")
        return snapshot_data["data"]

    def restore_batch(
        self, batch_id: str, verify_hash: bool = True
    ) -> Dict[int, Dict]:
        """
        Restore all posts in a batch from their snapshots.

        Args:
            batch_id: Batch identifier
            verify_hash: Verify data integrity

        Returns:
            Dict mapping post_id -> restored post data
        """
        restored = {}

        for snapshot_id, metadata in self.index.items():
            if metadata.get("batch_id") == batch_id:
                try:
                    post_data = self.restore_snapshot(snapshot_id, verify_hash)
                    post_id = metadata["post_id"]
                    restored[post_id] = post_data
                except Exception as e:
                    logger.error(
                        f"Failed to restore snapshot {snapshot_id}: {e}"
                    )
                    raise

        logger.info(f"Restored batch {batch_id}: {len(restored)} posts")
        return restored

    def list_snapshots(
        self,
        post_id: Optional[int] = None,
        batch_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """
        List snapshots with optional filtering.

        Args:
            post_id: Filter by post ID
            batch_id: Filter by batch ID
            limit: Max results

        Returns:
            List of snapshot metadata dicts
        """
        results = []

        for snapshot_id, metadata in sorted(
            self.index.items(), reverse=True
        ):
            if post_id and metadata["post_id"] != post_id:
                continue
            if batch_id and metadata.get("batch_id") != batch_id:
                continue

            results.append(
                {
                    "snapshot_id": snapshot_id,
                    "post_id": metadata["post_id"],
                    "batch_id": metadata.get("batch_id"),
                    "timestamp": metadata["timestamp"],
                    "status": metadata.get("status", "created"),
                }
            )

            if len(results) >= limit:
                break

        return results

    def get_snapshot_size(self, snapshot_id: str) -> int:
        """Get file size of snapshot in bytes"""
        snapshot_file = self.snapshot_dir / f"{snapshot_id}.json"
        if snapshot_file.exists():
            return snapshot_file.stat().st_size
        return 0

    def cleanup_old_snapshots(
        self, keep_recent: int = 100, batch_id: Optional[str] = None
    ) -> int:
        """
        Delete old snapshots, keeping only recent ones.

        Args:
            keep_recent: Number of recent snapshots to keep
            batch_id: Only clean snapshots from specific batch

        Returns:
            Number of deleted snapshots
        """
        snapshots = []

        for snapshot_id, metadata in self.index.items():
            if batch_id and metadata.get("batch_id") != batch_id:
                continue
            snapshots.append(
                (snapshot_id, metadata["timestamp"])
            )

        # Sort by timestamp, keep recent
        snapshots.sort(key=lambda x: x[1], reverse=True)
        to_delete = snapshots[keep_recent:]

        deleted_count = 0
        for snapshot_id, _ in to_delete:
            snapshot_file = self.snapshot_dir / f"{snapshot_id}.json"
            if snapshot_file.exists():
                snapshot_file.unlink()
                del self.index[snapshot_id]
                deleted_count += 1
                logger.info(f"Deleted old snapshot: {snapshot_id}")

        self._save_index()
        return deleted_count

    def export_batch_snapshots(
        self, batch_id: str, export_path: str
    ) -> str:
        """
        Export all snapshots in a batch to a single JSON file.

        Args:
            batch_id: Batch identifier
            export_path: Path to export file

        Returns:
            Path to exported file
        """
        export_data = {
            "batch_id": batch_id,
            "exported_at": datetime.utcnow().isoformat(),
            "snapshots": [],
        }

        for snapshot_id, metadata in self.index.items():
            if metadata.get("batch_id") == batch_id:
                snapshot_file = self.snapshot_dir / f"{snapshot_id}.json"
                if snapshot_file.exists():
                    with open(snapshot_file, "r", encoding="utf-8") as f:
                        snapshot_data = json.load(f)
                    export_data["snapshots"].append(snapshot_data)

        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(
            f"Exported batch {batch_id} to {export_path}: "
            f"{len(export_data['snapshots'])} snapshots"
        )
        return export_path
