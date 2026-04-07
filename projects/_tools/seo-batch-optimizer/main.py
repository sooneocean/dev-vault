#!/usr/bin/env python3
"""
SEO Batch Optimizer - Main execution script
Orchestrates the batch update workflow with safety checks
"""

import json
import logging
import argparse
import sys
from pathlib import Path
from typing import List, Optional

from batch_updater import BatchUpdater, BatchUpdate
from snapshot_manager import SnapshotManager
from post_validator import PostValidator
from wpcom_client import WPComAPIClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("batch_optimizer.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


def load_optimizations_file(filepath: str) -> List[dict]:
    """
    Load optimization suggestions from JSONL file.

    Expected format (one JSON per line):
    {
        "post_id": 34844,
        "optimizations": {
            "title_options": ["option1", "option2", ...],
            "meta_description": "...",
            "internal_links": [{"post_id": 123, "anchor": "text"}],
            "faq_expansion": [{"q": "question", "a": "answer"}],
            "image_alts": [{"image_id": 123, "alt": "description"}]
        }
    }
    """
    optimizations = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                opt = json.loads(line)
                optimizations.append(opt)

        logger.info(f"Loaded {len(optimizations)} optimizations from {filepath}")
        return optimizations

    except Exception as e:
        logger.error(f"Failed to load optimizations file {filepath}: {e}")
        return []


def create_updates_from_optimizations(
    optimizations: List[dict],
    select_title_option: int = 0,
    add_faq_schema: bool = True,
) -> List[BatchUpdate]:
    """
    Convert AI optimization suggestions into BatchUpdate objects.

    Args:
        optimizations: List of optimization dicts from AI
        select_title_option: Which title option to use (0=first, default)
        add_faq_schema: If True, append FAQ schema to content

    Returns:
        List of BatchUpdate objects
    """
    updates = []

    for opt in optimizations:
        post_id = opt.get("post_id")
        opt_data = opt.get("optimizations", {})

        # Select title
        title_options = opt_data.get("title_options", [])
        title = (
            title_options[select_title_option]["text"]
            if select_title_option < len(title_options)
            else title_options[0]["text"] if title_options
            else None
        )

        # Get meta description
        excerpt = opt_data.get("meta_description")

        # Build FAQ schema
        faq_data = opt_data.get("faq_expansion", [])
        faq_schema = ""
        if add_faq_schema and faq_data:
            faq_schema = _build_faq_schema(faq_data)

        # Get featured image alt (if available)
        image_alts = opt_data.get("image_alts", [])
        featured_image_alt = (
            image_alts[0].get("alt") if image_alts else None
        )

        update = BatchUpdate(
            post_id=post_id,
            title=title,
            excerpt=excerpt,
            content=faq_schema,  # Content will be appended
            featured_image_alt=featured_image_alt,
        )

        updates.append(update)

    logger.info(f"Created {len(updates)} batch updates")
    return updates


def _build_faq_schema(faq_items: List[dict]) -> str:
    """
    Build JSON-LD FAQ schema from Q&A items.

    Args:
        faq_items: List of {"q": "question", "a": "answer"} dicts

    Returns:
        HTML script tag with FAQ schema
    """
    if not faq_items:
        return ""

    # Build mainEntity array
    main_entity = []
    for item in faq_items:
        main_entity.append({
            "@type": "Question",
            "name": item.get("q"),
            "acceptedAnswer": {
                "@type": "Answer",
                "text": item.get("a"),
            }
        })

    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": main_entity,
    }

    # Wrap in HTML script tag
    json_str = json.dumps(schema, ensure_ascii=False, indent=2)
    html = f'<script type="application/ld+json">\n{json_str}\n</script>'

    return html


def print_simulation_report(
    updates: List[BatchUpdate],
    limit: int = 10,
) -> None:
    """
    Print detailed simulation report showing what would change.

    Args:
        updates: List of BatchUpdate objects
        limit: Max updates to display details for
    """
    print("\n" + "=" * 80)
    print("DRY RUN SIMULATION REPORT")
    print("=" * 80)

    print(f"\nTotal updates: {len(updates)}")
    print(f"Displaying details for first {min(limit, len(updates))} posts\n")

    for i, update in enumerate(updates[:limit], 1):
        print(f"{i}. Post ID: {update.post_id}")
        print("-" * 70)

        if update.title:
            print(f"   Title ({len(update.title)} chars):")
            print(f"     {update.title}")

        if update.excerpt:
            print(f"\n   Description ({len(update.excerpt)} chars):")
            desc_preview = (
                update.excerpt[:150] + "..."
                if len(update.excerpt) > 150
                else update.excerpt
            )
            print(f"     {desc_preview}")

        if update.featured_image_alt:
            print(f"\n   Featured Image Alt:")
            print(f"     {update.featured_image_alt}")

        if update.content:
            print(f"\n   Content Additions:")
            print(f"     Adding FAQ schema ({len(update.content)} chars)")

        print()

    if len(updates) > limit:
        print(f"... and {len(updates) - limit} more posts")

    print("\n" + "=" * 80)


def main():
    """Main execution entry point"""
    parser = argparse.ArgumentParser(
        description="SEO Batch Optimizer for WordPress.com"
    )

    parser.add_argument(
        "--site",
        default="yololab.net",
        help="WordPress.com site name",
    )

    parser.add_argument(
        "--optimizations-file",
        required=True,
        help="Path to JSONL file with optimization suggestions",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate updates without making changes",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Posts per batch (default: 50)",
    )

    parser.add_argument(
        "--require-confirmation",
        action="store_true",
        help="Ask for confirmation before each batch",
    )

    parser.add_argument(
        "--simulate-only",
        action="store_true",
        help="Print simulation report and exit",
    )

    parser.add_argument(
        "--title-option",
        type=int,
        default=0,
        help="Which title option to use (0=first, default)",
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    # Update logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    logger.info("=" * 70)
    logger.info("SEO BATCH OPTIMIZER STARTED")
    logger.info("=" * 70)

    try:
        # Step 1: Load optimization suggestions
        logger.info(f"Loading optimizations from {args.optimizations_file}")
        optimizations = load_optimizations_file(
            args.optimizations_file
        )

        if not optimizations:
            logger.error("No optimizations loaded. Exiting.")
            return 1

        # Step 2: Create batch updates
        logger.info(f"Creating {len(optimizations)} batch updates")
        updates = create_updates_from_optimizations(
            optimizations,
            select_title_option=args.title_option,
        )

        # Step 3: Print simulation report
        print_simulation_report(updates)

        if args.simulate_only:
            logger.info("Simulation only mode - exiting")
            return 0

        # Step 4: Initialize components
        logger.info("Initializing batch updater components")
        snapshot_mgr = SnapshotManager()
        validator = PostValidator(strict_mode=False)
        wpcom_client = WPComAPIClient(args.site)

        updater = BatchUpdater(
            site_name=args.site,
            dry_run=args.dry_run,
            snapshot_manager=snapshot_mgr,
            validator=validator,
        )

        # Get valid post IDs for link validation
        # logger.info("Fetching valid post IDs for validation...")
        # valid_post_ids = wpcom_client.get_valid_post_ids()
        # For now, use empty list
        valid_post_ids = []

        # Step 5: Process batches
        logger.info(f"Processing {len(updates)} posts in batches of {args.batch_size}")

        batch_results = updater.process_multiple_batches(
            updates,
            valid_post_ids=valid_post_ids,
            require_confirmation=args.require_confirmation,
        )

        # Step 6: Summary
        total_successful = sum(
            r.successful_updates for r in batch_results
        )
        total_failed = sum(r.failed_updates for r in batch_results)

        print("\n" + "=" * 70)
        print("BATCH EXECUTION SUMMARY")
        print("=" * 70)
        print(f"Total batches processed: {len(batch_results)}")
        print(f"Total successful updates: {total_successful}")
        print(f"Total failed updates: {total_failed}")
        print(f"Overall status: {'SUCCESS' if total_failed == 0 else 'PARTIAL'}")
        print("=" * 70)

        logger.info(
            f"Batch processing complete: {total_successful} successful, "
            f"{total_failed} failed"
        )

        return 0 if total_failed == 0 else 1

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1

    finally:
        logger.info("=" * 70)
        logger.info("SEO BATCH OPTIMIZER FINISHED")
        logger.info("=" * 70)


if __name__ == "__main__":
    sys.exit(main())
