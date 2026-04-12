#!/usr/bin/env python3
"""
SEO Batch Optimizer for YOLOLAB.net
Processes articles via WordPress.com MCP to optimize SEO metadata
"""

import os
import sys
import json
import time
import subprocess
from typing import Optional, Dict, List, Tuple
from datetime import datetime

import anthropic

# Configuration
SITE_ID = 133512998
BATCH_SIZE = 10
API_DELAY_SECONDS = 1
TOTAL_ARTICLES = 2725
ALREADY_OPTIMIZED = 74

# Anthropic API client
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def call_wpcom_mcp(operation: str, params: Dict) -> Dict:
    """Call WordPress.com MCP operations via Node.js"""
    cmd = [
        "node",
        "-e",
        f"""
const {{ mcp__wpcom_mcp__wpcom_mcp_content_authoring }} = require('mcp');
(async () => {{
  const result = await mcp__wpcom_mcp__wpcom_mcp_content_authoring({{
    action: 'execute',
    operation: '{operation}',
    wpcom_site: {SITE_ID},
    params: {json.dumps(params)}
  }});
  console.log(JSON.stringify(result));
}})();
"""
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"Error calling {operation}: {result.stderr}")
            return None
    except Exception as e:
        print(f"Exception calling {operation}: {e}")
        return None


def get_posts_page(page: int, per_page: int = 10) -> Optional[List[Dict]]:
    """Fetch a page of posts from WordPress.com site"""
    params = {
        "page": page,
        "per_page": per_page,
        "orderby": "id",
        "order": "desc",
        "status": "publish"
    }

    result = call_wpcom_mcp("posts.list", params)
    if result and "posts" in result:
        return result["posts"]
    return None


def get_post_detail(post_id: int) -> Optional[Dict]:
    """Fetch detailed information about a post"""
    result = call_wpcom_mcp("posts.get", {"id": post_id})
    return result if result else None


def generate_seo_metadata(title: str, excerpt: str) -> Tuple[str, str]:
    """Generate optimized SEO title and description using Claude"""
    try:
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": f"""请为以下文章生成优化的 SEO 元数据：

标题：{title}
摘要：{excerpt[:300]}

请提供：
1. SEO 优化标题（45-60 字，包含关键词）
2. Meta 描述（120-160 字，吸引人且包含关键词）

格式：
TITLE: [标题]
DESCRIPTION: [描述]"""
                }
            ]
        )

        content = message.content[0].text
        lines = content.strip().split('\n')

        seo_title = ""
        seo_desc = ""

        for line in lines:
            if line.startswith("TITLE:"):
                seo_title = line.replace("TITLE:", "").strip()
            elif line.startswith("DESCRIPTION:"):
                seo_desc = line.replace("DESCRIPTION:", "").strip()

        return seo_title, seo_desc
    except Exception as e:
        print(f"Error generating SEO metadata: {e}")
        return None, None


def update_post_seo(post_id: int, seo_title: str, seo_desc: str) -> bool:
    """Update post with SEO metadata"""
    params = {
        "id": post_id,
        "meta": {
            "jetpack_seo_html_title": seo_title,
            "advanced_seo_description": seo_desc
        },
        "user_confirmed": "yes"
    }

    result = call_wpcom_mcp("posts.update", params)
    return result is not None


def process_batch(start_page: int) -> Tuple[int, int, List[int]]:
    """Process a batch of posts
    Returns: (successful_count, failed_count, failed_ids)
    """
    posts = get_posts_page(start_page, BATCH_SIZE)
    if not posts:
        return 0, 0, []

    success_count = 0
    failed_ids = []

    for post in posts:
        post_id = post.get("id")
        title = post.get("title", "")
        excerpt = post.get("excerpt", "")

        print(f"  Processing post {post_id}: {title[:50]}...", end=" ", flush=True)

        if not title:
            print("SKIP (no title)")
            continue

        # Generate SEO metadata
        seo_title, seo_desc = generate_seo_metadata(title, excerpt)

        if not seo_title or not seo_desc:
            print("FAIL (generation)")
            failed_ids.append(post_id)
            continue

        # Update post
        if update_post_seo(post_id, seo_title, seo_desc):
            print("OK")
            success_count += 1
        else:
            print("FAIL (update)")
            failed_ids.append(post_id)

        # Rate limiting
        time.sleep(0.5)

    return success_count, len(failed_ids), failed_ids


def main():
    """Main execution loop"""
    print("=" * 80)
    print(f"SEO Batch Optimizer for YOLOLAB.net (Site: {SITE_ID})")
    print(f"Total articles: {TOTAL_ARTICLES}")
    print(f"Already optimized: {ALREADY_OPTIMIZED}")
    print(f"Remaining: {TOTAL_ARTICLES - ALREADY_OPTIMIZED}")
    print("=" * 80)
    print()

    total_success = 0
    total_failed = 0
    all_failed_ids = []

    # Calculate starting page (assuming 10 per page)
    pages_to_process = (TOTAL_ARTICLES - ALREADY_OPTIMIZED + BATCH_SIZE - 1) // BATCH_SIZE

    for page_num in range(1, pages_to_process + 1):
        print(f"Batch {page_num}/{pages_to_process} (Page {page_num}):")

        success, failed, failed_ids = process_batch(page_num)

        total_success += success
        total_failed += failed
        all_failed_ids.extend(failed_ids)

        print(f"  Result: {success} success, {failed} failed")
        print(f"  Running total: {ALREADY_OPTIMIZED + total_success}/{TOTAL_ARTICLES}")
        print()

        # Report milestones
        current_total = ALREADY_OPTIMIZED + total_success
        if current_total % 100 == 0:
            print(f"  MILESTONE: {current_total} articles optimized")
            print()

        # Rate limiting between batches
        if page_num < pages_to_process:
            time.sleep(API_DELAY_SECONDS)

    # Final report
    print("=" * 80)
    print(f"Final Report:")
    print(f"  Successful optimizations: {total_success}")
    print(f"  Failed: {total_failed}")
    print(f"  Total optimized: {ALREADY_OPTIMIZED + total_success}/{TOTAL_ARTICLES}")
    print(f"  Progress: {((ALREADY_OPTIMIZED + total_success) / TOTAL_ARTICLES * 100):.1f}%")

    if all_failed_ids:
        print(f"\nFailed post IDs: {all_failed_ids}")

    print("=" * 80)


if __name__ == "__main__":
    main()
