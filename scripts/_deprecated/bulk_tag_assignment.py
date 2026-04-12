#!/usr/bin/env python3
"""
Bulk tag assignment script for YOLO LAB WordPress.com site
Assigns tags to posts by category based on verified tag ID mapping
"""

import subprocess
import json
import sys
from typing import Dict, List, Any
import time

# Site configuration
SITE_ID = 133512998  # YOLO LAB

# Tag mapping: category_id -> list of tag_ids
TAG_MAPPING = {
    # MUSIC categories
    96987488: [96990595, 96990596, 96990597, 96990598],  # MUSIC
    96987493: [96990599, 96990600, 96990601],  # HIPHOP-NEWS
    96987631: [96990602, 96990603, 96990604],  # HIPHOP-INTRO
    96987492: [96990605, 96990606, 96990607],  # HIPHOP-NEW-SONGS
    1982: [96990608, 96990609, 96990610],  # HIPHOP-EVENT
    96990388: [96990611, 96990612],  # MUSIC-EVENTS
    96990386: [96990613, 96990614, 96990615],  # MUSIC-PERSONA
    96988967: [96990616, 96990617, 96990618],  # YOLO-LYRICS

    # FILM categories
    96990383: [96990619, 96990620, 96990621],  # FILM-INTRO
    96990384: [96990622, 96990623, 96990624],  # TV-SERIES
    96990499: [96990625, 96990626, 96990627],  # ANIME
    96990522: [96990628, 96990629, 96990630],  # CLASSIC-FILMS
    96990390: [96990631, 96990632, 96990633],  # FILM-PERSONA
    96990387: [96990634, 96990635, 96990636],  # FILM-EVENTS

    # GAMES categories
    96990424: [96990637, 96990638, 96990639],  # GAMES
    96990427: [96990640, 96990641],  # GAMES-NEWS

    # ENTERTAINMENT
    96987489: [96990642, 96990643, 96990644],

    # TECH categories
    96990096: [96990645, 96990646, 96990647],  # TECH-NEWS
    96990518: [96990648, 96990649, 96990650],  # TECH-PERSONA

    # SPORTS categories
    96990391: [96990651, 96990652, 96990653],  # SPORTS-NEWS
    96990517: [96990654, 96990655, 96990656],  # SPORTS-PERSONA

    # EVENTS
    96990120: [96990657, 96990658, 96990659],

    # PERSONA categories
    96990389: [96990660, 96990661, 96990662],  # PERSONA
    96990524: [96990663, 96990664],  # AUTHOR-PERSONA
    96990555: [96990665, 96990666, 96990667],  # BUSINESS-PERSONA
    96990519: [96990668, 96990669, 96990670],  # RAGNAROK-PERSONA
    96990554: [96990671, 96990672, 96990673],  # SEXY-PERSONA

    # CLASSIC categories
    96990521: [96990674, 96990675],  # CLASSIC
    96990523: [96990676, 96990677, 96990678],  # CLASSIC-BOOKS
    96990525: [96990679, 96990680, 96990681],  # CLASSIC-EVENTS
    96990532: [96990682, 96990683, 96990684],  # CLASSIC-WORKS
}

# Priority categories (processing order)
PRIORITY_CATEGORIES = [
    96987488,  # MUSIC
    96987489,  # ENTERTAINMENT
    96990383,  # FILM-INTRO (start FILM)
    96990384,  # TV-SERIES
    96990499,  # ANIME
    96990522,  # CLASSIC-FILMS
    96990390,  # FILM-PERSONA
    96990387,  # FILM-EVENTS
]

# Remaining categories (will be processed after priority ones)
REMAINING_CATEGORIES = [k for k in TAG_MAPPING.keys() if k not in PRIORITY_CATEGORIES]

def fetch_posts_by_category(category_id: int, page: int = 1) -> Dict[str, Any]:
    """Fetch posts from a specific category using gh API"""
    cmd = [
        'gh', 'api', '-H', 'Accept: application/vnd.github+json',
        f'/repos/sooneocean/yololab-wordpress/contents/posts',
        '-F', f'category_id={category_id}',
        '-F', f'page={page}',
        '-F', 'per_page=100'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error fetching posts for category {category_id}: {e.stderr}")
        return {"posts": [], "total": 0}

def update_post_tags(post_id: int, tag_ids: List[int]) -> bool:
    """Update a post's tags via WordPress.com API"""
    cmd = [
        'gh', 'api', '-X', 'POST',
        f'/sites/{SITE_ID}/posts/{post_id}',
        f'-f', f'tags={json.dumps(tag_ids)}'
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error updating post {post_id}: {e.stderr}")
        return False

def process_category(category_id: int, category_name: str, posts: List[Dict]) -> Dict[str, Any]:
    """Process all posts in a category"""
    tag_ids = TAG_MAPPING[category_id]
    success_count = 0
    failure_count = 0

    for i, post in enumerate(posts, 1):
        post_id = post.get('id')
        title = post.get('title', 'Untitled')[:50]

        if update_post_tags(post_id, tag_ids):
            success_count += 1
            status = "✓"
        else:
            failure_count += 1
            status = "✗"

        # Print progress every 10 posts
        if i % 10 == 0:
            print(f"  [{category_name}] {status} Post {i}/{len(posts)}: {title}...")

        # Small delay to avoid API throttling
        time.sleep(0.1)

    return {
        "category_id": category_id,
        "category_name": category_name,
        "total_posts": len(posts),
        "success": success_count,
        "failed": failure_count
    }

def main():
    print("=" * 70)
    print("YOLO LAB - 標籤批量分配")
    print("=" * 70)

    all_categories = PRIORITY_CATEGORIES + REMAINING_CATEGORIES
    total_posts_updated = 0
    total_failures = 0
    results = []

    for idx, category_id in enumerate(all_categories, 1):
        category_name = f"Category_{category_id}"

        # Fetch all posts for this category (paginate through all pages)
        all_posts = []
        page = 1

        print(f"\n[{idx}/{len(all_categories)}] 處理分類: {category_id}")

        while True:
            result = fetch_posts_by_category(category_id, page)
            posts = result.get("posts", [])

            if not posts:
                break

            all_posts.extend(posts)
            page += 1

            # Pagination limit
            if len(all_posts) >= 1000:
                break

        if all_posts:
            result = process_category(category_id, category_name, all_posts)
            results.append(result)
            total_posts_updated += result["success"]
            total_failures += result["failed"]

            print(f"  完成: {result['success']}/{result['total_posts']} 篇文章")

            # Progress report every 300 posts
            if total_posts_updated % 300 == 0:
                print(f"\n【進度報告】 已完成 {total_posts_updated} 篇文章")

    # Final report
    print("\n" + "=" * 70)
    print("標籤分配完成")
    print("=" * 70)
    print(f"總計: {total_posts_updated} 篇文章更新成功")
    print(f"失敗: {total_failures} 篇文章")
    print(f"處理分類: {len(results)} 個")

    return 0 if total_failures == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
