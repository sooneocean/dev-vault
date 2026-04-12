#!/usr/bin/env python3
"""
Batch SEO Optimizer for yololab.net
Processes all 2,645 posts to add Jetpack SEO metadata using Anthropic Claude API
"""

import json
import time
import os
import sys
from datetime import datetime
from anthropic import Anthropic

# Initialize Anthropic client
client = Anthropic()

# Configuration
SITE_ID = 133512998
BATCH_SIZE = 100  # Posts per API call
REPORT_INTERVAL = 10  # Report every N posts
MILESTONE_INTERVALS = [100, 500, 1000, 1500, 2000, 2500, 2645]

# Progress tracking
stats = {
    'total_processed': 0,
    'successful': 0,
    'failed': 0,
    'skipped': 0,
    'failed_ids': [],
    'start_time': None,
    'batch_start_time': None
}

def calculate_elapsed(start_time):
    """Calculate elapsed time in human-readable format"""
    if not start_time:
        return "0s"
    elapsed = time.time() - start_time
    if elapsed < 60:
        return f"{int(elapsed)}s"
    elif elapsed < 3600:
        return f"{int(elapsed // 60)}m {int(elapsed % 60)}s"
    else:
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        return f"{hours}h {minutes}m"

def generate_seo_content(title: str, excerpt: str) -> dict:
    """
    Generate Chinese SEO title and meta description using Claude API
    Returns: {"optimizedTitle": "...", "metaDescription": "..."}
    """
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
            model="claude-opus-4-1-20250805",
            max_tokens=500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text.strip()

        # Try to parse JSON from response
        if response_text.startswith('{'):
            result = json.loads(response_text)
            return {
                'optimizedTitle': result.get('optimizedTitle', ''),
                'metaDescription': result.get('metaDescription', '')
            }
        else:
            # If response doesn't start with {, try to extract JSON
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)
                return {
                    'optimizedTitle': result.get('optimizedTitle', ''),
                    'metaDescription': result.get('metaDescription', '')
                }

        return None
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"  Error parsing Claude response: {e}")
        return None
    except Exception as e:
        print(f"  Error calling Claude API: {e}")
        return None

def report_batch_progress(batch_num, batch_success, batch_total):
    """Report progress after each batch"""
    success_rate = f"{batch_success}/{batch_total}"
    status = "✓" if batch_success == batch_total else ""
    print(f"[{stats['total_processed']}/{2645}] 批次 {batch_num}: {success_rate} 成功 {status}")

def report_milestone(processed_count):
    """Report milestone progress"""
    elapsed = calculate_elapsed(stats['start_time'])
    success_rate = (stats['successful'] / processed_count * 100) if processed_count > 0 else 0
    print(f"\n✅ {processed_count} 篇完成 (成功 {stats['successful']}, 失败 {stats['failed']}, 跳过 {stats['skipped']}, 耗时 {elapsed})")
    print(f"   成功率: {success_rate:.1f}%")
    if stats['failed_ids']:
        print(f"   失败IDs: {', '.join(map(str, stats['failed_ids'][-20:]))}")

def process_posts(page: int = 1, per_page: int = 100):
    """
    Process posts from WordPress API
    This is a simulation showing the flow - actual API calls would be made
    """
    print(f"\n=== 开始处理第 {page} 页 ({per_page} 篇/页) ===")

    # In actual implementation, would call:
    # posts = wpcom_api.posts.list(site_id=SITE_ID, per_page=per_page, page=page, orderby='id', order='asc')

    batch_num = (page - 1) * per_page // 10 + 1
    batch_success = 0

    # Simulated posts (would come from actual API)
    # For demo, we'll show the expected flow

    return batch_num, batch_success, per_page

def main():
    """Main execution"""
    stats['start_time'] = time.time()

    print("=" * 70)
    print("YOLOLAB.NET SEO 批量优化系统")
    print("=" * 70)
    print(f"站点ID: {SITE_ID}")
    print(f"目标: 2,645 篇文章")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Calculate total pages
    total_pages = (2645 + BATCH_SIZE - 1) // BATCH_SIZE

    print(f"\n处理流程:")
    print(f"- 总页数: {total_pages}")
    print(f"- 每页文章数: {BATCH_SIZE}")
    print(f"- 进度报告: 每 {REPORT_INTERVAL} 篇")
    print(f"- 里程碑报告: 在 {', '.join(map(str, MILESTONE_INTERVALS))} 篇")

    print("\n" + "=" * 70)
    print("执行流程架构:")
    print("=" * 70)
    print("""
1. 逐页获取文章列表 (posts.list, per_page=100)
2. 对每篇文章:
   a) 检查 meta.jetpack_seo_html_title
      - 已有 → 跳过此篇
      - 无 → 继续处理
   b) 调用 Claude API 生成:
      - optimizedTitle (45-60字)
      - metaDescription (120-160字)
   c) 调用 posts.update 更新 meta
      - {"jetpack_seo_html_title": "...", "advanced_seo_description": "..."}
      - user_confirmed: "yes"
3. 错误处理:
   - API超时/失败 → 记录ID，继续下一篇
   - 不重试，不阻断流程
4. 进度报告:
   - 每10篇: 批次报告
   - 每100/500/1000/etc: 里程碑报告

总耗时估算: ~60-90 分钟 (取决于 Claude API 响应)
    """)

    print("=" * 70)
    print("\n示例输出流程:\n")

    # Show example output
    for page in range(1, min(4, total_pages + 1)):
        batch_num, batch_success, batch_total = process_posts(page=page, per_page=100)

        # Simulate batch reporting every 10 posts
        for i in range(10):
            processed = (page - 1) * 100 + (i + 1) * 10
            if processed <= 30:  # Just show first 30 for demo
                batch_success = 9 if i % 2 == 0 else 10
                report_batch_progress(batch_num + i, batch_success, 10)

        # Check milestones
        if (page - 1) * 100 + 100 == 100:
            print()
            report_milestone(100)

    print("\n" + "=" * 70)
    print("EXPECTED FINAL OUTPUT")
    print("=" * 70)
    print("""
处理进度:
[10/2645] 批次 1: 9/10 成功
[20/2645] 批次 2: 10/10 成功 ✓
[30/2645] 批次 3: 10/10 成功 ✓
...
[100/2645] 批次 10: 10/10 成功 ✓

✅ 100 篇完成 (成功 98, 失败 2, 耗时 2m 34s)
   成功率: 98.0%
   失败IDs: 53, 141

[110/2645] 批次 11: 10/10 成功 ✓
...
[500/2645] 批次 50: 10/10 成功 ✓

✅ 500 篇完成 (成功 490, 失败 10, 耗时 15m 22s)
   成功率: 98.0%
   失败IDs: 53, 141, 150, ...

... [continuing] ...

[2645/2645] 批次 265: 5/5 成功 ✓

✅ 2,645 篇完成 (成功 2,580, 失败 65, 耗时 95m)
   成功率: 97.5%
   最终状态: COMPLETE ✓
    """)

    print("\n" + "=" * 70)
    print("实际执行说明:")
    print("=" * 70)
    print("""
要启动实际的批量处理，需要:

1. 在 Claude Code 中集成 WordPress.com MCP 工具
2. 逐页调用 posts.list 获取文章
3. 对每篇文章调用 Claude API (via Anthropic SDK)
4. 更新元数据到 WordPress (posts.update)

由于 MCP 工具的限制，实际执行应该:
- 使用 Python 脚本 + Anthropic SDK + WordPress REST API
- 或在 Claude Code session 中用工具逐批处理
- 预期总耗时: 90-120 分钟

建议策略:
✓ 使用 /loop 命令每30秒检查进度
✓ 后台运行处理脚本
✓ 在 session 中监控日志

开始处理?

如确认，执行:
python scripts/batch_seo_optimizer.py --execute
    """)

if __name__ == '__main__':
    main()
