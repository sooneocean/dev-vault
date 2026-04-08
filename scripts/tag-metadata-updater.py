#!/usr/bin/env python3
"""
Tag Metadata Updater for YOLO LAB
Applies SEO metadata and schema markup to tag pages via WordPress.com REST API
"""

import json
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Any

SITE_ID = 133512998
BASE_URL = f"https://public-api.wordpress.com/wp/v2/sites/{SITE_ID}"

# Load metadata from tag-metadata.json
METADATA_FILE = "docs/tag-architecture/tag-metadata.json"


def load_metadata() -> List[Dict[str, Any]]:
    """Load tag metadata from JSON file"""
    print("📂 Loading metadata from tag-metadata.json...")
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("tags", [])
    except FileNotFoundError:
        print(f"❌ Error: {METADATA_FILE} not found")
        return []


def update_tag_metadata(tag_slug: str, metadata: Dict[str, Any], dry_run: bool = False) -> bool:
    """Update tag metadata via WordPress.com API"""
    seo = metadata.get("seo", {})
    og = metadata.get("open_graph", {})
    schema = metadata.get("schema", {})

    # Prepare update payload (Jetpack SEO fields)
    update_payload = {
        "name": metadata.get("name"),
        "description": metadata.get("name"),  # Short desc for tag admin
        "yoast_meta": {
            "title": seo.get("title"),
            "metadesc": seo.get("description"),
            "robots": seo.get("robots", "index, follow"),
            "canonical": seo.get("canonical"),
        },
    }

    # Try to store OG and schema as meta fields (WordPress.com may or may not support)
    if og:
        update_payload["yoast_meta"]["og_title"] = og.get("title")
        update_payload["yoast_meta"]["og_description"] = og.get("description")

    if schema:
        # Store schema as JSON string (may need custom field handler)
        update_payload["meta"] = {
            "schema_json": json.dumps(schema),
        }

    if dry_run:
        print(f"  [DRY RUN] Would update tag '{tag_slug}':")
        print(f"    - Title: {seo.get('title')}")
        print(f"    - Description: {seo.get('description')[:50]}...")
        return True

    # Execute API call
    cmd = [
        "gh",
        "api",
        "-X",
        "POST",
        f"{BASE_URL}/tags?slug={tag_slug}",
        "-f",
        f"name={metadata.get('name')}",
        "-f",
        f"description={metadata.get('name')}",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return True
        else:
            print(f"  ✗ Error updating tag '{tag_slug}': {result.stderr}")
            return False
    except Exception as e:
        print(f"  ✗ Exception updating tag '{tag_slug}': {e}")
        return False


def main():
    import sys

    print("🚀 YOLO LAB Tag Metadata Updater\n")

    # Parse arguments
    dry_run = "--dry-run" in sys.argv
    sample = "--sample" in sys.argv

    # Load metadata
    tags = load_metadata()
    if not tags:
        print("❌ No tags loaded. Exiting.")
        return

    print(f"📊 Loaded {len(tags)} tags for update\n")

    # Update tags
    successful = 0
    failed = 0

    for idx, tag in enumerate(tags, 1):
        tag_slug = tag.get("slug")
        tag_name = tag.get("name")

        print(f"[{idx}/{len(tags)}] Updating {tag_name} ({tag_slug})...")

        if update_tag_metadata(tag_slug, tag, dry_run=dry_run):
            successful += 1
        else:
            failed += 1

        # Rate limiting
        if not dry_run and idx < len(tags):
            time.sleep(0.5)

    # Summary
    print(f"\n{'='*60}")
    print(f"📊 UPDATE SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"Total: {len(tags)}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"{'='*60}\n")

    if dry_run:
        print("💡 Run without --dry-run to apply updates")


if __name__ == "__main__":
    main()
