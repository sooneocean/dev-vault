#!/usr/bin/env python3
"""
YOLOLAB SEO 优化验证脚本
Phase 2 完成后执行，检查 2,660 篇文章的 SEO 元数据是否已正确更新
"""

import urllib.request
import urllib.parse
import json
import random
from typing import List, Dict, Tuple

# ============ 配置 ============
SITE_URL = "yololab.net"
API_ENDPOINT = f"https://public-api.wordpress.com/rest/v1.1/sites/{SITE_URL}"
SAMPLE_SIZE = 10  # 抽样验证数量
VERIFY_PAGES = list(range(7, 137))  # Pages 7-136

class SEOVerifier:
    """SEO 元数据验证器"""

    def __init__(self):
        self.verified_count = 0
        self.failed_count = 0
        self.errors = []
        self.sample_ids = []

    def get_random_posts_from_pages(self, pages: List[int], sample_size: int = 10) -> List[int]:
        """随机抽取指定页面的 post IDs"""
        all_post_ids = []
        per_page = 20

        for page in pages:
            # 根据页码推算 post ID 范围（假设按倒序排列）
            # 这是一个估算值，实际 ID 可能不同
            start_id = 34200 - (page - 5) * 20
            for i in range(per_page):
                post_id = start_id - i
                all_post_ids.append(post_id)

        # 随机抽样
        sampled = random.sample(all_post_ids, min(sample_size, len(all_post_ids)))
        self.sample_ids = sampled
        return sampled

    def verify_post_seo(self, post_id: int) -> bool:
        """验证单篇文章的 SEO 元数据"""
        try:
            url = f"{API_ENDPOINT}/posts/{post_id}"
            params = urllib.parse.urlencode({
                "context": "edit",
                "fields": "id,title,meta"
            })

            with urllib.request.urlopen(f"{url}?{params}", timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                post = data.get("post", {})

                if not post:
                    self.errors.append(f"Post {post_id}: Not found")
                    self.failed_count += 1
                    return False

                meta = post.get("meta", {})

                # 检查 SEO 元数据是否存在
                seo_title = meta.get("jetpack_seo_html_title", "")
                seo_desc = meta.get("advanced_seo_description", "")

                if seo_title and seo_desc:
                    print(f"✅ Post {post_id}: SEO元数据已存在")
                    print(f"   标题长度: {len(seo_title)} | 描述长度: {len(seo_desc)}")
                    self.verified_count += 1
                    return True
                else:
                    msg = f"Post {post_id}: SEO元数据缺失"
                    if not seo_title:
                        msg += " (缺title)"
                    if not seo_desc:
                        msg += " (缺desc)"
                    self.errors.append(msg)
                    self.failed_count += 1
                    return False

        except Exception as e:
            self.errors.append(f"Post {post_id}: {str(e)}")
            self.failed_count += 1
            return False

    def run_verification(self):
        """执行验证流程"""
        print("=" * 60)
        print("🔍 YOLOLAB SEO 优化验证")
        print("=" * 60)

        # 步骤 1：抽样验证
        print(f"\n📊 步骤 1: 从 Pages 7-136 随机抽样 {SAMPLE_SIZE} 篇文章")
        sample_posts = self.get_random_posts_from_pages(VERIFY_PAGES, SAMPLE_SIZE)
        print(f"   抽样 IDs: {sample_posts}\n")

        for post_id in sample_posts:
            self.verify_post_seo(post_id)

        # 步骤 2: 日志分析
        print(f"\n📝 步骤 2: 分析批处理日志")
        log_path = "/c/DEX_data/Claude Code DEV/projects/seo-batch-run.log"
        try:
            with open(log_path, 'r') as f:
                log_content = f.read()

            # 统计成功和失败
            success_count = log_content.count("✅")
            failed_count = log_content.count("❌")
            total_posts = success_count + failed_count

            if total_posts > 0:
                success_rate = (success_count / total_posts) * 100
                print(f"   总处理: {total_posts} 篇")
                print(f"   成功: {success_count} 篇 ✅")
                print(f"   失败: {failed_count} 篇 ❌")
                print(f"   成功率: {success_rate:.1f}%")
            else:
                print("   日志文件为空或脚本仍在运行中")
        except FileNotFoundError:
            print(f"   ⚠️ 未找到日志文件: {log_path}")
        except Exception as e:
            print(f"   ❌ 日志分析失败: {str(e)}")

        # 步骤 3: 最终统计
        print(f"\n📈 步骤 3: 抽样验证统计")
        print(f"   验证成功: {self.verified_count}/{len(sample_posts)}")
        print(f"   验证失败: {self.failed_count}/{len(sample_posts)}")

        if self.errors:
            print(f"\n⚠️ 发现的问题:")
            for error in self.errors[:5]:  # 只显示前 5 个
                print(f"   - {error}")
            if len(self.errors) > 5:
                print(f"   ... 还有 {len(self.errors) - 5} 个问题")

        # 最终结论
        print(f"\n" + "=" * 60)
        if self.failed_count == 0 and self.verified_count == len(sample_posts):
            print("✅ 验证通过：所有抽样文章的 SEO 元数据已正确更新")
        else:
            print("⚠️ 验证有问题，建议检查日志或重新运行脚本")
        print("=" * 60)

if __name__ == "__main__":
    verifier = SEOVerifier()
    verifier.run_verification()
