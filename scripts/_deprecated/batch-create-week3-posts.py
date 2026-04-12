#!/usr/bin/env python3
"""
Batch create Week 3 posts to WordPress.com with scheduled publish times
Posts: Article 6-15, scheduled for 2026-04-15 to 2026-04-19
"""

import os
import re
import json
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

# Configuration
SITE_URL = "yololab.net"
API_ENDPOINT = f"https://public-api.wordpress.com/rest/v1.1/sites/{SITE_URL}"
WP_TOKEN = os.getenv("WP_TOKEN")
PUBLISHING_DIR = Path(__file__).parent.parent / "docs" / "publishing"

# Article metadata with publication timestamps (UTC+8)
ARTICLES = [
    {
        "file": "article-06-kpop-neogen.md",
        "title": "K-pop 二代團怎麼贏 BLACKPINK？粉絲經濟軍備競賽解碼",
        "slug": "kpop-neogen-fan-economy-2026",
        "publish_date": "2026-04-15T18:00:00+08:00",
        "category": "Music",
        "tags": ["K-pop", "粉絲經濟", "NewJeans", "IVE", "應援色"]
    },
    {
        "file": "article-07-taylor-political.md",
        "title": "Taylor Swift 從政治中立到公然對抗，52 億美元帝國怎麼被綁架了",
        "slug": "taylor-swift-political-transformation-2026",
        "publish_date": "2026-04-15T19:00:00+08:00",
        "category": "Music",
        "tags": ["Taylor-Swift", "政治言論", "Eras-Tour"]
    },
    {
        "file": "article-08-indie-pop.md",
        "title": "Phoebe Bridgers 怎麼變成奢侈品？獨立音樂的反商業悖論",
        "slug": "indie-pop-luxury-paradox-2026",
        "publish_date": "2026-04-16T18:00:00+08:00",
        "category": "Music",
        "tags": ["Indie-Pop", "Phoebe-Bridgers", "身份消費"]
    },
    {
        "file": "article-09-tiktok-spotify.md",
        "title": "抖音超越 Spotify？音樂產業的碎片化時代來臨",
        "slug": "tiktok-spotify-music-fragmentation-2026",
        "publish_date": "2026-04-16T19:00:00+08:00",
        "category": "Music",
        "tags": ["TikTok", "Spotify", "音樂產業", "短視頻"]
    },
    {
        "file": "article-10-hollywood-q2.md",
        "title": "好萊塢 2026 Q2 檔期崩盤：110 億製片成本 vs 全球票房腰斬",
        "slug": "hollywood-q2-2026-box-office-collapse",
        "publish_date": "2026-04-17T18:00:00+08:00",
        "category": "Film",
        "tags": ["Hollywood", "票房危機", "大片檔期"]
    },
    {
        "file": "article-11-deadpool.md",
        "title": "Deadpool 3 內地禁映：好萊塢創意自由的最後一戰",
        "slug": "deadpool-3-china-censorship-2026",
        "publish_date": "2026-04-17T19:00:00+08:00",
        "category": "Film",
        "tags": ["Deadpool", "電影審查", "中國市場"]
    },
    {
        "file": "article-12-netflix-cinema.md",
        "title": "Netflix 為什麼要殺死院線？2026 年串流 vs 電影院的最後一戰",
        "slug": "netflix-cinema-death-2026",
        "publish_date": "2026-04-18T18:00:00+08:00",
        "category": "Film",
        "tags": ["Netflix", "院線", "串流戰爭"]
    },
    {
        "file": "article-13-disney-ip.md",
        "title": "迪士尼版權帝國為什麼在衰退？2026 年從 IP 壟斷到 IP 洗牌",
        "slug": "disney-ip-empire-2026-crisis",
        "publish_date": "2026-04-18T19:00:00+08:00",
        "category": "Film",
        "tags": ["Disney", "版權", "IP帝國", "漫威"]
    },
    {
        "file": "article-14-google-io.md",
        "title": "Google I/O 2026 的 AI 助理陷阱：隱私幻象 vs 個性化欲望",
        "slug": "google-io-ai-assistant-privacy-paradox-2026",
        "publish_date": "2026-04-19T18:00:00+08:00",
        "category": "Tech",
        "tags": ["Google", "AI", "隱私", "Google-I/O"]
    },
    {
        "file": "article-15-tiktok-transparency.md",
        "title": "TikTok 算法透明化是障眼法：歐盟強制公開背後的終極營利邏輯",
        "slug": "tiktok-algorithm-transparency-illusion-2026",
        "publish_date": "2026-04-19T19:00:00+08:00",
        "category": "Tech",
        "tags": ["TikTok", "算法", "透明化", "監管", "歐盟"]
    }
]

def read_article_content(file_path):
    """Extract body content from markdown file (skip frontmatter)"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Skip frontmatter if present
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            body = parts[2].strip()
        else:
            body = content
    else:
        body = content

    return body

def convert_md_to_html(markdown_content):
    """Convert markdown to HTML (basic conversion)"""
    # Use Pandoc if available, otherwise do basic conversion
    import subprocess
    try:
        result = subprocess.run(
            ["pandoc", "-f", "markdown", "-t", "html"],
            input=markdown_content.encode('utf-8'),
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.decode('utf-8')
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback: return markdown as-is (WordPress will handle it)
    return markdown_content

def publish_post(article_data):
    """Publish a single post via WordPress REST API"""
    if not WP_TOKEN:
        print("❌ Error: WP_TOKEN environment variable not set")
        return None

    # Read article content
    file_path = PUBLISHING_DIR / article_data["file"]
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return None

    body = read_article_content(file_path)

    # Prepare API request
    url = f"{API_ENDPOINT}/posts/new"

    post_data = {
        "title": article_data["title"],
        "content": body,
        "slug": article_data["slug"],
        "status": "future",
        "date": article_data["publish_date"],
        "categories": article_data["category"],
        "tags": ",".join(article_data["tags"])
    }

    encoded_data = urllib.parse.urlencode(post_data, doseq=True).encode('utf-8')

    req = urllib.request.Request(url, data=encoded_data, method='POST')
    req.add_header('Authorization', f'Bearer {WP_TOKEN}')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')

    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return {
                "id": res_data.get("ID"),
                "url": res_data.get("URL"),
                "slug": article_data["slug"],
                "publish_date": article_data["publish_date"]
            }
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"❌ HTTP Error {e.code}: {error_body}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    print("=" * 60)
    print("🚀 WordPress Batch Publisher - Week 3 Content")
    print(f"Target site: {SITE_URL}")
    print("=" * 60)

    if not WP_TOKEN:
        print("⚠️  Warning: WP_TOKEN not set. Please set it before publishing.")
        print("   Export WP_TOKEN=your_token to authenticate.")
        return

    results = []
    successful = 0
    failed = 0

    for i, article in enumerate(ARTICLES, 1):
        print(f"\n[{i}/10] Publishing: {article['title'][:60]}...")
        result = publish_post(article)

        if result:
            successful += 1
            results.append(result)
            print(f"✅ Post ID: {result['id']}")
            print(f"   Scheduled for: {result['publish_date']}")
        else:
            failed += 1
            print(f"❌ Failed to publish")

    # Summary report
    print("\n" + "=" * 60)
    print(f"📊 SUMMARY: {successful} ✅ / {failed} ❌")
    print("=" * 60)

    if results:
        print("\n📝 Published Posts List:")
        print("-" * 60)
        for i, result in enumerate(results, 1):
            print(f"{i}. Post ID {result['id']} | {result['publish_date']}")
            print(f"   Slug: {result['slug']}")

        # Save results to JSON
        output_file = Path(__file__).parent.parent / "docs" / "publishing" / "week3-posts-created.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "created_at": datetime.now().isoformat(),
                "successful": successful,
                "failed": failed,
                "posts": results
            }, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Results saved to: {output_file}")

if __name__ == "__main__":
    main()
