#!/usr/bin/env python3
"""
Tag Audit Generator for YOLO LAB
Queries WordPress.com API to fetch all tags, analyze usage patterns, and identify redundancy
"""

import os
import json
import subprocess
from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict

SITE_ID = 133512998
BASE_URL = f"https://public-api.wordpress.com/wp/v2/sites/{SITE_ID}"

# Category names mapped from bulk_tags_final.py
CATEGORY_NAMES = {
    96987488: "MUSIC",
    96987493: "HIPHOP-NEWS",
    96987631: "HIPHOP-INTRO",
    96987492: "HIPHOP-NEW-SONGS",
    1982: "HIPHOP-EVENT",
    96990388: "MUSIC-EVENTS",
    96990386: "MUSIC-PERSONA",
    96988967: "YOLO-LYRICS",
    96987489: "ENTERTAINMENT",
    96990383: "FILM-INTRO",
    96990384: "TV-SERIES",
    96990499: "ANIME",
    96990522: "CLASSIC-FILMS",
    96990390: "FILM-PERSONA",
    96990387: "FILM-EVENTS",
    96990424: "GAMES",
    96990427: "GAMES-NEWS",
    96990096: "TECH-NEWS",
    96990518: "TECH-PERSONA",
    96990391: "SPORTS-NEWS",
    96990517: "SPORTS-PERSONA",
    96990120: "EVENTS",
    96990389: "PERSONA",
    96990524: "AUTHOR-PERSONA",
    96990555: "BUSINESS-PERSONA",
    96990519: "RAGNAROK-PERSONA",
    96990554: "SEXY-PERSONA",
    96990521: "CLASSIC",
    96990523: "CLASSIC-BOOKS",
    96990525: "CLASSIC-EVENTS",
    96990532: "CLASSIC-WORKS",
}

# Tag mapping from bulk_tags_final.py
TAG_MAPPING = {
    96987488: [96990595, 96990596, 96990597, 96990598],
    96987493: [96990599, 96990600, 96990601],
    96987631: [96990602, 96990603, 96990604],
    96987492: [96990605, 96990606, 96990607],
    1982: [96990608, 96990609, 96990610],
    96990388: [96990611, 96990612],
    96990386: [96990613, 96990614, 96990615],
    96988967: [96990616, 96990617, 96990618],
    96987489: [96990642, 96990643, 96990644],
    96990383: [96990619, 96990620, 96990621],
    96990384: [96990622, 96990623, 96990624],
    96990499: [96990625, 96990626, 96990627],
    96990522: [96990628, 96990629, 96990630],
    96990390: [96990631, 96990632, 96990633],
    96990387: [96990634, 96990635, 96990636],
    96990424: [96990637, 96990638, 96990639],
    96990427: [96990640, 96990641],
    96990096: [96990645, 96990646, 96990647],
    96990518: [96990648, 96990649, 96990650],
    96990391: [96990651, 96990652, 96990653],
    96990517: [96990654, 96990655, 96990656],
    96990120: [96990657, 96990658, 96990659],
    96990389: [96990660, 96990661, 96990662],
    96990524: [96990663, 96990664],
    96990555: [96990665, 96990666, 96990667],
    96990519: [96990668, 96990669, 96990670],
    96990554: [96990671, 96990672, 96990673],
    96990521: [96990674, 96990675],
    96990523: [96990676, 96990677, 96990678],
    96990525: [96990679, 96990680, 96990681],
    96990532: [96990682, 96990683, 96990684],
}


def fetch_all_tags() -> List[Dict[str, Any]]:
    """Fetch all tags from WordPress.com API using gh cli"""
    print("📊 Fetching all tags from WordPress.com...")
    all_tags = []
    page = 1
    per_page = 100

    while True:
        query = f"?per_page={per_page}&page={page}&_fields=id,name,slug,count,description"
        cmd = ["gh", "api", f"{BASE_URL}/tags{query}"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            tags = json.loads(result.stdout)

            if not tags or len(tags) == 0:
                break

            all_tags.extend(tags)
            print(f"  ✓ Page {page}: {len(tags)} tags fetched")
            page += 1

        except Exception as e:
            print(f"  ✗ Error fetching tags on page {page}: {e}")
            break

    return all_tags


def categorize_tags(all_tags: List[Dict], tag_mapping: Dict) -> Dict[str, Any]:
    """Categorize tags by their category assignment"""
    # Flatten tag_mapping for reverse lookup (tag_id -> category_id)
    tag_to_category = {}
    for category_id, tag_ids in tag_mapping.items():
        for tag_id in tag_ids:
            tag_to_category[tag_id] = category_id

    categorized = defaultdict(list)
    uncategorized = []

    for tag in all_tags:
        tag_id = tag["id"]
        category_id = tag_to_category.get(tag_id)

        if category_id:
            category_name = CATEGORY_NAMES.get(category_id, f"UNKNOWN-{category_id}")
            categorized[category_name].append(tag)
        else:
            uncategorized.append(tag)

    return {
        "categorized": dict(categorized),
        "uncategorized": uncategorized,
        "total_categorized": sum(len(v) for v in categorized.values()),
        "total_uncategorized": len(uncategorized),
    }


def identify_redundancy(categorized: Dict) -> Dict[str, List[str]]:
    """Identify redundant/similar tags for consolidation"""
    print("\n🔍 Analyzing semantic redundancy...")

    redundancy_patterns = defaultdict(list)

    # Pattern 1: Multiple PERSONA tags
    for category, tags in categorized.items():
        if "PERSONA" in category:
            redundancy_patterns["PERSONA_TAGS"].extend([t["slug"] for t in tags])

    # Pattern 2: Multiple NEWS tags
    for category, tags in categorized.items():
        if "NEWS" in category:
            redundancy_patterns["NEWS_TAGS"].extend([t["slug"] for t in tags])

    # Pattern 3: Multiple EVENT tags
    for category, tags in categorized.items():
        if "EVENT" in category:
            redundancy_patterns["EVENT_TAGS"].extend([t["slug"] for t in tags])

    # Pattern 4: Multiple INTRO tags
    for category, tags in categorized.items():
        if "INTRO" in category:
            redundancy_patterns["INTRO_TAGS"].extend([t["slug"] for t in tags])

    # Pattern 5: Low-usage tags (< 5 posts)
    low_usage = []
    for category, tags in categorized.items():
        for tag in tags:
            if tag.get("count", 0) < 5:
                low_usage.append(
                    {
                        "slug": tag["slug"],
                        "category": category,
                        "count": tag.get("count", 0),
                    }
                )

    if low_usage:
        redundancy_patterns["LOW_USAGE_TAGS"] = sorted(
            low_usage, key=lambda x: x["count"]
        )

    return redundancy_patterns


def generate_audit_report(all_tags: List[Dict], categorized: Dict, redundancy: Dict):
    """Generate JSON audit report"""
    audit_report = {
        "timestamp": datetime.now().isoformat(),
        "site_id": SITE_ID,
        "summary": {
            "total_tags": len(all_tags),
            "categorized_tags": categorized["total_categorized"],
            "uncategorized_tags": categorized["total_uncategorized"],
            "total_categories": len(categorized["categorized"]),
        },
        "tags_by_category": {},
        "uncategorized_tags": categorized["uncategorized"],
        "redundancy_analysis": redundancy,
    }

    # Detailed category breakdown
    for category, tags in categorized["categorized"].items():
        audit_report["tags_by_category"][category] = {
            "count": len(tags),
            "tags": [
                {
                    "id": t["id"],
                    "name": t["name"],
                    "slug": t["slug"],
                    "post_count": t.get("count", 0),
                    "description": t.get("description", ""),
                }
                for t in sorted(tags, key=lambda x: x.get("count", 0), reverse=True)
            ],
            "total_posts": sum(t.get("count", 0) for t in tags),
        }

    return audit_report


def generate_redundancy_markdown(redundancy: Dict, categorized: Dict) -> str:
    """Generate Markdown redundancy analysis"""
    md = """# Tag Redundancy Analysis for YOLO LAB

## Executive Summary

This analysis identifies semantic overlap and consolidation candidates among YOLO LAB's 80+ tags.

## Redundancy Patterns

### 1. PERSONA Tags (Consolidation Candidates)

Multiple "PERSONA" tags should be consolidated into a single "Personalities" super-tag cluster.

"""

    if "PERSONA_TAGS" in redundancy:
        md += f"**Found {len(redundancy['PERSONA_TAGS'])} PERSONA tags:**\n\n"
        md += "| Tag Slug | Category | Usage |\n"
        md += "|----------|----------|-------|\n"

        # Find usage for each persona tag
        for tag_slug in sorted(set(redundancy["PERSONA_TAGS"])):
            for category, tags in categorized.items():
                for tag in tags:
                    if tag["slug"] == tag_slug:
                        usage = tag.get("count", 0)
                        md += f"| `{tag_slug}` | {category} | {usage} posts |\n"
                        break

    md += """

**Recommendation:** Consolidate these into a single "Personalities" tag cluster with 10-15 related tags.

---

### 2. NEWS Tags (Consolidation Candidates)

Multiple "NEWS" tags should be consolidated into a single "News & Updates" super-tag cluster.

"""

    if "NEWS_TAGS" in redundancy:
        md += f"**Found {len(redundancy['NEWS_TAGS'])} NEWS tags:**\n\n"
        md += "| Tag Slug | Category | Usage |\n"
        md += "|----------|----------|-------|\n"

        for tag_slug in sorted(set(redundancy["NEWS_TAGS"])):
            for category, tags in categorized.items():
                for tag in tags:
                    if tag["slug"] == tag_slug:
                        usage = tag.get("count", 0)
                        md += f"| `{tag_slug}` | {category} | {usage} posts |\n"
                        break

    md += """

**Recommendation:** Consolidate into a single "News & Updates" tag cluster.

---

### 3. EVENT Tags (Consolidation Candidates)

Multiple "EVENT" tags should be consolidated into a single "Events & Culture" super-tag cluster.

"""

    if "EVENT_TAGS" in redundancy:
        md += f"**Found {len(redundancy['EVENT_TAGS'])} EVENT tags:**\n\n"
        md += "| Tag Slug | Category | Usage |\n"
        md += "|----------|----------|-------|\n"

        for tag_slug in sorted(set(redundancy["EVENT_TAGS"])):
            for category, tags in categorized.items():
                for tag in tags:
                    if tag["slug"] == tag_slug:
                        usage = tag.get("count", 0)
                        md += f"| `{tag_slug}` | {category} | {usage} posts |\n"
                        break

    md += """

**Recommendation:** Consolidate into a single "Events & Culture" tag cluster.

---

### 4. INTRO Tags (Consolidation Candidates)

Multiple "INTRO" tags suggest different entry-point categories. Evaluate whether to preserve or consolidate.

"""

    if "INTRO_TAGS" in redundancy:
        md += f"**Found {len(redundancy['INTRO_TAGS'])} INTRO tags:**\n\n"
        md += "| Tag Slug | Category | Usage |\n"
        md += "|----------|----------|-------|\n"

        for tag_slug in sorted(set(redundancy["INTRO_TAGS"])):
            for category, tags in categorized.items():
                for tag in tags:
                    if tag["slug"] == tag_slug:
                        usage = tag.get("count", 0)
                        md += f"| `{tag_slug}` | {category} | {usage} posts |\n"
                        break

    md += """

**Recommendation:** Preserve but organize under respective parent clusters (Music, Entertainment, etc).

---

### 5. Low-Usage Tags (< 5 posts)

These tags have minimal content and should be consolidated or deprecated.

"""

    if "LOW_USAGE_TAGS" in redundancy:
        md += f"**Found {len(redundancy['LOW_USAGE_TAGS'])} tags with < 5 posts:**\n\n"
        md += "| Tag Slug | Category | Posts |\n"
        md += "|----------|----------|-------|\n"

        for item in redundancy["LOW_USAGE_TAGS"][:20]:  # Show top 20
            md += f"| `{item['slug']}` | {item['category']} | {item['count']} |\n"

        if len(redundancy["LOW_USAGE_TAGS"]) > 20:
            md += f"\n*(... and {len(redundancy['LOW_USAGE_TAGS']) - 20} more low-usage tags)*\n"

    md += """

**Recommendation:** Merge these into appropriate super-tag clusters. Consider deprecating if no relevant parent category.

---

## Summary of Consolidation Strategy

### Current State
- **30 Categories** with mixed naming (English/Chinese)
- **80+ Tags** distributed across categories
- **Multiple semantic clusters** (PERSONA, NEWS, EVENT, INTRO, etc.)
- **Low-usage tags** creating thin content

### Proposed State (5-7 Super-Tag Clusters)
1. **Music** (10-15 tags: Hip-Hop News, Hip-Hop Intro, Hip-Hop New Songs, Music Events, Lyrics, Persona, etc.)
2. **Entertainment** (10-15 tags: Film, TV, Anime, Games, Personas, News, etc.)
3. **Tech** (3-5 tags: Tech News, Tech Personas, Events)
4. **Sports** (3-5 tags: Sports News, Sports Personas)
5. **Culture** (5-8 tags: Events, Personas, Classics, Business Personas, etc.)
6. **Trending** (cross-cutting, optional)
7. **Interviews** (cross-cutting, optional)

### Benefits
- Reduced cognitive load for readers
- Better content discovery
- Improved topical clustering for SEO
- Consolidated tag pages with richer content
- E-E-A-T signals for Google SGE

---

## Next Steps

1. **Unit 2:** Design super-tag taxonomy and merge strategy
2. **Unit 3:** Create tag descriptions and templates
3. **Unit 4:** Generate SEO metadata and schema markup
4. **Unit 5:** Build metadata update script
5. **Unit 6:** Implement tag remapping and 301 redirects
6. **Unit 7:** QA and verification
7. **Unit 8:** Tag governance and future rules

"""

    return md


def main():
    print("🚀 YOLO LAB Tag Audit Generator\n")

    # Fetch all tags
    all_tags = fetch_all_tags()
    print(f"\n✅ Total tags fetched: {len(all_tags)}\n")

    # Categorize and analyze
    categorized = categorize_tags(all_tags, TAG_MAPPING)
    redundancy = identify_redundancy(categorized["categorized"])

    # Generate reports
    audit_report = generate_audit_report(all_tags, categorized, redundancy)
    redundancy_md = generate_redundancy_markdown(redundancy, categorized["categorized"])

    # Save reports
    output_dir = "docs/tag-architecture"
    os.makedirs(output_dir, exist_ok=True)

    # Save JSON audit
    audit_file = os.path.join(output_dir, "tag-audit-report.json")
    with open(audit_file, "w", encoding="utf-8") as f:
        json.dump(audit_report, f, indent=2, ensure_ascii=False)
    print(f"✅ Audit report saved: {audit_file}")

    # Save Markdown redundancy analysis
    redundancy_file = os.path.join(output_dir, "tag-redundancy-analysis.md")
    with open(redundancy_file, "w", encoding="utf-8") as f:
        f.write(redundancy_md)
    print(f"✅ Redundancy analysis saved: {redundancy_file}")

    # Print summary
    print(f"\n{'='*60}")
    print(f"📊 TAG AUDIT SUMMARY")
    print(f"{'='*60}")
    print(f"Total Tags in WordPress.com: {len(all_tags)}")
    print(f"  - Managed Tags (via TAG_MAPPING): {audit_report['summary']['categorized_tags']}")
    print(f"  - Unmanaged/Wildcard Tags: {audit_report['summary']['uncategorized_tags']}")
    print(f"\n✅ FOCUS: Optimizing {audit_report['summary']['categorized_tags']} managed tags + 80+ related tags")
    print(f"⏸️  DEFER: Wildcard tags (1 post each) will be evaluated in Unit 2\n")
    print(f"Categories in TAG_MAPPING: {audit_report['summary']['total_categories']}")
    print(f"\nTop 5 Uncategorized Tags by Usage:")
    sorted_uncategorized = sorted(
        audit_report["uncategorized_tags"],
        key=lambda x: x.get("count", 0),
        reverse=True
    )[:5]
    for tag in sorted_uncategorized:
        print(f"  - {tag['slug']}: {tag.get('count', 0)} posts")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
