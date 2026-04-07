#!/usr/bin/env python3
"""
Cost calculator for AI optimizer batch processing.
Estimates token usage and pricing for 2700-post YOLO LAB optimization.
"""

import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PricingTier:
    """Pricing information for a model."""
    model: str
    input_cost_per_m: float
    output_cost_per_m: float
    context_window: int
    max_output_tokens: int


# Current Claude models as of March 2026
PRICING_TIERS = {
    "claude-opus-4-6": PricingTier(
        model="claude-opus-4-6",
        input_cost_per_m=5.00,
        output_cost_per_m=25.00,
        context_window=200_000,
        max_output_tokens=128_000,
    ),
    "claude-sonnet-4-6": PricingTier(
        model="claude-sonnet-4-6",
        input_cost_per_m=3.00,
        output_cost_per_m=15.00,
        context_window=200_000,
        max_output_tokens=64_000,
    ),
    "claude-haiku-4-5": PricingTier(
        model="claude-haiku-4-5",
        input_cost_per_m=1.00,
        output_cost_per_m=5.00,
        context_window=200_000,
        max_output_tokens=64_000,
    ),
}


class CostCalculator:
    """Calculate optimization costs for batches."""

    def __init__(self, model: str = "claude-opus-4-6"):
        """Initialize with pricing tier."""
        if model not in PRICING_TIERS:
            raise ValueError(f"Unknown model: {model}")
        self.tier = PRICING_TIERS[model]

    def estimate_per_post_tokens(
        self,
        title_length: int = 100,
        content_length: int = 2000,
        excerpt_length: int = 200,
    ) -> dict[str, int]:
        """Estimate tokens per post for 5-turn optimization."""
        # Conservative estimates based on Claude token counting
        # Roughly: 1 token ≈ 4 characters or 0.75 words

        # System prompt (~800 tokens per turn)
        system_tokens = 800

        # Turn 1: Title generation
        turn1_input = system_tokens + int(title_length / 4) + int(excerpt_length / 4) + 300
        turn1_output = 300  # 3 titles with explanation

        # Turn 2: Meta description
        turn2_input = system_tokens + int(title_length / 4) + int(content_length / 4) + 200
        turn2_output = 200  # Description + explanation

        # Turn 3: Related articles
        turn3_input = system_tokens + int(title_length / 4) + int(content_length / 4) + 200
        turn3_output = 250  # Related links explanation

        # Turn 4: FAQ expansion
        turn4_input = system_tokens + int(title_length / 4) + int(content_length / 4) + 200
        turn4_output = 400  # 5-7 Q&A pairs

        # Turn 5: Image alt text
        turn5_input = system_tokens + int(title_length / 4) + int(excerpt_length / 4) + 200
        turn5_output = 200  # Alt text explanations

        # Context from prior turns (each turn includes previous messages)
        context_growth = [0, turn1_input + turn1_output,
                         turn2_input + turn2_output,
                         turn3_input + turn3_output,
                         turn4_input + turn4_output]

        total_input = (
            turn1_input +
            (turn1_input + turn1_output) + turn2_input +
            (turn1_input + turn1_output + turn2_input + turn2_output) + turn3_input +
            (turn1_input + turn1_output + turn2_input + turn2_output + turn3_input + turn3_output) + turn4_input +
            (turn1_input + turn1_output + turn2_input + turn2_output + turn3_input + turn3_output + turn4_input + turn4_output) + turn5_input
        )

        total_output = turn1_output + turn2_output + turn3_output + turn4_output + turn5_output

        return {
            "per_turn_input": [turn1_input, turn2_input, turn3_input, turn4_input, turn5_input],
            "per_turn_output": [turn1_output, turn2_output, turn3_output, turn4_output, turn5_output],
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
        }

    def estimate_batch_cost(
        self,
        num_posts: int = 2700,
        posts_by_tier: Optional[dict[str, int]] = None,
    ) -> dict[str, any]:
        """Estimate cost for full batch optimization."""
        if posts_by_tier is None:
            # Default YOLO LAB priority distribution
            posts_by_tier = {
                "tier_1": 200,   # High traffic (>20 views/30d)
                "tier_2": 800,   # Medium traffic (5-20 views/30d)
                "tier_3": 1700,  # Low traffic (<5 views/30d)
            }

        # Token estimates (conservative)
        tokens_per_post = self.estimate_per_post_tokens()

        # Tier 1 + Tier 2 optimized (Tier 3 deferred)
        optimized_posts = posts_by_tier["tier_1"] + posts_by_tier["tier_2"]

        total_input = tokens_per_post["total_input_tokens"] * optimized_posts
        total_output = tokens_per_post["total_output_tokens"] * optimized_posts

        input_cost = (total_input / 1_000_000) * self.tier.input_cost_per_m
        output_cost = (total_output / 1_000_000) * self.tier.output_cost_per_m
        total_cost = input_cost + output_cost

        return {
            "model": self.tier.model,
            "optimization_scope": {
                "total_posts": num_posts,
                "tier_1_optimized": posts_by_tier["tier_1"],
                "tier_2_optimized": posts_by_tier["tier_2"],
                "tier_3_deferred": posts_by_tier["tier_3"],
            },
            "token_estimates": {
                "per_post_input": tokens_per_post["total_input_tokens"],
                "per_post_output": tokens_per_post["total_output_tokens"],
                "total_input_tokens": int(total_input),
                "total_output_tokens": int(total_output),
                "total_tokens": int(total_input + total_output),
            },
            "costs": {
                "input_cost_usd": round(input_cost, 2),
                "output_cost_usd": round(output_cost, 2),
                "total_cost_usd": round(total_cost, 2),
                "cost_per_post_usd": round(total_cost / optimized_posts, 4),
            },
            "efficiency": {
                "avg_tokens_per_post": int((total_input + total_output) / optimized_posts),
                "input_output_ratio": f"{total_input / total_output:.2f}:1",
            },
        }

    def estimate_with_caching(
        self,
        num_posts: int = 2700,
        cache_hit_rate: float = 0.7,
    ) -> dict[str, any]:
        """Estimate cost with prompt caching enabled (90% savings on cache reads)."""
        base_estimate = self.estimate_batch_cost(num_posts=num_posts)
        tokens_base = base_estimate["token_estimates"]["total_input_tokens"]

        # System prompt is cached (same for all posts)
        # Assume 70% of input tokens are cacheable (system + turn setup)
        cacheable_tokens = int(tokens_base * 0.7)
        cached_reads = int(cacheable_tokens * cache_hit_rate)
        cache_writes = int(cacheable_tokens * (1 - cache_hit_rate))

        # Pricing: cache writes = 1.25x, cache reads = 0.1x, uncached = 1x
        cache_write_cost = (cache_writes / 1_000_000) * self.tier.input_cost_per_m * 1.25
        cache_read_cost = (cached_reads / 1_000_000) * self.tier.input_cost_per_m * 0.1
        uncached_cost = ((tokens_base - cacheable_tokens) / 1_000_000) * self.tier.input_cost_per_m
        output_cost = (base_estimate["token_estimates"]["total_output_tokens"] / 1_000_000) * self.tier.output_cost_per_m

        total_with_cache = cache_write_cost + cache_read_cost + uncached_cost + output_cost
        savings = base_estimate["costs"]["total_cost_usd"] - total_with_cache

        return {
            "base_cost_usd": base_estimate["costs"]["total_cost_usd"],
            "caching_enabled": {
                "cache_hit_rate": f"{cache_hit_rate * 100:.0f}%",
                "cacheable_tokens": cacheable_tokens,
                "cached_write_tokens": cache_writes,
                "cached_read_tokens": cached_reads,
                "uncached_tokens": tokens_base - cacheable_tokens,
            },
            "cost_breakdown": {
                "cache_write_cost_usd": round(cache_write_cost, 2),
                "cache_read_cost_usd": round(cache_read_cost, 2),
                "uncached_input_cost_usd": round(uncached_cost, 2),
                "output_cost_usd": round(output_cost, 2),
                "total_cost_usd": round(total_with_cache, 2),
            },
            "savings": {
                "absolute_savings_usd": round(savings, 2),
                "savings_percentage": f"{(savings / base_estimate['costs']['total_cost_usd'] * 100):.1f}%",
            },
        }

    def compare_models(self, num_posts: int = 1000) -> dict[str, any]:
        """Compare costs across available models."""
        results = {}
        for model_name in PRICING_TIERS.keys():
            calc = CostCalculator(model=model_name)
            estimate = calc.estimate_batch_cost(num_posts=num_posts)
            results[model_name] = {
                "total_cost": estimate["costs"]["total_cost_usd"],
                "cost_per_post": estimate["costs"]["cost_per_post_usd"],
                "context_window": calc.tier.context_window,
                "max_output": calc.tier.max_output_tokens,
            }
        return results


def main():
    """Generate cost estimates for YOLO LAB optimization."""
    print("=" * 70)
    print("SEO BATCH OPTIMIZER - COST ANALYSIS (2700 posts)")
    print("=" * 70)

    # Base estimate with Claude Opus 4.6
    calc = CostCalculator(model="claude-opus-4-6")

    # Scenario 1: Tier 1 + Tier 2 optimization
    print("\nSCENARIO 1: Base Estimate (Tier 1 + 2 only)")
    print("-" * 70)
    estimate = calc.estimate_batch_cost(num_posts=2700)
    print(json.dumps(estimate, indent=2, ensure_ascii=False))

    # Scenario 2: With prompt caching
    print("\nSCENARIO 2: With Prompt Caching (70% cache hit)")
    print("-" * 70)
    with_cache = calc.estimate_with_caching(num_posts=2700, cache_hit_rate=0.7)
    print(json.dumps(with_cache, indent=2, ensure_ascii=False))

    # Scenario 3: Model comparison
    print("\nSCENARIO 3: Model Comparison (1000 posts)")
    print("-" * 70)
    comparison = calc.compare_models(num_posts=1000)
    for model, costs in comparison.items():
        print(f"\n{model}:")
        print(f"  Total Cost: ${costs['total_cost']:.2f}")
        print(f"  Cost/Post: ${costs['cost_per_post']:.4f}")
        print(f"  Context: {costs['context_window']:,} tokens")

    # Scenario 4: Full batch projection
    print("\nSCENARIO 4: Full Batch (2700 posts) Timeline & Cost")
    print("-" * 70)
    tier1_posts = 200
    tier2_posts = 800
    total_optimized = tier1_posts + tier2_posts
    estimate_full = calc.estimate_batch_cost(num_posts=2700)

    cost_per_post = estimate_full["costs"]["cost_per_post_usd"]
    # Assume 3 minutes per post (5 turns × ~30 seconds per API call)
    min_per_post = 3
    total_minutes = total_optimized * min_per_post
    total_hours = total_minutes / 60
    total_days = total_hours / 8  # 8-hour workday

    print(f"Posts to optimize: {total_optimized:,}")
    print(f"  - Tier 1 (high traffic): {tier1_posts}")
    print(f"  - Tier 2 (medium traffic): {tier2_posts}")
    print(f"  - Tier 3 (deferred): 1,700")
    print(f"\nToken Usage:")
    print(f"  - Per post: {estimate_full['token_estimates']['per_post_input']} input + {estimate_full['token_estimates']['per_post_output']} output")
    print(f"  - Total: {estimate_full['token_estimates']['total_input_tokens']:,} input + {estimate_full['token_estimates']['total_output_tokens']:,} output")
    print(f"\nCost:")
    print(f"  - Base cost: ${estimate_full['costs']['total_cost_usd']:,.2f}")
    print(f"  - With 70% caching: ${with_cache['cost_breakdown']['total_cost_usd']:,.2f}")
    print(f"  - Savings: ${with_cache['savings']['absolute_savings_usd']:.2f} ({with_cache['savings']['savings_percentage']})")
    print(f"\nTimeline (sequential):")
    print(f"  - Est. time per post: {min_per_post} min (5 API calls)")
    print(f"  - Total: {total_hours:.1f} hours = {total_days:.1f} working days")
    print(f"  - Recommendation: Batch processing with 50-100 posts/day to stay under rate limits")

    # Export estimates to JSON
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    with open(output_dir / "cost_estimates.json", "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "model": "claude-opus-4-6",
            "base_estimate": estimate,
            "with_caching": with_cache,
            "model_comparison": comparison,
        }, f, indent=2, ensure_ascii=False)

    print(f"\nEstimates exported to output/cost_estimates.json")


if __name__ == "__main__":
    main()
