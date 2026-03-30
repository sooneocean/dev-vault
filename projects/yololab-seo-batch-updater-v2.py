#!/usr/bin/env python3
"""
YOLOLAB SEO Batch Updater v2
使用内置库实现批量 SEO 优化（无需外部依赖）
"""

import urllib.request
import urllib.parse
import json
import time
import sys
import os
from typing import Dict, Tuple
from datetime import datetime

# ============ 配置 ============
SITE_URL = "yololab.net"
API_ENDPOINT = f"https://public-api.wordpress.com/rest/v1.1/sites/{SITE_URL}"
PER_PAGE = 20
TOTAL_PAGES = 136
RETRY_LIMIT = 3
RETRY_DELAY = 1

class SEOGenerator:
    """SEO 内容生成器"""

    def __init__(self):
        self.updated_count = 0
        self.failed_count = 0
        self.error_log = []

    def fetch_posts(self, page: int) -> list:
        """获取一页文章列表"""
        url = f"{API_ENDPOINT}/posts"
        params = urllib.parse.urlencode({
            "page": page,
            "per_page": PER_PAGE,
            "orderby": "id",
            "order": "desc"
        })

        full_url = f"{url}?{params}"
        user = os.environ.get("WP_USER")
        passwd = os.environ.get("WP_PASS")

        for attempt in range(RETRY_LIMIT):
            try:
                req = urllib.request.Request(full_url)
                if user and passwd:
                    import base64
                    creds = base64.b64encode(f"{user}:{passwd}".encode()).decode()
                    req.add_header('Authorization', f'Basic {creds}')
                with urllib.request.urlopen(req, timeout=15) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    return data.get("posts", [])
            except Exception as e:
                if attempt < RETRY_LIMIT - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                self.error_log.append(f"Page {page}: Fetch failed - {str(e)}")
                return []

    def generate_seo_content(self, title: str, excerpt: str) -> Tuple[str, str]:
        """生成 SEO 标题和描述"""
        # 清理 HTML
        title = self._clean_html(title)
        excerpt = self._clean_html(excerpt)

        # 生成 SEO 标题 (55-60 字符中文)
        seo_title = title[:60] if len(title) <= 60 else title[:57] + "..."

        # 生成 SEO 描述 (155-160 字符中文)
        if len(excerpt) > 155:
            seo_desc = excerpt[:152] + "..."
        else:
            seo_desc = excerpt[:160]

        return seo_title, seo_desc

    def _clean_html(self, text: str) -> str:
        """移除 HTML 标签"""
        import re
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
        return text.strip()

    def update_post_seo(self, post_id: int, seo_title: str, seo_desc: str) -> bool:
        """更新单篇文章 SEO 元数据"""
        url = f"{API_ENDPOINT}/posts/{post_id}"
        user = os.environ.get("WP_USER")
        passwd = os.environ.get("WP_PASS")

        # Use JSON payload instead of form-urlencoded for better WordPress.com API support
        payload = json.dumps({
            "title": seo_title,
            "excerpt": seo_desc
        }).encode('utf-8')

        for attempt in range(RETRY_LIMIT):
            try:
                req = urllib.request.Request(url, data=payload, method='POST')
                req.add_header('Content-Type', 'application/json')
                if user and passwd:
                    import base64
                    creds = base64.b64encode(f"{user}:{passwd}".encode()).decode()
                    req.add_header('Authorization', f'Basic {creds}')
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status in [200, 201]:
                        self.updated_count += 1
                        return True
            except urllib.error.HTTPError as e:
                if e.code == 403:
                    self.error_log.append(f"Post {post_id}: Permission denied (403)")
                    self.failed_count += 1
                    return False
                elif e.code == 400:
                    self.error_log.append(f"Post {post_id}: Bad request (400) - {e.reason}")
                    self.failed_count += 1
                    return False
            except Exception as e:
                if attempt < RETRY_LIMIT - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                self.error_log.append(f"Post {post_id}: {str(e)}")

        self.failed_count += 1
        return False

    def process_page(self, page: int) -> Tuple[int, int]:
        """处理单个分页"""
        print(f"\n📄 Page {page}...", end=" ", flush=True)

        posts = self.fetch_posts(page)
        if not posts:
            print(f"⚠️ 无文章")
            return 0, 0

        success = 0
        failed = 0

        for i, post in enumerate(posts):
            post_id = post.get("ID")  # WordPress API returns uppercase ID
            title = post.get("title", "")
            excerpt = post.get("excerpt", "")

            if not title:
                continue

            # 生成 SEO 内容
            seo_title, seo_desc = self.generate_seo_content(title, excerpt)

            # 更新
            if self.update_post_seo(post_id, seo_title, seo_desc):
                success += 1
            else:
                failed += 1

            # 速率限制
            time.sleep(0.3)

        print(f"✅ {success}/{len(posts)}")
        return success, failed

    def run_batch(self, start_page: int = 6, end_page: int = 136):
        """批量更新"""
        print(f"\n🚀 YOLOLAB SEO 批量优化启动")
        print(f"📊 范围：Page {start_page} - {end_page}")
        print(f"⏰ 开始：{datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")

        start_time = time.time()
        total_success = 0
        total_failed = 0

        for page in range(start_page, end_page + 1):
            success, failed = self.process_page(page)
            total_success += success
            total_failed += failed

            if page % 20 == 0 and page > start_page:
                elapsed = time.time() - start_time
                rate = (page - start_page + 1) / elapsed
                remaining = (end_page - page) / rate if rate > 0 else 0
                print(f"   📈 {page}/{end_page} | 成功：{total_success} | ETA: {remaining:.0f}s")

        elapsed = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"✨ 完成！成功：{total_success} | 失败：{total_failed} | 耗时：{elapsed:.0f}s")

        if self.error_log:
            print(f"\n⚠️ 前 5 条错误：")
            for error in self.error_log[:5]:
                print(f"   {error}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=6)
    parser.add_argument("--end", type=int, default=136)
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    if args.test:
        args.start = 6
        args.end = 8

    updater = SEOGenerator()
    updater.run_batch(args.start, args.end)
