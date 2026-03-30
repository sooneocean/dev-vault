#!/usr/bin/env python3
"""
YOLOLAB SEO Batch Updater
批量优化 yololab.net 所有文章的 SEO 元数据 (jetpack_seo_html_title 和 advanced_seo_description)
"""

import requests
import json
import time
import sys
from typing import Dict, List, Tuple
from datetime import datetime

# ============ 配置 ============
SITE_URL = "yololab.net"
API_ENDPOINT = f"https://public-api.wordpress.com/rest/v1.1/sites/{SITE_URL}"
PER_PAGE = 20
TOTAL_PAGES = 136
RETRY_LIMIT = 3
RETRY_DELAY = 2

# SEO 生成规则（中文）
SEO_TEMPLATES = {
    "default": {
        "title_format": "{main_keyword} | {sub_keyword}",
        "desc_format": "{main_keyword}深度解析。{key_insight1}。{key_insight2}。立即了解这场{topic_type}的影响与前景。"
    }
}

# ============ SEO 内容库 ============
# 从已优化的文章中学习模式
OPTIMIZED_SAMPLES = {
    34196: {
        "title": "笑声与热力学：为什么幽默感是大脑冷却系统",
        "desc": "从物理学角度解析笑声本质。当大脑预测崩塌，多余能量如何排出？幽默感作为心灵散热器的科学真相，让你的大脑核心永不掉速。"
    },
    34190: {
        "title": "ADHD奇点时刻：如何靠AI协作成为创意主场",
        "desc": "执行力已变廉价，你的创意噪音才是真金。如何利用AI补足ADHD大脑最弱的前额叶功能，将思绪跳跃转化为竞争武器。现在就学会驾驭这场技术奇点。"
    }
}

class SEOGenerator:
    """SEO 内容生成器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'YOLOLAB-SEO-Batch-Updater/1.0'
        })
        self.updated_count = 0
        self.failed_count = 0
        self.error_log = []

    def fetch_post(self, post_id: int) -> Dict:
        """获取单篇文章信息"""
        url = f"{API_ENDPOINT}/posts/{post_id}"
        params = {"context": "edit", "fields": "id,title,excerpt"}

        for attempt in range(RETRY_LIMIT):
            try:
                resp = self.session.get(url, params=params, timeout=10)
                resp.raise_for_status()
                return resp.json().get("post", {})
            except Exception as e:
                if attempt < RETRY_LIMIT - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                self.error_log.append(f"Post {post_id}: Fetch failed - {str(e)}")
                return {}

    def generate_seo_content(self, post_id: int, title: str, excerpt: str) -> Tuple[str, str]:
        """
        基于文章标题和摘要生成 SEO 标题和描述
        规则：
        - 标题：55-60 字符（中文）
        - 描述：155-160 字符（中文）
        """

        # 清理 HTML
        title = self._clean_html(title)
        excerpt = self._clean_html(excerpt)

        # 从标题提取关键词
        keywords = self._extract_keywords(title)

        # 生成 SEO 标题 (优先使用模板，限制长度)
        seo_title = title[:60] if len(title) <= 60 else title[:57] + "..."

        # 生成 SEO 描述 (从摘要截断或扩展)
        if len(excerpt) > 155:
            seo_desc = excerpt[:152] + "..."
        else:
            # 补充关键词信息
            seo_desc = f"{excerpt} 深入了解{keywords[0] if keywords else ''}的前景。"
            seo_desc = seo_desc[:160]

        return seo_title, seo_desc

    def _clean_html(self, text: str) -> str:
        """移除 HTML 标签"""
        import re
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
        return text.strip()

    def _extract_keywords(self, text: str) -> List[str]:
        """从标题提取主要关键词"""
        # 简单的分割策略：以冒号/竖线分割
        parts = [p.strip() for p in text.replace('|', '：').split('：')]
        return parts[:2]

    def update_post_seo(self, post_id: int, seo_title: str, seo_desc: str) -> bool:
        """更新单篇文章的 SEO 元数据"""
        url = f"{API_ENDPOINT}/posts/{post_id}"

        # 使用括号标记法（REST API 支持的方式）
        data = {
            f"meta[jetpack_seo_html_title]": seo_title,
            f"meta[advanced_seo_description]": seo_desc
        }

        for attempt in range(RETRY_LIMIT):
            try:
                resp = self.session.post(url, data=data, timeout=10)
                if resp.status_code in [200, 201]:
                    self.updated_count += 1
                    return True
                elif resp.status_code == 403:
                    self.error_log.append(f"Post {post_id}: Permission denied")
                    self.failed_count += 1
                    return False
            except requests.Timeout:
                if attempt < RETRY_LIMIT - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                    continue
            except Exception as e:
                self.error_log.append(f"Post {post_id} (attempt {attempt+1}): {str(e)}")

        self.failed_count += 1
        return False

    def process_page(self, page: int, start_post_id: int = None) -> Tuple[int, int]:
        """处理单个分页"""
        print(f"\n📄 处理 Page {page}...")

        # 获取该页的文章列表
        url = f"{API_ENDPOINT}/posts"
        params = {
            "page": page,
            "per_page": PER_PAGE,
            "orderby": "id",
            "order": "desc",
            "fields": "id,title,excerpt"
        }

        try:
            resp = self.session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            posts = resp.json().get("posts", [])
        except Exception as e:
            print(f"❌ Page {page} 获取失败: {e}")
            return 0, 0

        if not posts:
            print(f"⚠️ Page {page} 无文章")
            return 0, 0

        success = 0
        failed = 0

        for i, post in enumerate(posts):
            post_id = post.get("id")
            title = post.get("title", "")
            excerpt = post.get("excerpt", "")

            # 生成 SEO 内容
            seo_title, seo_desc = self.generate_seo_content(post_id, title, excerpt)

            # 更新文章
            if self.update_post_seo(post_id, seo_title, seo_desc):
                success += 1
                status = "✅"
            else:
                failed += 1
                status = "❌"

            # 进度显示
            progress = f"[{i+1}/{len(posts)}]"
            print(f"  {status} {progress} Post {post_id}: {title[:30]}...")

            # 速率限制：每秒最多 2 个请求
            time.sleep(0.5)

        return success, failed

    def run_batch_update(self, start_page: int = 6, end_page: int = 136):
        """批量更新所有页面"""
        print(f"🚀 开始批量 SEO 优化")
        print(f"📊 范围：Page {start_page} - Page {end_page}")
        print(f"⏰ 开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"=" * 60)

        start_time = time.time()
        total_success = 0
        total_failed = 0

        for page in range(start_page, end_page + 1):
            success, failed = self.process_page(page)
            total_success += success
            total_failed += failed

            # 每处理 10 页显示一次进度汇总
            if page % 10 == 0:
                elapsed = time.time() - start_time
                rate = (page - start_page + 1) / (elapsed / 60)  # 页/分钟
                remaining_pages = end_page - page
                eta_minutes = remaining_pages / rate if rate > 0 else 0
                print(f"\n📈 进度：{page}/{end_page} | 成功：{total_success} | 失败：{total_failed} | 预计剩余时间：{eta_minutes:.1f}分钟\n")

        elapsed = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"✨ 批量更新完成！")
        print(f"📊 统计结果：")
        print(f"   ✅ 成功：{total_success} 篇")
        print(f"   ❌ 失败：{total_failed} 篇")
        print(f"   ⏱️ 耗时：{elapsed:.1f} 秒 ({elapsed/60:.1f} 分钟)")
        print(f"   📈 速率：{(total_success + total_failed) / elapsed:.1f} 篇/秒")
        print(f"⏰ 完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if self.error_log:
            print(f"\n⚠️ 错误日志 ({len(self.error_log)} 条)：")
            for error in self.error_log[:10]:  # 仅显示前 10 条
                print(f"   - {error}")
            if len(self.error_log) > 10:
                print(f"   ... 还有 {len(self.error_log) - 10} 条错误")

def main():
    """主程序入口"""
    import argparse

    parser = argparse.ArgumentParser(description="YOLOLAB SEO 批量优化工具")
    parser.add_argument("--start-page", type=int, default=6, help="起始页码（默认：6）")
    parser.add_argument("--end-page", type=int, default=136, help="结束页码（默认：136）")
    parser.add_argument("--test", action="store_true", help="测试模式（仅处理前 3 页）")

    args = parser.parse_args()

    if args.test:
        args.start_page = 6
        args.end_page = 8
        print("🧪 进入测试模式（仅处理 Page 6-8）")

    updater = SEOGenerator()
    updater.run_batch_update(args.start_page, args.end_page)

if __name__ == "__main__":
    main()
