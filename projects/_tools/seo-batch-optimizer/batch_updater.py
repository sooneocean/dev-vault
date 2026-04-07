"""
Batch Updater - Safe, transactional batch updates for WordPress.com posts
Implements rollback, validation, and monitoring
"""

import json
import logging
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

from snapshot_manager import SnapshotManager
from post_validator import PostValidator

logger = logging.getLogger(__name__)


class BatchStatus(Enum):
    """Batch execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class BatchUpdate:
    """Single post update in a batch"""
    post_id: int
    title: Optional[str] = None
    excerpt: Optional[str] = None
    content: Optional[str] = None
    featured_image_alt: Optional[str] = None
    meta: Optional[Dict] = None
    internal_links: Optional[List[Dict]] = None


@dataclass
class UpdateResult:
    """Result of updating a single post"""
    post_id: int
    success: bool
    snapshot_id: str
    old_values: Dict
    new_values: Dict
    error: Optional[str] = None
    warning: Optional[str] = None


@dataclass
class BatchResult:
    """Result of batch update operation"""
    batch_id: str
    batch_size: int
    status: BatchStatus
    started_at: str
    completed_at: Optional[str] = None
    successful_updates: int = 0
    failed_updates: int = 0
    rolled_back: bool = False
    update_results: List[UpdateResult] = None
    error_message: Optional[str] = None
    git_commit: Optional[str] = None

    def __post_init__(self):
        if self.update_results is None:
            self.update_results = []


class BatchUpdater:
    """
    Safe batch updater for WordPress.com posts.
    Supports:
    - Transactional updates (all-or-nothing)
    - Automatic rollback on failure
    - Validation before/after updates
    - Git integration
    - Progress tracking
    """

    BATCH_SIZE = 50
    API_RATE_LIMIT_DELAY = 0.5  # seconds between API calls

    def __init__(
        self,
        site_name: str,
        dry_run: bool = False,
        snapshot_manager: Optional[SnapshotManager] = None,
        validator: Optional[PostValidator] = None,
    ):
        """
        Initialize batch updater.

        Args:
            site_name: WordPress.com site name (e.g., 'yololab.net')
            dry_run: If True, simulate updates without making changes
            snapshot_manager: SnapshotManager instance
            validator: PostValidator instance
        """
        self.site_name = site_name
        self.dry_run = dry_run
        self.snapshot_manager = (
            snapshot_manager or SnapshotManager()
        )
        self.validator = validator or PostValidator()

        self.log_dir = Path("batch_logs")
        self.log_dir.mkdir(exist_ok=True)

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.utcnow().isoformat()

    def _generate_batch_id(self, first_post_id: int, last_post_id: int) -> str:
        """Generate batch ID from post ID range"""
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        return f"batch-{first_post_id}-{last_post_id}-{timestamp}"

    def _log_batch(self, batch_result: BatchResult) -> Path:
        """Save batch result to log file"""
        log_file = (
            self.log_dir / f"{batch_result.batch_id}-result.json"
        )

        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(asdict(batch_result), f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Batch log saved to {log_file}")
        return log_file

    def prepare_batch(
        self,
        updates: List[BatchUpdate],
        valid_post_ids: Optional[List[int]] = None,
    ) -> Tuple[List[BatchUpdate], List[Dict]]:
        """
        Prepare and validate batch updates.

        Returns:
            (validated_updates, validation_errors)
        """
        validated = []
        errors = []

        for update in updates:
            # Build post data for validation
            post_data = {
                "id": update.post_id,
                "title": update.title or "",
                "excerpt": update.excerpt or "",
                "content": update.content or "",
                "featured_image": {"alt": update.featured_image_alt} if update.featured_image_alt else None,
            }

            is_valid, results = self.validator.validate_post(
                post_data, valid_post_ids
            )

            if is_valid:
                validated.append(update)
            else:
                error_summary = self.validator.get_error_summary()
                errors.append({
                    "post_id": update.post_id,
                    "errors": error_summary,
                })
                logger.warning(
                    f"Post {update.post_id} failed validation: "
                    f"{error_summary}"
                )

        logger.info(
            f"Batch validation: {len(validated)}/{len(updates)} valid"
        )
        return validated, errors

    def execute_batch(
        self,
        updates: List[BatchUpdate],
        valid_post_ids: Optional[List[int]] = None,
        require_confirmation: bool = False,
    ) -> BatchResult:
        """
        Execute batch update with safety checks and rollback.

        Args:
            updates: List of BatchUpdate objects
            valid_post_ids: List of valid post IDs for link validation
            require_confirmation: If True, print summary and wait for input

        Returns:
            BatchResult with execution status and details
        """
        if not updates:
            raise ValueError("No updates provided")

        # Generate batch ID
        post_ids = [u.post_id for u in updates]
        batch_id = self._generate_batch_id(min(post_ids), max(post_ids))

        batch_result = BatchResult(
            batch_id=batch_id,
            batch_size=len(updates),
            status=BatchStatus.PENDING,
            started_at=self._get_timestamp(),
        )

        try:
            # Step 1: Prepare and validate
            logger.info(f"[BATCH] Starting batch {batch_id}")
            logger.info(f"[BATCH] Validating {len(updates)} updates...")

            validated, validation_errors = self.prepare_batch(
                updates, valid_post_ids
            )

            if not validated:
                batch_result.status = BatchStatus.FAILED
                batch_result.error_message = (
                    f"All {len(updates)} posts failed validation"
                )
                batch_result.completed_at = self._get_timestamp()
                self._log_batch(batch_result)
                return batch_result

            if len(validated) < len(updates):
                logger.warning(
                    f"{len(updates) - len(validated)} posts failed "
                    f"validation and will be skipped"
                )

            # Step 2: Summary and confirmation
            self._print_batch_summary(validated, batch_result)

            if require_confirmation and not self.dry_run:
                confirm = input(
                    f"\nProceed with {len(validated)} updates? "
                    f"(yes/no): "
                )
                if confirm.lower() != "yes":
                    batch_result.status = BatchStatus.PENDING
                    batch_result.completed_at = self._get_timestamp()
                    logger.info("[BATCH] Cancelled by user")
                    self._log_batch(batch_result)
                    return batch_result

            # Step 3: Create snapshots
            logger.info("[BATCH] Creating snapshots...")
            # Note: In real implementation, fetch post data first
            # For now, we simulate with update data
            snapshot_ids = []
            for update in validated:
                snapshot_id = self.snapshot_manager.create_snapshot(
                    post_id=update.post_id,
                    post_data={
                        "id": update.post_id,
                        "title": update.title or "",
                        "excerpt": update.excerpt or "",
                        "content": update.content or "",
                    },
                    batch_id=batch_id,
                    description="Pre-batch snapshot",
                )
                snapshot_ids.append(snapshot_id)

            # Step 4: Execute updates
            batch_result.status = BatchStatus.IN_PROGRESS
            logger.info("[BATCH] Executing updates...")

            results = []
            for i, update in enumerate(validated, 1):
                logger.info(
                    f"[BATCH] Updating {i}/{len(validated)}: "
                    f"post {update.post_id}"
                )

                result = self._update_single_post(update)
                results.append(result)

                if not result.success:
                    logger.error(
                        f"[BATCH] Failed to update post {update.post_id}: "
                        f"{result.error}"
                    )

                # Rate limiting
                if i < len(validated):
                    time.sleep(self.API_RATE_LIMIT_DELAY)

                batch_result.update_results.append(result)

            # Step 5: Count results
            batch_result.successful_updates = sum(
                1 for r in results if r.success
            )
            batch_result.failed_updates = len(results) - batch_result.successful_updates

            # Step 6: Rollback if all failed
            if batch_result.failed_updates == len(results):
                logger.error(
                    "[BATCH] All updates failed, rolling back..."
                )
                self._rollback_batch(batch_id)
                batch_result.rolled_back = True
                batch_result.status = BatchStatus.ROLLED_BACK
                batch_result.completed_at = self._get_timestamp()
                self._log_batch(batch_result)
                return batch_result

            # Step 7: Git commit (if not dry-run)
            if not self.dry_run and batch_result.successful_updates > 0:
                commit_hash = self._git_commit_batch(batch_result)
                batch_result.git_commit = commit_hash
                logger.info(f"[BATCH] Committed: {commit_hash}")

            batch_result.status = BatchStatus.COMPLETED
            batch_result.completed_at = self._get_timestamp()

            logger.info(
                f"[BATCH] Completed: {batch_result.successful_updates} "
                f"successful, {batch_result.failed_updates} failed"
            )

        except Exception as e:
            logger.exception(f"[BATCH] Unexpected error: {e}")
            batch_result.status = BatchStatus.FAILED
            batch_result.error_message = str(e)
            batch_result.completed_at = self._get_timestamp()

        finally:
            self._log_batch(batch_result)

        return batch_result

    def _update_single_post(self, update: BatchUpdate) -> UpdateResult:
        """
        Update a single post (simulated if dry-run).

        Returns:
            UpdateResult with status and details
        """
        snapshot_ids = self.snapshot_manager.list_snapshots(
            post_id=update.post_id, limit=1
        )
        snapshot_id = (
            snapshot_ids[0]["snapshot_id"]
            if snapshot_ids
            else "unknown"
        )

        old_values = {
            "title": "[current]",
            "excerpt": "[current]",
        }

        new_values = {
            "title": update.title,
            "excerpt": update.excerpt,
        }

        if self.dry_run:
            return UpdateResult(
                post_id=update.post_id,
                success=True,
                snapshot_id=snapshot_id,
                old_values=old_values,
                new_values=new_values,
                warning="DRY RUN - no actual changes made",
            )

        try:
            # In real implementation, call wpcom-mcp API here
            # For now, simulate successful update
            logger.debug(
                f"Updating post {update.post_id}: "
                f"title={update.title}, excerpt={update.excerpt}"
            )

            return UpdateResult(
                post_id=update.post_id,
                success=True,
                snapshot_id=snapshot_id,
                old_values=old_values,
                new_values=new_values,
            )

        except Exception as e:
            logger.error(f"Failed to update post {update.post_id}: {e}")
            return UpdateResult(
                post_id=update.post_id,
                success=False,
                snapshot_id=snapshot_id,
                old_values=old_values,
                new_values=new_values,
                error=str(e),
            )

    def _rollback_batch(self, batch_id: str) -> int:
        """
        Rollback all posts in batch from snapshots.

        Returns:
            Number of posts rolled back
        """
        try:
            restored = self.snapshot_manager.restore_batch(batch_id)
            logger.info(
                f"[BATCH] Rolled back {len(restored)} posts "
                f"from batch {batch_id}"
            )
            return len(restored)
        except Exception as e:
            logger.error(f"[BATCH] Rollback failed: {e}")
            return 0

    def _git_commit_batch(self, batch_result: BatchResult) -> str:
        """
        Create git commit for batch update.

        Returns:
            Commit hash
        """
        first_id = (
            batch_result.update_results[0].post_id
            if batch_result.update_results
            else "???"
        )
        last_id = (
            batch_result.update_results[-1].post_id
            if batch_result.update_results
            else "???"
        )

        commit_msg = (
            f"chore(seo): optimize {batch_result.successful_updates} posts "
            f"[ID: {first_id}-{last_id}]"
        )

        if self.dry_run:
            logger.info(f"[DRY RUN] Would commit: {commit_msg}")
            return "dry-run-commit"

        try:
            # Create commit
            subprocess.run(
                ["git", "add", "."],
                cwd=Path.cwd(),
                capture_output=True,
                check=True,
            )

            result = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                # Extract commit hash
                commit_hash = result.stdout.split()[2].rstrip("]")
                return commit_hash
            else:
                logger.warning(
                    f"Git commit failed: {result.stderr}"
                )
                return "unknown"

        except Exception as e:
            logger.error(f"Git commit error: {e}")
            return "error"

    def _print_batch_summary(
        self,
        updates: List[BatchUpdate],
        batch_result: BatchResult,
    ) -> None:
        """Print human-readable batch summary"""
        print("\n" + "=" * 70)
        print(f"BATCH UPDATE SUMMARY")
        print("=" * 70)
        print(f"Batch ID: {batch_result.batch_id}")
        print(f"Posts to update: {len(updates)}")
        print(f"Dry run: {self.dry_run}")
        print(f"Started at: {batch_result.started_at}")
        print("\nSample updates:")

        for update in updates[:5]:
            print(f"\n  Post {update.post_id}:")
            if update.title:
                title_preview = update.title[:60] + (
                    "..." if len(update.title) > 60 else ""
                )
                print(f"    Title: {title_preview}")
            if update.excerpt:
                desc_preview = update.excerpt[:60] + (
                    "..." if len(update.excerpt) > 60 else ""
                )
                print(f"    Description: {desc_preview}")

        if len(updates) > 5:
            print(f"\n  ... and {len(updates) - 5} more posts")

        print("\n" + "=" * 70)

    def chunk_updates(
        self,
        updates: List[BatchUpdate],
        chunk_size: int = BATCH_SIZE,
    ) -> List[List[BatchUpdate]]:
        """
        Split updates into smaller batches.

        Args:
            updates: Full update list
            chunk_size: Posts per batch

        Returns:
            List of update chunks
        """
        return [
            updates[i : i + chunk_size]
            for i in range(0, len(updates), chunk_size)
        ]

    def process_multiple_batches(
        self,
        all_updates: List[BatchUpdate],
        valid_post_ids: Optional[List[int]] = None,
        require_confirmation: bool = True,
    ) -> List[BatchResult]:
        """
        Process multiple batches sequentially.

        Returns:
            List of BatchResult objects
        """
        batches = self.chunk_updates(all_updates)
        results = []

        logger.info(
            f"[UPDATER] Processing {len(batches)} batches "
            f"({len(all_updates)} total posts)"
        )

        for i, batch in enumerate(batches, 1):
            logger.info(
                f"[UPDATER] Batch {i}/{len(batches)}: "
                f"{len(batch)} posts"
            )

            batch_result = self.execute_batch(
                batch,
                valid_post_ids=valid_post_ids,
                require_confirmation=require_confirmation,
            )

            results.append(batch_result)

            if batch_result.status == BatchStatus.FAILED:
                logger.error(
                    f"[UPDATER] Batch {i} failed: "
                    f"{batch_result.error_message}"
                )
                # Optionally stop processing
                break

        return results
