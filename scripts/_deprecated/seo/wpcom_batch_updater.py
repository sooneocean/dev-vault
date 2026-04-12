#!/usr/bin/env python3
"""
YOLOLAB wpcom-mcp Batch Updater
用 wpcom-mcp 自動逐篇更新 SEO 元數據
"""

import json
import time
import subprocess
import urllib.request
import urllib.parse
import base64
import os
from datetime import datetime

# ============ 配置 ============
SITE_URL = "yololab.net"
API_ENDPOINT = f"https://public-api.wordpress.com/rest/v1.1/sites/{SITE_URL}"
PER_PAGE = 20
TOTAL_PAGES = 136

class WpcomSEOUpdater:
    def __init__(self):
        self.updated_count = 0
        self.failed_count = 0
        self.error_log = []
        self.user = os.environ.get("WP_USER")
        self.passwd = os.environ.get("WP_PASS")

    def fetch_posts(self, page: int) -> list:
        """用 REST API 獲取一頁文章"""
        url = f"{API_ENDPOINT}/posts"
        params = urllib.parse.urlencode({
            "page": page,
            "per_page": PER_PAGE,
            "orderby": "id",
            "order": "desc"
        })
        
        full_url = f"{url}?{params}"
        
        try:
            req = urllib.request.Request(full_url)
            if self.user and self.passwd:
                creds = base64.b64encode(f"{self.user}:{self.passwd}".encode()).decode()
                req.add_header('Authorization', f'Basic {creds}')
            
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data.get("posts", [])
        except Exception as e:
            self.error_log.append(f"Page {page}: Fetch failed - {str(e)}")
            return []

    def generate_seo_content(self, title: str, excerpt: str) -> tuple:
        """生成 SEO 標題和描述"""
        import re
        title = re.sub(r'<[^>]+>', '', title).replace('&nbsp;', ' ')[:60]
        excerpt = re.sub(r'<[^>]+>', '', excerpt).replace('&nbsp;', ' ')[:155]
        return title, excerpt

    def update_post_seo(self, post_id: int, seo_title: str, seo_desc: str) -> bool:
        """用 REST API 更新單篇文章 SEO 元數據"""
        url = f"{API_ENDPOINT}/posts/{post_id}"
        
        data = urllib.parse.urlencode({
            "meta[jetpack_seo_html_title]": seo_title,
            "meta[advanced_seo_description]": seo_desc
        }).encode('utf-8')
        
        try:
            req = urllib.request.Request(url, data=data, method='POST')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            if self.user and self.passwd:
                creds = base64.b64encode(f"{self.user}:{self.passwd}".encode()).decode()
                req.add_header('Authorization', f'Basic {creds}')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status in [200, 201]:
                    self.updated_count += 1
                    return True
        except urllib.error.HTTPError as e:
            if e.code == 403:
                self.error_log.append(f"Post {post_id}: Permission denied (403)")
            else:
                self.error_log.append(f"Post {post_id}: HTTP {e.code}")
        except Exception as e:
            self.error_log.append(f"Post {post_id}: {str(e)}")
        
        self.failed_count += 1
        return False

    def process_page(self, page: int) -> tuple:
        """處理單個分頁"""
        print(f"\n📄 Page {page}...", end=" ", flush=True)
        
        posts = self.fetch_posts(page)
        if not posts:
            print(f"⚠️ 無文章")
            return 0, 0
        
        success = 0
        failed = 0
        
        for post in posts:
            post_id = post.get("ID")
            title = post.get("title", "")
            excerpt = post.get("excerpt", "")
            
            if not title:
                continue
            
            seo_title, seo_desc = self.generate_seo_content(title, excerpt)
            
            if self.update_post_seo(post_id, seo_title, seo_desc):
                success += 1
            else:
                failed += 1
            
            time.sleep(0.3)
        
        print(f"✅ {success}/{len(posts)}")
        return success, failed

    def run_batch(self, start_page: int = 1, end_page: int = 136):
        """批量更新"""
        print(f"\n🚀 YOLOLAB SEO 批量優化")
        print(f"📊 範圍：Page {start_page} - {end_page}")
        print(f"⏰ 開始：{datetime.now().strftime('%H:%M:%S')}")
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
        print(f"✨ 完成！成功：{total_success} | 失敗：{total_failed} | 耗時：{elapsed:.0f}s")
        
        if self.error_log:
            print(f"\n⚠️ 前 5 條錯誤：")
            for error in self.error_log[:5]:
                print(f"   {error}")

if __name__ == "__main__":
    updater = WpcomSEOUpdater()
    updater.run_batch(1, 136)
