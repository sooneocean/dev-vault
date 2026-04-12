#!/usr/bin/env python3
"""
Bulk tag assignment for YOLO LAB WordPress.com
Final phase - systematically assign tags to all posts by category
"""

import subprocess
import json
import time
from typing import Dict, List, Any
from datetime import datetime

SITE_ID = 133512998
BASE_URL = f"https://public-api.wordpress.com/wp/v2/sites/{SITE_ID}"

# Tag mapping by category
TAG_MAPPING = {
    96987488: [96990595, 96990596, 96990597, 96990598],  # MUSIC
    96987493: [96990599, 96990600, 96990601],  # HIPHOP-NEWS
    96987631: [96990602, 96990603, 96990604],  # HIPHOP-INTRO
    96987492: [96990605, 96990606, 96990607],  # HIPHOP-NEW-SONGS
    1982: [96990608, 96990609, 96990610],  # HIPHOP-EVENT
    96990388: [96990611, 96990612],  # MUSIC-EVENTS
    96990386: [96990613, 96990614, 96990615],  # MUSIC-PERSONA
    96988967: [96990616, 96990617, 96990618],  # YOLO-LYRICS
    96987489: [96990642, 96990643, 96990644],  # ENTERTAINMENT
    96990383: [96990619, 96990620, 96990621],  # FILM-INTRO
    96990384: [96990622, 96990623, 96990624],  # TV-SERIES
    96990499: [96990625, 96990626, 96990627],  # ANIME
    96990522: [96990628, 96990629, 96990630],  # CLASSIC-FILMS
    96990390: [96990631, 96990632, 96990633],  # FILM-PERSONA
    96990387: [96990634, 96990635, 96990636],  # FILM-EVENTS
    96990424: [96990637, 96990638, 96990639],  # GAMES
    96990427: [96990640, 96990641],  # GAMES-NEWS
    96990096: [96990645, 96990646, 96990647],  # TECH-NEWS
    96990518: [96990648, 96990649, 96990650],  # TECH-PERSONA
    96990391: [96990651, 96990652, 96990653],  # SPORTS-NEWS
    96990517: [96990654, 96990655, 96990656],  # SPORTS-PERSONA
    96990120: [96990657, 96990658, 96990659],  # EVENTS
    96990389: [96990660, 96990661, 96990662],  # PERSONA
    96990524: [96990663, 96990664],  # AUTHOR-PERSONA
    96990555: [96990665, 96990666, 96990667],  # BUSINESS-PERSONA
    96990519: [96990668, 96990669, 96990670],  # RAGNAROK-PERSONA
    96990554: [96990671, 96990672, 96990673],  # SEXY-PERSONA
    96990521: [96990674, 96990675],  # CLASSIC
    96990523: [96990676, 96990677, 96990678],  # CLASSIC-BOOKS
    96990525: [96990679, 96990680, 96990681],  # CLASSIC-EVENTS
    96990532: [96990682, 96990683, 96990684],  # CLASSIC-WORKS
}

PRIORITY_ORDER = [96987488, 96987489]  # MUSIC, ENTERTAINMENT first

def fetch_posts_by_category(category_id: int, page: int = 1, per_page: int = 100) -> Dict[str, Any]:
    """Fetch posts from a specific category"""
    query = f"?categories={category_id}&status=publish&per_page={per_page}&page={page}&_fields=id,title,tags"
    cmd = ['gh', 'api', f'{BASE_URL}/posts{query}', '--jq', '.']

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        return data if isinstance(data, dict) and 'id' in str(data) else {"posts": data if isinstance(data, list) else []}
    except Exception as e:
        print(f"  ✗ Error fetching posts: {e}")
        return {"posts": []}

def update_post_tags(post_id: int, tag_ids: List[int]) -> bool:
    """Update post tags"""
    payload = json.dumps({"tags": tag_ids})
    cmd = ['gh', 'api', '-X', 'POST', f'{BASE_URL}/posts/{post_id}',
           '-f', f'tags={payload}']

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=5)
        return True
    except:
        return False

def process_category(category_id: int, tag_ids: List[int]) -> Dict[str, Any]:
    """Process all posts in a category"""
    success_count = 0
    skip_count = 0
    total_posts = 0

    page = 1
    while True:
        posts = fetch_posts_by_category(category_id, page)

        if not posts:
            break

        page_posts = posts if isinstance(posts, list) else posts.get('posts', [])
        if not page_posts:
            break

        for post in page_posts:
            post_id = post.get('id')
            existing_tags = post.get('tags', [])
            total_posts += 1

            # Only update if missing tags
            if not existing_tags:
                if update_post_tags(post_id, tag_ids):
                    success_count += 1
                time.sleep(0.05)
            else:
                skip_count += 1

        page += 1
        if total_posts >= 500:  # Limit per category
            break

    return {
        "category_id": category_id,
        "success": success_count,
        "skipped": skip_count,
        "total": total_posts
    }

def main():
    print("=" * 70)
    print(f"YOLO LAB - 標籤批量分配 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    all_categories = list(TAG_MAPPING.keys())
    grand_total_success = 0
    grand_total_skip = 0
    results = []

    for idx, category_id in enumerate(all_categories, 1):
        tag_ids = TAG_MAPPING[category_id]
        print(f"\n[{idx}/{len(all_categories)}] 分類 {category_id} | 標籤: {tag_ids}")

        result = process_category(category_id, tag_ids)
        results.append(result)

        grand_total_success += result["success"]
        grand_total_skip += result["skipped"]

        print(f"  ✓ 成功: {result['success']} | 跳過: {result['skipped']} | 總計: {result['total']}")

        # Progress report
        if grand_total_success % 300 == 0 and grand_total_success > 0:
            print(f"\n【進度報告】已完成 {grand_total_success} 篇文章")

    print("\n" + "=" * 70)
    print("完成!")
    print("=" * 70)
    print(f"✓ 成功分配: {grand_total_success} 篇")
    print(f"⊘ 已有標籤: {grand_total_skip} 篇")
    print(f"分類數: {len(results)}")

if __name__ == "__main__":
    main()
