#!/usr/bin/env python3
"""
Batch Tag Allocator - Optimized Label Assignment
Assigns tags in 5-post batches with progressive monitoring
"""

import os
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime

# Configuration
SITE_URL = "yololab.net"
API_ENDPOINT = f"https://public-api.wordpress.com/rest/v1.1/sites/{SITE_URL}"
WP_TOKEN = os.getenv("WP_TOKEN")

# Category and tag mappings
CATEGORIES = {
    "MUSIC": 96987488,
    "ENTERTAINMENT": 97219648,
    "FILM&TV": 97219649,
}

TAG_IDS = [
    96990595,  # Tag 1
    96990596,  # Tag 2
    96990597,  # Tag 3
    96990598,  # Tag 4
]

BATCH_SIZE = 5
BATCH_INTERVAL = 3  # seconds between batches
PROGRESS_CHECKPOINT = 50  # report every N posts


def fetch_posts_by_category(category_id, page=1, per_page=100):
    """Fetch posts from a specific category"""
    url = f"{API_ENDPOINT}/posts?categories={category_id}&per_page={per_page}&page={page}"

    req = urllib.request.Request(url, method='GET')
    req.add_header('Authorization', f'Bearer {WP_TOKEN}')

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get('posts', []), data.get('found', 0)
    except Exception as e:
        print(f"Error fetching posts from category {category_id}: {e}")
        return [], 0


def update_post_tags(post_id, tag_ids):
    """Add tags to a single post"""
    url = f"{API_ENDPOINT}/posts/{post_id}"

    data = urllib.parse.urlencode({
        "tags": ",".join(str(tid) for tid in tag_ids)
    }).encode('utf-8')

    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Authorization', f'Bearer {WP_TOKEN}')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return True
    except Exception as e:
        print(f"Error updating post {post_id}: {e}")
        return False


def process_category_batch(category_name, category_id, start_from=1):
    """Process a category in batches"""
    print(f"\n{'='*60}")
    print(f"Processing {category_name} (Category ID: {category_id})")
    print(f"{'='*60}")

    total_found = 0
    processed = 0
    failed = 0
    page = 1
    all_posts = []

    # Fetch all posts from category
    while True:
        posts, total = fetch_posts_by_category(category_id, page=page)
        if not posts:
            break

        all_posts.extend(posts)
        total_found = total
        page += 1
        print(f"Fetched page {page-1}: {len(posts)} posts (Total: {total_found})")

    print(f"\nTotal posts in {category_name}: {total_found}")

    # Process in batches of 5
    for i in range(start_from - 1, len(all_posts), BATCH_SIZE):
        batch = all_posts[i:i+BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1

        print(f"\n[Batch {batch_num}] Processing {len(batch)} posts ({i+1}-{min(i+BATCH_SIZE, len(all_posts))})")

        for post in batch:
            post_id = post['ID']
            post_title = post['title'][:50]  # truncate for display

            if update_post_tags(post_id, TAG_IDS):
                processed += 1
                print(f"  ✓ Post {post_id}: {post_title}")
            else:
                failed += 1
                print(f"  ✗ Post {post_id}: {post_title} [FAILED]")

        # Progress report every 50 posts
        if processed % PROGRESS_CHECKPOINT == 0:
            print(f"\n>>> Progress: {processed}/{total_found} completed, {failed} failed")

        # Interval between batches
        if i + BATCH_SIZE < len(all_posts):
            print(f"Waiting {BATCH_INTERVAL}s before next batch...")
            time.sleep(BATCH_INTERVAL)

    print(f"\n{'='*60}")
    print(f"{category_name} Complete: {processed}/{total_found} posts tagged")
    print(f"Failed: {failed}")
    print(f"{'='*60}\n")

    return processed, total_found, failed


def main():
    if not WP_TOKEN:
        print("Error: WP_TOKEN environment variable not set.")
        return

    print(f"\n🚀 Batch Tag Allocator - Optimized Strategy")
    print(f"Batch Size: {BATCH_SIZE} posts")
    print(f"Interval: {BATCH_INTERVAL} seconds")
    print(f"Progress Checkpoint: {PROGRESS_CHECKPOINT} posts\n")

    grand_total_processed = 0
    grand_total_found = 0
    grand_total_failed = 0

    # Process categories in priority order
    priority_order = ["MUSIC", "ENTERTAINMENT", "FILM&TV"]

    for category_name in priority_order:
        if category_name not in CATEGORIES:
            continue

        category_id = CATEGORIES[category_name]
        processed, total, failed = process_category_batch(category_name, category_id)

        grand_total_processed += processed
        grand_total_found += total
        grand_total_failed += failed

    # Final summary
    print(f"\n{'='*60}")
    print(f"FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"Total Processed: {grand_total_processed}/{grand_total_found}")
    print(f"Total Failed: {grand_total_failed}")
    print(f"Success Rate: {(grand_total_processed/grand_total_found*100):.1f}%" if grand_total_found > 0 else "N/A")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
