#!/usr/bin/env python3
"""
SEO Scanner: Phase 1 baseline data collection
Fetches posts from WordPress.com, analyzes SEO metrics, exports CSV + JSON
"""

import json
import csv
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict, field
from html.parser import HTMLParser
from collections import defaultdict
from pathlib import Path
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('scan_seo_baseline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class SEOMetrics:
    """Core SEO metrics for a post"""
    post_id: int
    title: str
    title_len: int
    description_len: int
    h1_count: int
    internal_links: int
    images_no_alt: int
    schema_present: bool
    views_30d: int
    seo_score: int = 0
    tier: str = ""
    issues: List[Dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)


class ImageAltParser(HTMLParser):
    """Parse images and track alt text coverage"""

    def __init__(self):
        super().__init__()
        self.images = []
        self.images_without_alt = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            attrs_dict = dict(attrs)
            has_alt = 'alt' in attrs_dict and attrs_dict['alt'].strip()
            self.images.append({
                'src': attrs_dict.get('src', ''),
                'alt': attrs_dict.get('alt', ''),
                'has_alt': has_alt
            })
            if not has_alt:
                self.images_without_alt += 1


class LinkParser(HTMLParser):
    """Parse internal and external links"""

    def __init__(self, site_url: str):
        super().__init__()
        self.internal_links = 0
        self.external_links = 0
        self.site_domain = self._extract_domain(site_url)

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        match = re.search(r'https?://([^/]+)', url)
        return match.group(1) if match else ""

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            attrs_dict = dict(attrs)
            href = attrs_dict.get('href', '')

            if not href:
                return

            # Check if internal
            if self.site_domain in href or href.startswith('/'):
                self.internal_links += 1
            elif href.startswith('http'):
                self.external_links += 1


class SEOScanner:
    """Main SEO scanning engine"""

    # SEO Scoring weights
    SCORING_WEIGHTS = {
        'title_optimal': 15,
        'description_optimal': 15,
        'h1_present': 10,
        'internal_links': 12,
        'images_alt': 12,
        'schema': 10,
        'views_bonus': 10,
        'content_health': 16
    }

    # SEO Rules
    TITLE_OPTIMAL_RANGE = (55, 60)
    DESCRIPTION_OPTIMAL_RANGE = (155, 160)
    MIN_INTERNAL_LINKS = 2
    MIN_H1 = 1

    def __init__(self, site_url: str = "yololab.net", enable_mock: bool = False):
        """Initialize scanner

        Args:
            site_url: WordPress.com site URL
            enable_mock: If True, use mock data instead of real API calls
        """
        self.site_url = site_url
        self.enable_mock = enable_mock
        self.posts_processed = 0
        self.total_posts_estimate = 2700
        self.start_time = None

    def scan_posts(self, per_page: int = 100, max_pages: Optional[int] = None) -> Tuple[List[SEOMetrics], Dict]:
        """Scan all posts for SEO baseline

        Args:
            per_page: Posts per API call
            max_pages: Limit pages for testing (None = fetch all)

        Returns:
            Tuple of (metrics_list, stats_dict)
        """
        self.start_time = datetime.now()
        metrics = []
        pages_processed = 0
        current_page = 1

        logger.info(f"Starting SEO scan of {self.site_url}")
        logger.info(f"Configuration: per_page={per_page}, max_pages={max_pages}")

        try:
            while True:
                if max_pages and pages_processed >= max_pages:
                    logger.info(f"Reached max_pages limit ({max_pages})")
                    break

                # Fetch posts page
                posts = self._fetch_posts_page(current_page, per_page)
                if not posts:
                    logger.info(f"No more posts at page {current_page}")
                    break

                # Process each post
                for post in posts:
                    try:
                        metric = self._scan_post(post)
                        metrics.append(metric)
                        self.posts_processed += 1

                        # Progress display
                        if self.posts_processed % 50 == 0:
                            self._print_progress(self.posts_processed)
                    except Exception as e:
                        logger.warning(f"Failed to scan post {post.get('id', 'unknown')}: {e}")
                        continue

                pages_processed += 1
                current_page += 1

                # Rate limiting
                time.sleep(0.5)

        except Exception as e:
            logger.error(f"Fatal error during scan: {e}")
            raise

        # Calculate stats
        stats = self._calculate_stats(metrics)

        logger.info(f"Scan complete: {self.posts_processed} posts processed")
        logger.info(f"Execution time: {self._format_duration()}")

        return metrics, stats

    def _fetch_posts_page(self, page: int, per_page: int) -> List[Dict]:
        """Fetch posts from WordPress.com API

        In production, this would use wpcom-mcp client.
        For now, returns mock data for testing.
        """
        if self.enable_mock or not self._has_wpcom_client():
            return self._generate_mock_posts(page, per_page)

        # Real implementation would use wpcom MCP:
        # from wpcom_client import WPComAPI
        # api = WPComAPI(self.site_url)
        # return api.get_posts(page=page, per_page=per_page)

        return []

    def _has_wpcom_client(self) -> bool:
        """Check if wpcom-mcp is available"""
        try:
            import wpcom_client
            return True
        except ImportError:
            return False

    def _generate_mock_posts(self, page: int, per_page: int) -> List[Dict]:
        """Generate realistic mock posts for testing"""
        if page > 3:  # Mock 300 posts total
            return []

        posts = []
        base_id = (page - 1) * per_page + 1

        templates = [
            {
                "title_template": "Kodaline 解散震撼彈！{date} 台北站告別巡演搶票全攻略",
                "content_template": """
                    <h1>Kodaline 告別演唱會完整攻略</h1>
                    <p>愛爾蘭獨立搖滾樂團 Kodaline 宣布解散，於 {date} 舉辦最終台北演唱會。</p>
                    <h2>演出資訊</h2>
                    <p>時間：{date} 19:30</p>
                    <p>地點：台北國際會議中心 (TICC)</p>
                    <a href="/articles/kodaline-history/">Kodaline 樂團歷史</a>
                    <a href="https://external.com/kodaline">外部連結</a>
                    <img src="/images/kodaline.jpg" alt="Kodaline 樂團海報"/>
                    <img src="/images/venue.jpg"/>
                    <h2>購票方式</h2>
                    <p>KKTIX / TIXCRAFT 販售中</p>
                """,
                "category": "music",
                "base_views": 45
            },
            {
                "title_template": "五月天 {date} 北京演唱會｜搶票最新訊息",
                "content_template": """
                    <h1>五月天北京演唱會搶票指南</h1>
                    <p>五月天宣布 {date} 北京首唱。</p>
                    <h2>演出詳情</h2>
                    <p>時間：{date}</p>
                    <p>地點：北京奧體中心</p>
                    <a href="/articles/may-day-albums/">五月天專輯全集</a>
                    <img src="/images/maydays.jpg" alt="五月天演唱會海報"/>
                    <h2>票價資訊</h2>
                """,
                "category": "music",
                "base_views": 320
            },
            {
                "title_template": "2024 年度科技趨勢：AI 與雲計算演進",
                "content_template": """
                    <h1>2024 年科技趨勢預測</h1>
                    <p>本文分析年度科技發展方向。</p>
                    <h2>AI 發展</h2>
                    <p>機器學習模型越來越精準。</p>
                    <a href="/tags/ai/">更多 AI 文章</a>
                    <a href="/articles/cloud-computing/">雲計算完整指南</a>
                    <img src="/images/ai-trend.jpg"/>
                    <img src="/images/tech.jpg" alt="科技趨勢圖表"/>
                """,
                "category": "tech",
                "base_views": 12
            }
        ]

        for i in range(per_page):
            post_id = base_id + i
            if post_id > 2700:  # Stop at total estimate
                break

            template = templates[i % len(templates)]
            date_str = f"8/{24 + (i % 7)}"

            posts.append({
                "id": post_id,
                "title": template["title_template"].format(date=date_str),
                "content": template["content_template"].format(date=date_str),
                "excerpt": f"Preview of post {post_id}: {template['title_template'][:100]}...",
                "category": template["category"],
                "views_30d": max(template["base_views"] + (i % 50) - 25, 1)
            })

        return posts

    def _scan_post(self, post: Dict) -> SEOMetrics:
        """Analyze single post for SEO metrics"""
        post_id = post.get('id', 0)
        title = post.get('title', '')
        content = post.get('content', '')
        excerpt = post.get('excerpt', '')
        views = post.get('views_30d', 0)

        # Parse HTML metrics
        alt_parser = ImageAltParser()
        try:
            alt_parser.feed(content)
        except Exception as e:
            logger.warning(f"Failed to parse images in post {post_id}: {e}")
            alt_parser.images_without_alt = 0

        link_parser = LinkParser(self.site_url)
        try:
            link_parser.feed(content)
        except Exception as e:
            logger.warning(f"Failed to parse links in post {post_id}: {e}")
            link_parser.internal_links = 0

        # Calculate metrics
        title_len = len(title)
        description_len = len(excerpt)
        h1_count = content.count('<h1') if content else 0
        schema_present = 'application/ld+json' in content if content else False

        # Determine tier
        tier = self._classify_tier(views)

        # Calculate SEO score
        score, issues = self._calculate_seo_score(
            title_len=title_len,
            description_len=description_len,
            h1_count=h1_count,
            internal_links=link_parser.internal_links,
            images_no_alt=alt_parser.images_without_alt,
            schema_present=schema_present,
            views=views
        )

        return SEOMetrics(
            post_id=post_id,
            title=title,
            title_len=title_len,
            description_len=description_len,
            h1_count=h1_count,
            internal_links=link_parser.internal_links,
            images_no_alt=alt_parser.images_without_alt,
            schema_present=schema_present,
            views_30d=views,
            seo_score=score,
            tier=tier,
            issues=issues
        )

    def _calculate_seo_score(self, title_len: int, description_len: int, h1_count: int,
                            internal_links: int, images_no_alt: int,
                            schema_present: bool, views: int) -> Tuple[int, List[Dict]]:
        """Calculate SEO score (0-100) and identify issues"""
        score = 0
        issues = []

        # Title scoring
        if self.TITLE_OPTIMAL_RANGE[0] <= title_len <= self.TITLE_OPTIMAL_RANGE[1]:
            score += self.SCORING_WEIGHTS['title_optimal']
        else:
            gap = title_len - self.TITLE_OPTIMAL_RANGE[1]
            if gap > 0:
                penalty = min(gap * 2, self.SCORING_WEIGHTS['title_optimal'])
            else:
                penalty = min(abs(gap) * 2.5, self.SCORING_WEIGHTS['title_optimal'])
            score += max(0, self.SCORING_WEIGHTS['title_optimal'] - penalty)
            issues.append({
                "type": "title_length_issue",
                "value": title_len,
                "target_range": self.TITLE_OPTIMAL_RANGE,
                "severity": "high" if abs(gap) > 10 else "medium"
            })

        # Description scoring
        if self.DESCRIPTION_OPTIMAL_RANGE[0] <= description_len <= self.DESCRIPTION_OPTIMAL_RANGE[1]:
            score += self.SCORING_WEIGHTS['description_optimal']
        else:
            gap = description_len - self.DESCRIPTION_OPTIMAL_RANGE[1]
            if gap > 0:
                penalty = min(gap * 1.5, self.SCORING_WEIGHTS['description_optimal'])
            else:
                penalty = min(abs(gap) * 2, self.SCORING_WEIGHTS['description_optimal'])
            score += max(0, self.SCORING_WEIGHTS['description_optimal'] - penalty)
            if abs(gap) > 50:
                issues.append({
                    "type": "description_length_issue",
                    "value": description_len,
                    "target_range": self.DESCRIPTION_OPTIMAL_RANGE,
                    "severity": "high"
                })

        # H1 scoring
        if h1_count >= self.MIN_H1:
            score += self.SCORING_WEIGHTS['h1_present']
        else:
            score += self.SCORING_WEIGHTS['h1_present'] * 0.3
            issues.append({
                "type": "h1_missing",
                "severity": "high"
            })

        # Internal links scoring
        if internal_links >= self.MIN_INTERNAL_LINKS:
            score += self.SCORING_WEIGHTS['internal_links']
        else:
            score += self.SCORING_WEIGHTS['internal_links'] * (internal_links / self.MIN_INTERNAL_LINKS)
            issues.append({
                "type": "internal_links_insufficient",
                "current": internal_links,
                "target": self.MIN_INTERNAL_LINKS,
                "severity": "high"
            })

        # Image alt text scoring
        if images_no_alt == 0:
            score += self.SCORING_WEIGHTS['images_alt']
        elif images_no_alt <= 2:
            score += self.SCORING_WEIGHTS['images_alt'] * 0.7
            issues.append({
                "type": "images_missing_alt",
                "count": images_no_alt,
                "severity": "medium"
            })
        else:
            score += self.SCORING_WEIGHTS['images_alt'] * 0.3
            issues.append({
                "type": "images_missing_alt",
                "count": images_no_alt,
                "severity": "high"
            })

        # Schema scoring
        if schema_present:
            score += self.SCORING_WEIGHTS['schema']
        else:
            score += self.SCORING_WEIGHTS['schema'] * 0.4
            issues.append({
                "type": "schema_missing",
                "severity": "medium"
            })

        # Content health (basic)
        score += self.SCORING_WEIGHTS['content_health'] * 0.8

        # View bonus
        if views > 50:
            score += self.SCORING_WEIGHTS['views_bonus']
        elif views > 20:
            score += self.SCORING_WEIGHTS['views_bonus'] * 0.7
        elif views > 5:
            score += self.SCORING_WEIGHTS['views_bonus'] * 0.4

        return min(100, int(score)), issues

    def _classify_tier(self, views: int) -> str:
        """Classify post into optimization tier"""
        if views > 20:
            return "tier_1"
        elif views >= 5:
            return "tier_2"
        else:
            return "tier_3"

    def _calculate_stats(self, metrics: List[SEOMetrics]) -> Dict:
        """Calculate aggregate statistics"""
        if not metrics:
            return {}

        scores = [m.seo_score for m in metrics]
        views = [m.views_30d for m in metrics]

        tier_counts = defaultdict(int)
        for m in metrics:
            tier_counts[m.tier] += 1

        issue_types = defaultdict(int)
        for m in metrics:
            for issue in m.issues:
                issue_types[issue['type']] += 1

        avg_score = sum(scores) / len(scores)
        avg_views = sum(views) / len(views)

        return {
            "total_posts": len(metrics),
            "avg_seo_score": round(avg_score, 2),
            "min_score": min(scores),
            "max_score": max(scores),
            "avg_views_30d": round(avg_views, 2),
            "tier_distribution": dict(tier_counts),
            "top_issues": dict(sorted(issue_types.items(), key=lambda x: x[1], reverse=True)[:10]),
            "execution_time": self._format_duration()
        }

    def _print_progress(self, count: int):
        """Display progress"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        rate = count / elapsed if elapsed > 0 else 0
        remaining = self.total_posts_estimate - count
        eta_seconds = remaining / rate if rate > 0 else 0

        logger.info(
            f"Progress: {count}/{self.total_posts_estimate} posts "
            f"({count*100//self.total_posts_estimate}%) | "
            f"Rate: {rate:.1f} posts/sec | "
            f"ETA: {timedelta(seconds=int(eta_seconds))}"
        )

    def _format_duration(self) -> str:
        """Format execution duration"""
        if not self.start_time:
            return "0m 0s"

        duration = (datetime.now() - self.start_time).total_seconds()
        minutes = int(duration) // 60
        seconds = int(duration) % 60

        return f"{minutes}m {seconds}s"


def export_csv(metrics: List[SEOMetrics], output_path: str = "seo_baseline.csv"):
    """Export metrics to CSV"""
    if not metrics:
        logger.warning("No metrics to export")
        return

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'post_id', 'title', 'title_len', 'description_len', 'h1_count',
            'internal_links', 'images_no_alt', 'schema_present', 'views_30d',
            'seo_score', 'tier', 'issue_count'
        ])

        # Data rows
        for m in metrics:
            writer.writerow([
                m.post_id,
                m.title[:100],  # Truncate for CSV readability
                m.title_len,
                m.description_len,
                m.h1_count,
                m.internal_links,
                m.images_no_alt,
                "yes" if m.schema_present else "no",
                m.views_30d,
                m.seo_score,
                m.tier,
                len(m.issues)
            ])

    logger.info(f"Exported {len(metrics)} rows to {output_path}")


def export_json(metrics: List[SEOMetrics], stats: Dict, output_path: str = "seo_baseline.json"):
    """Export metrics to JSON"""
    if not metrics:
        logger.warning("No metrics to export")
        return

    data = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_posts": len(metrics),
            "phase": "Phase 1: SEO Baseline Scan"
        },
        "statistics": stats,
        "posts": [
            {
                **m.to_dict(),
                "issues": m.issues,
                "optimization_potential": max(100 - m.seo_score, 0)
            }
            for m in sorted(metrics, key=lambda x: (len(x.issues), -x.views_30d))
        ]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info(f"Exported detailed data to {output_path}")


def main():
    """Main entry point"""
    # Configuration
    SITE_URL = "yololab.net"
    ENABLE_MOCK = False  # Use real wpcom-mcp
    MAX_PAGES = None  # Scan all pages

    logger.info("=" * 60)
    logger.info("SEO Scanner - Phase 1: Baseline Collection")
    logger.info("=" * 60)

    # Run scan
    scanner = SEOScanner(site_url=SITE_URL, enable_mock=ENABLE_MOCK)
    metrics, stats = scanner.scan_posts(per_page=100, max_pages=MAX_PAGES)

    # Export results
    output_dir = Path(__file__).parent
    csv_path = output_dir / "seo_baseline.csv"
    json_path = output_dir / "seo_baseline.json"

    export_csv(metrics, str(csv_path))
    export_json(metrics, stats, str(json_path))

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("SCAN SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total posts processed: {stats.get('total_posts', 0)}")
    logger.info(f"Average SEO score: {stats.get('avg_seo_score', 0):.1f}/100")
    logger.info(f"Score range: {stats.get('min_score', 0)}-{stats.get('max_score', 0)}")
    logger.info(f"Average views (30d): {stats.get('avg_views_30d', 0):.1f}")
    logger.info(f"\nTier Distribution:")
    for tier, count in stats.get('tier_distribution', {}).items():
        pct = (count / stats.get('total_posts', 1)) * 100
        logger.info(f"  {tier}: {count} posts ({pct:.1f}%)")

    logger.info(f"\nTop Issues:")
    for issue_type, count in list(stats.get('top_issues', {}).items())[:5]:
        logger.info(f"  {issue_type}: {count} posts")

    logger.info(f"\nExecution time: {stats.get('execution_time', '0m 0s')}")
    logger.info(f"\nOutputs:")
    logger.info(f"  CSV: {csv_path}")
    logger.info(f"  JSON: {json_path}")
    logger.info(f"  Log: scan_seo_baseline.log")


if __name__ == "__main__":
    main()
