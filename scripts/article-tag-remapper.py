#!/usr/bin/env python3
"""
Article Tag Remapper for YOLO LAB
Remaps articles from old tags to new super-tag clusters
"""

import json
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Any
import sys

SITE_ID = 133512998
BASE_URL = f"https://public-api.wordpress.com/wp/v2/sites/{SITE_ID}"

# Load super-tag taxonomy
TAXONOMY_FILE = "docs/tag-architecture/super-tag-taxonomy.json"

# Tag remapping: old tag ID -> new super-tag ID
# Based on super-tag-taxonomy.json merge strategy
TAG_REMAP = {
    # Music cluster remaps
    96990599: 96990595,   # HIPHOP-NEWS (3 tags) -> MUSIC (96990595)
    96990600: 96990595,
    96990601: 96990595,
    96990602: 96990595,   # HIPHOP-INTRO -> MUSIC
    96990603: 96990595,
    96990604: 96990595,
    96990605: 96990595,   # HIPHOP-NEW-SONGS -> MUSIC
    96990606: 96990595,
    96990607: 96990595,
    96990608: 96990595,   # HIPHOP-EVENT -> MUSIC
    96990609: 96990595,
    96990610: 96990595,
    96990611: 96990595,   # MUSIC-EVENTS -> MUSIC
    96990612: 96990595,
    96990613: 96990595,   # MUSIC-PERSONA -> MUSIC
    96990614: 96990595,
    96990615: 96990595,
    96990616: 96990595,   # YOLO-LYRICS -> MUSIC (decision: merge)
    96990617: 96990595,
    96990618: 96990595,

    # Entertainment cluster remaps
    96990619: 96990642,   # FILM-INTRO (3 tags) -> ENTERTAINMENT (96990642)
    96990620: 96990642,
    96990621: 96990642,
    96990622: 96990642,   # TV-SERIES -> ENTERTAINMENT
    96990623: 96990642,
    96990624: 96990642,
    96990625: 96990642,   # ANIME -> ENTERTAINMENT
    96990626: 96990642,
    96990627: 96990642,
    96990628: 96990642,   # CLASSIC-FILMS -> ENTERTAINMENT
    96990629: 96990642,
    96990630: 96990642,
    96990631: 96990642,   # FILM-PERSONA -> ENTERTAINMENT
    96990632: 96990642,
    96990633: 96990642,
    96990634: 96990642,   # FILM-EVENTS -> ENTERTAINMENT
    96990635: 96990642,
    96990636: 96990642,
    96990637: 96990642,   # GAMES -> ENTERTAINMENT
    96990638: 96990642,
    96990639: 96990642,
    96990640: 96990642,   # GAMES-NEWS -> ENTERTAINMENT
    96990641: 96990642,

    # Culture cluster remaps
    96990657: 96990660,   # EVENTS (3 tags) -> CULTURE (96990660 = PERSONA)
    96990658: 96990660,
    96990659: 96990660,
    96990663: 96990660,   # AUTHOR-PERSONA -> CULTURE
    96990664: 96990660,
    96990665: 96990660,   # BUSINESS-PERSONA -> CULTURE
    96990666: 96990660,
    96990667: 96990660,
    96990668: 96990660,   # RAGNAROK-PERSONA -> CULTURE (decision: merge)
    96990669: 96990660,
    96990670: 96990660,
    96990671: 96990660,   # SEXY-PERSONA -> CULTURE (decision: merge)
    96990672: 96990660,
    96990673: 96990660,
    96990674: 96990660,   # CLASSIC -> CULTURE
    96990675: 96990660,
    96990676: 96990660,   # CLASSIC-BOOKS -> CULTURE
    96990677: 96990660,
    96990678: 96990660,
    96990679: 96990660,   # CLASSIC-EVENTS -> CULTURE
    96990680: 96990660,
    96990681: 96990660,
    96990682: 96990660,   # CLASSIC-WORKS -> CULTURE
    96990683: 96990660,
    96990684: 96990660,

    # Tech cluster remaps
    96990648: 96990645,   # TECH-PERSONA (3 tags) -> TECH-NEWS (96990645)
    96990649: 96990645,
    96990650: 96990645,

    # Sports cluster remaps
    96990654: 96990651,   # SPORTS-PERSONA (3 tags) -> SPORTS-NEWS (96990651)
    96990655: 96990651,
    96990656: 96990651,
}

# Preserved core tags (no remapping)
PRESERVED_TAGS = {96990595, 96990596, 96990597, 96990598,  # MUSIC core
                  96990642, 96990643, 96990644,            # ENTERTAINMENT core
                  96990660, 96990661, 96990662,            # CULTURE core
                  96990645, 96990646, 96990647,            # TECH-NEWS
                  96990651, 96990652, 96990653}            # SPORTS-NEWS


def fetch_articles_by_tag(tag_id: int, page: int = 1, per_page: int = 100) -> tuple:
    """Fetch articles with a specific tag"""
    query = f"?tags={tag_id}&status=publish&per_page={per_page}&page={page}&_fields=id,title,tags"
    cmd = ["gh", "api", f"{BASE_URL}/posts{query}"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return (data if isinstance(data, list) else []), True
        else:
            return [], False
    except Exception as e:
        print(f"  ✗ Error fetching articles: {e}")
        return [], False


def update_article_tags(post_id: int, new_tags: List[int], dry_run: bool = False) -> bool:
    """Update article tags"""
    if dry_run:
        return True

    payload = json.dumps({"tags": new_tags})
    cmd = ["gh", "api", "-X", "POST", f"{BASE_URL}/posts/{post_id}",
           "-f", f"tags={payload}"]

    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=True)
        return True
    except Exception as e:
        print(f"    ✗ Error updating post {post_id}: {e}")
        return False


def remap_article_tags(old_tags: List[int]) -> List[int]:
    """Remap old tags to new super-tags, preserving core tags"""
    new_tags = []

    for tag_id in old_tags:
        if tag_id in PRESERVED_TAGS:
            # Keep preserved tags as-is
            new_tags.append(tag_id)
        elif tag_id in TAG_REMAP:
            # Remap old tag to new super-tag
            new_tag_id = TAG_REMAP[tag_id]
            if new_tag_id not in new_tags:  # Avoid duplicates
                new_tags.append(new_tag_id)
        else:
            # Keep wildcard/uncategorized tags as-is
            new_tags.append(tag_id)

    return new_tags


def main():
    print("🚀 YOLO LAB Article Tag Remapper\n")

    # Parse arguments
    dry_run = "--dry-run" in sys.argv
    sample = "--sample" in sys.argv
    sample_count = 20
    batch_size = 50
    delay = 0.5

    # Parse optional sample count
    if sample and len(sys.argv) > sys.argv.index("--sample") + 1:
        try:
            sample_count = int(sys.argv[sys.argv.index("--sample") + 1])
        except:
            pass

    print(f"📋 Configuration:")
    print(f"  Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"  Sample: {sample_count if sample else 'Full'} articles")
    print(f"  Batch size: {batch_size}")
    print(f"  Delay: {delay}s\n")

    # Initialize stats
    total_processed = 0
    total_remapped = 0
    total_failed = 0
    migration_log = {
        "timestamp": datetime.now().isoformat(),
        "mode": "dry_run" if dry_run else "live",
        "statistics": {
            "total_processed": 0,
            "total_remapped": 0,
            "total_failed": 0,
            "total_skipped": 0,
        },
        "remappings": [],
    }

    # Fetch all articles that need remapping
    print("📂 Fetching articles with old tags...")
    all_articles = []

    for tag_id in TAG_REMAP.keys():
        articles, success = fetch_articles_by_tag(tag_id)
        if success:
            all_articles.extend(articles)
        time.sleep(0.1)

    # Deduplicate by post ID
    seen = set()
    unique_articles = []
    for article in all_articles:
        if article["id"] not in seen:
            seen.add(article["id"])
            unique_articles.append(article)

    print(f"  Found {len(unique_articles)} unique articles\n")

    if sample:
        unique_articles = unique_articles[:sample_count]
        print(f"  Using sample: {len(unique_articles)} articles\n")

    # Process articles in batches
    print(f"📊 Processing articles...")
    for idx, article in enumerate(unique_articles, 1):
        post_id = article["id"]
        old_tags = article.get("tags", [])
        new_tags = remap_article_tags(old_tags)

        # Check if tags changed
        if set(old_tags) == set(new_tags):
            migration_log["statistics"]["total_skipped"] += 1
            continue

        # Update tags
        if update_article_tags(post_id, new_tags, dry_run=dry_run):
            total_remapped += 1
            migration_log["remappings"].append({
                "post_id": post_id,
                "title": article.get("title", "Unknown")[:50],
                "old_tags": old_tags,
                "new_tags": new_tags,
                "timestamp": datetime.now().isoformat(),
            })
        else:
            total_failed += 1

        total_processed += 1

        # Progress report every 50
        if total_processed % 50 == 0:
            print(f"  ✓ Progress: {total_processed}/{len(unique_articles)} processed")

        # Rate limiting
        if not dry_run and idx < len(unique_articles):
            if idx % batch_size == 0:
                time.sleep(delay)

    # Update stats
    migration_log["statistics"]["total_processed"] = total_processed
    migration_log["statistics"]["total_remapped"] = total_remapped
    migration_log["statistics"]["total_failed"] = total_failed

    # Save migration log
    if not dry_run:
        log_file = "docs/tag-architecture/migration-logs.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(migration_log, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Migration log saved: {log_file}")

    # Summary
    print(f"\n{'='*60}")
    print(f"📊 REMAPPING SUMMARY")
    print(f"{'='*60}")
    print(f"Total Processed: {total_processed}")
    print(f"✅ Remapped: {total_remapped}")
    print(f"❌ Failed: {total_failed}")
    print(f"⊘ Skipped: {migration_log['statistics']['total_skipped']}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"{'='*60}\n")

    if dry_run:
        print("💡 Run without --dry-run to apply remappings")


if __name__ == "__main__":
    main()
