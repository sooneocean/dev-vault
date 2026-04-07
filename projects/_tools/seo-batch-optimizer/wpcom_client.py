"""
WordPress.com API Client wrapper
Provides safe interface to wpcom-mcp tool
"""

import json
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WPPost:
    """WordPress post data structure"""
    id: int
    title: str
    excerpt: str
    content: str
    featured_image: Optional[Dict] = None
    meta: Optional[Dict] = None
    categories: Optional[List] = None
    tags: Optional[List] = None
    status: str = "publish"
    type: str = "post"


class WPComAPIClient:
    """
    WordPress.com API client using wpcom-mcp.

    This is a wrapper that will interface with the MCP tool.
    In actual implementation, this would call the wpcom-mcp tool
    via the Claude Code environment.
    """

    def __init__(self, site_name: str, rate_limit_delay: float = 0.5):
        """
        Initialize WordPress.com client.

        Args:
            site_name: WordPress.com site name (e.g., 'yololab.net')
            rate_limit_delay: Delay between API calls in seconds
        """
        self.site_name = site_name
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time = 0

    def _apply_rate_limit(self) -> None:
        """Apply rate limiting between API calls"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()

    def get_post(self, post_id: int) -> Optional[Dict]:
        """
        Fetch a single post from WordPress.com.

        Args:
            post_id: WordPress post ID

        Returns:
            Post data dict or None if not found
        """
        self._apply_rate_limit()
        logger.debug(f"Fetching post {post_id} from {self.site_name}")

        # In actual implementation, call wpcom-mcp-content-authoring
        # For now, return stub
        try:
            # TODO: Call wpcom-mcp-content-authoring with operation="posts.get"
            post = {
                "id": post_id,
                "title": "[post title]",
                "excerpt": "[post excerpt]",
                "content": "[post content]",
                "featured_image": None,
                "meta": {},
                "status": "publish",
            }
            return post
        except Exception as e:
            logger.error(f"Failed to fetch post {post_id}: {e}")
            return None

    def get_posts(
        self,
        per_page: int = 100,
        page: int = 1,
        status: str = "publish",
    ) -> List[Dict]:
        """
        Fetch posts from WordPress.com.

        Args:
            per_page: Posts per request
            page: Page number
            status: Post status filter

        Returns:
            List of post data dicts
        """
        self._apply_rate_limit()
        logger.debug(
            f"Fetching posts page {page} from {self.site_name}"
        )

        # TODO: Call wpcom-mcp-content-authoring with operation="posts.list"
        return []

    def get_all_posts(self) -> List[Dict]:
        """
        Fetch all posts from WordPress.com (paginated).

        Returns:
            List of all posts
        """
        all_posts = []
        page = 1
        per_page = 100

        while True:
            posts = self.get_posts(per_page=per_page, page=page)

            if not posts:
                break

            all_posts.extend(posts)
            page += 1

        logger.info(f"Fetched {len(all_posts)} posts from {self.site_name}")
        return all_posts

    def update_post(self, post_id: int, updates: Dict) -> bool:
        """
        Update a post on WordPress.com.

        Args:
            post_id: WordPress post ID
            updates: Dict with fields to update (title, excerpt, content, meta, etc.)

        Returns:
            True if successful
        """
        self._apply_rate_limit()
        logger.debug(
            f"Updating post {post_id}: {list(updates.keys())}"
        )

        # TODO: Call wpcom-mcp-content-authoring with operation="posts.update"
        try:
            # Validate required fields
            if not post_id or not updates:
                raise ValueError("post_id and updates required")

            logger.info(f"Updated post {post_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update post {post_id}: {e}")
            return False

    def update_posts_batch(
        self,
        updates: List[Dict],
        continue_on_error: bool = False,
    ) -> tuple[int, int]:
        """
        Update multiple posts.

        Args:
            updates: List of update dicts (must include 'id' field)
            continue_on_error: If True, continue even if some updates fail

        Returns:
            (successful, failed) count
        """
        successful = 0
        failed = 0

        for update in updates:
            post_id = update.pop("id", None)
            if not post_id:
                logger.warning("Update dict missing 'id' field")
                failed += 1
                if not continue_on_error:
                    break
                continue

            if self.update_post(post_id, update):
                successful += 1
            else:
                failed += 1
                if not continue_on_error:
                    break

        logger.info(
            f"Batch update complete: {successful} successful, {failed} failed"
        )
        return successful, failed

    def get_post_stats(
        self,
        post_id: int,
        period: str = "month",
    ) -> Optional[Dict]:
        """
        Get post statistics (views, visitors, etc.).

        Args:
            post_id: WordPress post ID
            period: Time period ('day', 'week', 'month', 'year')

        Returns:
            Stats dict or None if not found
        """
        self._apply_rate_limit()

        # TODO: Call wpcom-mcp-site-statistics
        try:
            stats = {
                "post_id": post_id,
                "views": 0,
                "visitors": 0,
                "period": period,
            }
            return stats
        except Exception as e:
            logger.error(f"Failed to fetch stats for post {post_id}: {e}")
            return None

    def search_posts(self, query: str) -> List[Dict]:
        """
        Search posts on WordPress.com.

        Args:
            query: Search query

        Returns:
            List of matching posts
        """
        self._apply_rate_limit()

        # TODO: Call wpcom-mcp-content-authoring with search query
        return []

    def get_valid_post_ids(self) -> List[int]:
        """
        Get list of all valid post IDs (for link validation).

        Returns:
            List of post IDs
        """
        posts = self.get_all_posts()
        return [p["id"] for p in posts]

    def verify_post_exists(self, post_id: int) -> bool:
        """
        Check if post exists.

        Args:
            post_id: WordPress post ID

        Returns:
            True if post exists and is accessible
        """
        post = self.get_post(post_id)
        return post is not None

    def monitor_for_404(
        self,
        post_ids: List[int],
        duration_hours: int = 24,
        check_interval_minutes: int = 60,
    ) -> Dict[int, List[str]]:
        """
        Monitor posts for 404 errors over time.

        Args:
            post_ids: List of post IDs to monitor
            duration_hours: Monitoring duration
            check_interval_minutes: Time between checks

        Returns:
            Dict mapping post_id -> list of error timestamps
        """
        logger.info(
            f"Starting 24h monitoring for {len(post_ids)} posts"
        )

        # TODO: Implement monitoring loop with HTTP health checks
        # For now, return empty dict (no errors)
        return {post_id: [] for post_id in post_ids}
