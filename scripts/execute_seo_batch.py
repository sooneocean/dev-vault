#!/usr/bin/env python3
"""
Batch SEO Optimizer - EXECUTION VERSION
Processes all 2,645 posts from yololab.net using Anthropic Claude API
"""

import json
import time
import os
import sys
import requests
from datetime import datetime
from urllib.parse import urljoin
from anthropic import Anthropic

# Initialize Anthropic client
client = Anthropic()

# Configuration
SITE_ID = 133512998
SITE_URL = "https://yololab.net"
WP_REST_API = urljoin(SITE_URL, "/wp-json/wp/v2/")
BATCH_SIZE = 100
REPORT_INTERVAL = 10

# Get WordPress token from environment
WP_TOKEN = os.getenv('WP_REST_API_TOKEN', '')

# Progress tracking
stats = {
    'total_processed': 0,
    'successful': 0,
    'failed': 0,
    'skipped': 0,
    'failed_ids': [],
    'start_time': datetime.now(),
}

def calculate_elapsed():
    """Calculate elapsed time"""
    elapsed = (datetime.now() - stats['start_time']).total_seconds()
    if elapsed < 60:
        return f"{int(elapsed)}s"
    elif elapsed < 3600:
        return f"{int(elapsed // 60)}m {int(elapsed % 60)}s"
    else:
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        return f"{hours}h {minutes}m"

def generate_seo_content(title: str, excerpt: str) -> dict:
    """Generate Chinese SEO content using Claude"""
    prompt = f"""请为以下文章生成中文SEO优化内容。

文章标题: {title}
文章摘要: {excerpt}

要求:
1. SEO标题：45-60个中文字符，包含关键词，吸引点击
2. Meta描述：120-160个中文字符，简洁概括内容亮点

请以JSON格式返回（不要包含markdown代码块）:
{{"optimizedTitle": "...", "metaDescription": "..."}}"""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text.strip()

        # Parse JSON response
        if response_text.startswith('{'):
            result = json.loads(response_text)
        else:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx == -1:
                return None
            json_str = response_text[start_idx:end_idx]
            result = json.loads(json_str)

        return {
            'optimizedTitle': result.get('optimizedTitle', ''),
            'metaDescription': result.get('metaDescription', '')
        }
    except Exception as e:
        print(f"  ⚠ Claude API error: {e}")
        return None

def fetch_posts(page: int = 1, per_page: int = 100) -> list:
    """Fetch posts from WordPress REST API"""
    try:
        url = urljoin(WP_REST_API, "posts/")
        params = {
            'per_page': per_page,
            'page': page,
            'orderby': 'id',
            'order': 'asc',
            '_fields': 'id,title,excerpt,meta'
        }
        headers = {
            'Authorization': f'Bearer {WP_TOKEN}' if WP_TOKEN else None
        }

        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  ⚠ Error fetching posts page {page}: {e}")
        return []

def update_post_seo(post_id: int, seo_data: dict) -> bool:
    """Update post with SEO metadata"""
    try:
        url = urljoin(WP_REST_API, f"posts/{post_id}/")
        payload = {
            'meta': {
                'jetpack_seo_html_title': seo_data['optimizedTitle'],
                'advanced_seo_description': seo_data['metaDescription']
            }
        }
        headers = {
            'Authorization': f'Bearer {WP_TOKEN}' if WP_TOKEN else None
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"  ⚠ Error updating post {post_id}: {e}")
        return False

def process_batch(posts: list) -> dict:
    """Process a batch of posts"""
    batch_stats = {
        'processed': 0,
        'success': 0,
        'failed': 0,
        'skipped': 0
    }

    for post in posts:
        post_id = post.get('id')
        title = post.get('title', {}).get('rendered', '')
        excerpt = post.get('excerpt', {}).get('rendered', '')
        meta = post.get('meta', {})

        # Check if SEO title already exists
        if meta.get('jetpack_seo_html_title'):
            batch_stats['skipped'] += 1
            stats['skipped'] += 1
            continue

        # Generate SEO content
        seo_data = generate_seo_content(title, excerpt)
        if not seo_data or not seo_data['optimizedTitle']:
            batch_stats['failed'] += 1
            stats['failed'] += 1
            stats['failed_ids'].append(post_id)
            continue

        # Update post
        if update_post_seo(post_id, seo_data):
            batch_stats['success'] += 1
            stats['successful'] += 1
        else:
            batch_stats['failed'] += 1
            stats['failed'] += 1
            stats['failed_ids'].append(post_id)

        batch_stats['processed'] += 1
        time.sleep(0.5)  # Rate limiting

    return batch_stats

def main():
    """Main execution"""
    print("=" * 70)
    print("YOLOLAB.NET SEO 批量优化 - 执行模式")
    print("=" * 70)
    print(f"开始时间: {stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总目标: 2,645 篇文章")
    print()

    # Estimated 27 pages (100 posts per page)
    total_pages = 27

    milestone_intervals = [100, 500, 1000, 1500, 2000, 2500, 2645]
    next_milestone_idx = 0

    for page in range(1, total_pages + 1):
        posts = fetch_posts(page=page, per_page=BATCH_SIZE)
        if not posts:
            break

        batch_stats = process_batch(posts)
        stats['total_processed'] += batch_stats['processed']

        # Report every 10 posts
        if stats['total_processed'] % REPORT_INTERVAL == 0:
            success_emoji = "✓" if batch_stats['failed'] == 0 else ""
            print(f"[{stats['total_processed']}/2645] 批次 {page}: {batch_stats['success']}/{batch_stats['processed']} 成功 {success_emoji}")

        # Check milestones
        if next_milestone_idx < len(milestone_intervals):
            milestone = milestone_intervals[next_milestone_idx]
            if stats['total_processed'] >= milestone:
                success_rate = (stats['successful'] / stats['total_processed'] * 100) if stats['total_processed'] > 0 else 0
                elapsed = calculate_elapsed()
                print()
                print(f"✅ {milestone} 篇完成 (成功 {stats['successful']}, 失败 {stats['failed']}, 跳过 {stats['skipped']}, 耗时 {elapsed})")
                print(f"   成功率: {success_rate:.1f}%")
                if stats['failed_ids']:
                    print(f"   失败IDs: {', '.join(map(str, stats['failed_ids'][-20:]))}")
                print()
                next_milestone_idx += 1

    # Final report
    print("=" * 70)
    elapsed = calculate_elapsed()
    success_rate = (stats['successful'] / stats['total_processed'] * 100) if stats['total_processed'] > 0 else 0
    print(f"✅ 处理完成！")
    print(f"总耗时: {elapsed}")
    print(f"总处理: {stats['total_processed']}")
    print(f"成功: {stats['successful']} ({success_rate:.1f}%)")
    print(f"失败: {stats['failed']}")
    print(f"跳过: {stats['skipped']}")
    if stats['failed_ids']:
        print(f"失败IDs: {', '.join(map(str, stats['failed_ids']))}")
    print("=" * 70)

if __name__ == '__main__':
    # Check for token
    if not WP_TOKEN:
        print("⚠ 警告: 未设置 WP_REST_API_TOKEN")
        print("   设置方法: export WP_REST_API_TOKEN='your-token'")
        print()

    main()
