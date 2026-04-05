#!/usr/bin/env python3
"""
CEWF Batch Publisher
Automates publishing subtype: article notes from Obsidian to WordPress.
"""

import os
import re
import json
import yaml
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

# ============ Configuration ============
VAULT_ROOT = Path(__file__).parent.parent
RESOURCE_DIR = VAULT_ROOT / "resources"
SITE_URL = "yololab.net"
API_ENDPOINT = f"https://public-api.wordpress.com/rest/v1.1/sites/{SITE_URL}"
WP_TOKEN = os.getenv("WP_TOKEN")

def get_draft_articles():
    """Find all articles with publish_status: draft"""
    articles = []
    for file in RESOURCE_DIR.glob("*.md"):
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.startswith("---"):
                continue
            
            try:
                # Extract frontmatter
                parts = content.split("---", 2)
                if len(parts) < 3:
                    continue
                
                frontmatter = yaml.safe_all(parts[1])
                data = next(frontmatter)
                
                if data.get("subtype") == "article" and data.get("publish_status") == "draft":
                    articles.append({
                        "path": file,
                        "frontmatter": data,
                        "body": parts[2].strip()
                    })
            except Exception as e:
                print(f"Error parsing {file.name}: {e}")
    
    return articles

def publish_to_wp(article):
    """Publish a single article to WordPress"""
    if not WP_TOKEN:
        print("Error: WP_TOKEN environment variable not set.")
        return None

    title = article["frontmatter"].get("title")
    content = article["body"]
    excerpt = article["frontmatter"].get("excerpt", "")
    
    # Remove H1 if it's the same as the title
    content = re.sub(r'^# .*\n', '', content)
    
    # Prepare API request
    url = f"{API_ENDPOINT}/posts/new"
    data = urllib.parse.urlencode({
        "title": title,
        "content": content,
        "excerpt": excerpt,
        "status": "publish",
        "meta[jetpack_seo_html_title]": title,
        "meta[advanced_seo_description]": excerpt
    }).encode('utf-8')

    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Authorization', f'Bearer {WP_TOKEN}')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')

    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return {
                "id": res_data.get("ID"),
                "url": res_data.get("URL")
            }
    except Exception as e:
        print(f"Failed to publish {title}: {e}")
        return None

def update_note(article, wp_result):
    """Update Obsidian note frontmatter after publishing"""
    path = article["path"]
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Update frontmatter fields
    content = re.sub(r'publish_status: draft', 'publish_status: published', content)
    content = re.sub(r'wordpress_id: null', f'wordpress_id: {wp_result["id"]}', content)
    content = re.sub(r'canonical_url: null', f'canonical_url: "{wp_result["url"]}"', content)
    content = re.sub(r'updated: ".*"', f'updated: "{datetime.now().strftime("%Y-%m-%d")}"', content)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated {path.name}")

def main():
    print(f"🚀 CEWF Batch Publisher - Target: {SITE_URL}")
    
    articles = get_draft_articles()
    if not articles:
        print("No draft articles found.")
        return

    print(f"Found {len(articles)} draft(s). Proceeding to publish...")
    
    for article in articles:
        print(f"Publishing: {article['frontmatter']['title']}...", end=" ", flush=True)
        result = publish_to_wp(article)
        if result:
            print(f"✅ ID: {result['id']}")
            update_note(article, result)
        else:
            print("❌ Failed")

if __name__ == "__main__":
    main()
