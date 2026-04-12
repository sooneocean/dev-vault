#!/usr/bin/env python3
"""
YOLOLAB SEO 批量优化 - wpcom-mcp 版本
改进版本：包含完整错误处理与重试机制
"""

import urllib.request
import urllib.parse
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple

# ============ 配置 ============
SITE_URL = "yololab.net"
API_ENDPOINT = f"https://public-api.wordpress.com/rest/v1.1/sites/{SITE_URL}"
PER_PAGE = 20
START_PAGE = 7
END_PAGE = 136
RETRY_LIMIT = 3
RETRY_DELAY = 1.5
REQUEST_TIMEOUT = 15

class WpcomSEOUpdater:
    """WordPress.com SEO 批量优化器"""

    def __init__(self):
        self.total_updated = 0
        self.total_failed = 0
        self.error_log = []
        self.start_time = time.time()

    def fetch_posts_safe(self, page: int) -> List[Dict]:
        """安全获取单页文章"""
        url = f"{API_ENDPOINT}/posts"
        params = urllib.parse.urlencode({
            "page": page,
            "per_page": PER_PAGE,
            "orderby": "id",
            "order": "desc"
        })
        full_url = f"{url}?{params}"

        for attempt in range(RETRY_LIMIT):
            try:
                with urllib.request.urlopen(full_url, timeout=REQUEST_TIMEOUT) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    posts = data.get("posts", [])
                    if posts:
                        return posts
                    return []
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return []
                if attempt < RETRY_LIMIT - 1:
                    time.sleep(RETRY_DELAY)
            except Exception as e:
                if attempt < RETRY_LIMIT - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    self.error_log.append(f"Page {page}: Fetch error - {str(e)[:60]}")
        return []

    def generate_seo_content(self, title: str, excerpt: str) -> Tuple[str, str]:
        """生成 SEO 标题和描述"""
        import re
        
        # 清理 HTML
        title = re.sub(r'<[^>]+>', '', title).strip()
        excerpt = re.sub(r'<[^>]+>', '', excerpt).strip()
        
        # SEO 标题 (55-60 字)
        seo_title = title[:60] if len(title) <= 60 else title[:57] + "..."
        
        # SEO 描述 (155-160 字)
        seo_desc = excerpt[:155] if len(excerpt) <= 155 else excerpt[:152] + "..."
        
        return seo_title, seo_desc

    def update_post(self, post_id: int, seo_title: str, seo_desc: str) -> bool:
        """更新单篇文章的 SEO 元数据"""
        url = f"{API_ENDPOINT}/posts/{post_id}"
        
        # 构建请求数据
        data = urllib.parse.urlencode({
            "meta[jetpack_seo_html_title]": seo_title,
            "meta[advanced_seo_description]": seo_desc
        }).encode('utf-8')

        for attempt in range(RETRY_LIMIT):
            try:
                req = urllib.request.Request(url, data=data, method='POST')
                req.add_header('Content-Type', 'application/x-www-form-urlencoded')
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status in [200, 201]:
                        self.total_updated += 1
                        return True
                    
            except urllib.error.HTTPError as e:
                if e.code == 403:
                    # 权限问题 - 可能需要认证
                    self.error_log.append(f"Post {post_id}: 403 Forbidden")
                    self.total_failed += 1
                    return False
                elif e.code >= 500 and attempt < RETRY_LIMIT - 1:
                    time.sleep(RETRY_DELAY)
                    continue
            except Exception as e:
                if attempt < RETRY_LIMIT - 1:
                    time.sleep(RETRY_DELAY)
                    continue
        
        self.total_failed += 1
        return False

    def process_page(self, page: int) -> Tuple[int, int]:
        """处理单个页面"""
        print(f"📄 Page {page}...", end=" ", flush=True)
        
        posts = self.fetch_posts_safe(page)
        if not posts:
            print(f"⚠️ 无数据")
            return 0, 0

        success = 0
        failed = 0

        for post in posts:
            post_id = post.get("ID")
            if not post_id:
                continue
            
            title = post.get("title", "")
            excerpt = post.get("excerpt", "")
            
            if not title:
                continue

            seo_title, seo_desc = self.generate_seo_content(title, excerpt)
            
            if self.update_post(post_id, seo_title, seo_desc):
                success += 1
                print("✅", end="", flush=True)
            else:
                failed += 1
                print("❌", end="", flush=True)
            
            # 速率限制
            time.sleep(0.5)

        print(f" {success}/{len(posts)}")
        return success, failed

    def run(self):
        """执行批量更新"""
        print(f"\n🚀 YOLOLAB SEO 批量优化 (wpcom-mcp 版本)")
        print(f"📊 范围：Page {START_PAGE} - {END_PAGE}")
        print(f"⏰ 开始：{datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}\n")

        total_success = 0
        total_failed = 0

        try:
            for page in range(START_PAGE, END_PAGE + 1):
                success, failed = self.process_page(page)
                total_success += success
                total_failed += failed

                # 每 20 页显示进度
                if page % 20 == 0 or page == END_PAGE:
                    elapsed = time.time() - self.start_time
                    elapsed_min = elapsed / 60
                    rate = (page - START_PAGE + 1) / (elapsed + 0.1)
                    eta_min = (END_PAGE - page) / (rate + 0.1)
                    progress = ((page - START_PAGE + 1) / (END_PAGE - START_PAGE + 1)) * 100
                    
                    print(f"   📈 {page}/{END_PAGE} ({progress:.0f}%) | ✅{total_success} ❌{total_failed} | ETA: {eta_min:.0f}min")

        except KeyboardInterrupt:
            print(f"\n⚠️ 用户中断")
        except Exception as e:
            print(f"\n❌ 错误: {str(e)}")

        # 最终报告
        elapsed = time.time() - self.start_time
        print(f"\n{'='*60}")
        print(f"✨ 完成！")
        print(f"  ✅ 成功：{total_success} 篇")
        print(f"  ❌ 失败：{total_failed} 篇")
        print(f"  ⏱️  耗时：{elapsed/60:.1f} 分钟")
        print(f"  📊 成功率：{(total_success/(total_success+total_failed)*100):.1f}%" if (total_success+total_failed) > 0 else "  📊 成功率：N/A")
        
        if self.error_log:
            print(f"\n⚠️ 前 3 条错误：")
            for error in self.error_log[:3]:
                print(f"   • {error}")

if __name__ == "__main__":
    updater = WpcomSEOUpdater()
    updater.run()
