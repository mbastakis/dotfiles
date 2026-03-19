#!/usr/bin/env python3
"""
Adaptive Crawl4AI crawler with information foraging.

Uses intelligent crawling that knows when to stop based on information sufficiency.
Ideal for research tasks, question answering, and knowledge base building.

Usage:
    python adaptive_crawler.py <start_url> --query "your research query"
    python adaptive_crawler.py <start_url> --query "async context managers" --strategy embedding
    python adaptive_crawler.py <start_url> --query "machine learning" --max-pages 30 --confidence 0.8
"""

import argparse
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

# Version check
MIN_CRAWL4AI_VERSION = "0.7.4"
try:
    from crawl4ai.__version__ import __version__
    from packaging import version

    if version.parse(__version__) < version.parse(MIN_CRAWL4AI_VERSION):
        print(
            f"⚠️  Warning: Crawl4AI {MIN_CRAWL4AI_VERSION}+ recommended (you have {__version__})"
        )
except ImportError:
    print(f"ℹ️  Crawl4AI {MIN_CRAWL4AI_VERSION}+ required")

from crawl4ai import AsyncWebCrawler, AdaptiveCrawler, AdaptiveConfig


async def adaptive_crawl(
    start_url: str,
    query: str,
    strategy: str = "statistical",
    confidence_threshold: float = 0.7,
    max_pages: int = 20,
    top_k_links: int = 3,
    min_gain_threshold: float = 0.1,
    output_dir: str = ".",
    save_state: bool = False,
    resume_from: str | None = None,
    export_kb: bool = False,
):
    """
    Adaptive crawling with information foraging algorithm.

    The crawler intelligently decides:
    - Which links to follow based on relevance to query
    - When to stop based on information sufficiency (coverage, consistency, saturation)
    """

    # Configure adaptive crawler
    config = AdaptiveConfig(
        strategy=strategy,
        confidence_threshold=confidence_threshold,
        max_pages=max_pages,
        top_k_links=top_k_links,
        min_gain_threshold=min_gain_threshold,
        save_state=save_state,
        state_path=os.path.join(output_dir, "crawl_state.json") if save_state else None,
    )

    print(f"🎯 Adaptive Crawl Configuration:")
    print(f"   Strategy: {strategy}")
    print(f"   Confidence threshold: {confidence_threshold}")
    print(f"   Max pages: {max_pages}")
    print(f"   Top-k links per page: {top_k_links}")
    print(f"   Min gain threshold: {min_gain_threshold}")
    print()

    async with AsyncWebCrawler() as crawler:
        adaptive = AdaptiveCrawler(crawler, config)

        print(f"🔍 Starting adaptive crawl...")
        print(f"   URL: {start_url}")
        print(f'   Query: "{query}"')
        print()

        # Execute adaptive crawl
        if resume_from:
            print(f"📂 Resuming from: {resume_from}")
            result = await adaptive.digest(
                start_url=start_url,
                query=query,
                resume_from=resume_from,
            )
        else:
            result = await adaptive.digest(
                start_url=start_url,
                query=query,
            )

        # Print statistics
        print("\n" + "=" * 60)
        adaptive.print_stats(detailed=True)
        print("=" * 60)

        # Get relevant content
        relevant_pages = adaptive.get_relevant_content(top_k=5)

        print(f"\n📊 Top {len(relevant_pages)} Most Relevant Pages:")
        print("-" * 60)
        for i, page in enumerate(relevant_pages, 1):
            print(f"{i}. {page['url']}")
            print(f"   Score: {page['score']:.2f}")
            print()

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save relevant content
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pages_dir = output_path / "pages"
        pages_dir.mkdir(exist_ok=True)

        for i, page in enumerate(relevant_pages, 1):
            filename = f"{i:03d}_{_sanitize_filename(page['url'])}.md"
            filepath = pages_dir / filename

            content = f"# {page.get('title', 'Untitled')}\n\n"
            content += f"**Source:** {page['url']}\n"
            content += f"**Relevance Score:** {page['score']:.2f}\n\n"
            content += "---\n\n"
            content += page.get("content", "")[:10000]  # Limit content size

            with open(filepath, "w") as f:
                f.write(content)

        print(f"📄 Saved {len(relevant_pages)} relevant pages to {pages_dir}/")

        # Save crawl summary
        summary = {
            "query": query,
            "start_url": start_url,
            "strategy": strategy,
            "timestamp": timestamp,
            "config": {
                "confidence_threshold": confidence_threshold,
                "max_pages": max_pages,
                "top_k_links": top_k_links,
                "min_gain_threshold": min_gain_threshold,
            },
            "results": {
                "pages_crawled": len(relevant_pages),
                "final_confidence": result.metrics.get("confidence", 0)
                if hasattr(result, "metrics")
                else 0,
                "is_irrelevant": result.metrics.get("is_irrelevant", False)
                if hasattr(result, "metrics")
                else False,
            },
            "relevant_pages": [
                {"url": p["url"], "score": p["score"]} for p in relevant_pages
            ],
        }

        summary_path = output_path / "crawl_summary.json"
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"📋 Saved crawl summary to {summary_path}")

        # Export knowledge base if requested
        if export_kb:
            kb_path = output_path / "knowledge_base.jsonl"
            adaptive.export_knowledge_base(str(kb_path))
            print(f"📚 Exported knowledge base to {kb_path}")

        return result, relevant_pages


def _sanitize_filename(url: str) -> str:
    """Convert URL to safe filename."""
    # Remove protocol and common prefixes
    name = url.replace("https://", "").replace("http://", "")
    name = name.replace("www.", "")
    # Replace unsafe characters
    for char in [":", "/", "?", "&", "=", "#", "%"]:
        name = name.replace(char, "_")
    # Truncate
    return name[:50]


def main():
    parser = argparse.ArgumentParser(
        description="Adaptive Crawl4AI crawler with information foraging.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic adaptive crawl with query
  python adaptive_crawler.py https://docs.python.org --query "async context managers"

  # Use embedding strategy for semantic understanding (requires API key)
  python adaptive_crawler.py https://realpython.com --query "decorators" --strategy embedding

  # Higher confidence threshold for exhaustive coverage
  python adaptive_crawler.py https://api.example.com/docs --query "authentication" --confidence 0.85

  # Research with more pages and export knowledge base
  python adaptive_crawler.py https://scikit-learn.org --query "model evaluation" --max-pages 30 --export-kb

  # Save state for resumption
  python adaptive_crawler.py https://docs.example.com --query "API" --save-state -o ./my_crawl

  # Resume a previous crawl
  python adaptive_crawler.py https://docs.example.com --query "API" --resume-from ./my_crawl/crawl_state.json

Strategy Comparison:
  statistical (default):
    - Fast, no API calls, works offline
    - Best for: Technical docs, specific terminology
    - Uses term-based coverage analysis

  embedding:
    - Semantic understanding beyond exact matches
    - Requires embedding model or API
    - Best for: Research, broad topics, conceptual understanding
        """,
    )
    parser.add_argument("start_url", help="Starting URL for adaptive crawl")
    parser.add_argument(
        "--query",
        "-q",
        required=True,
        help="Research query (what information are you looking for?)",
    )
    parser.add_argument(
        "--strategy",
        "-s",
        choices=["statistical", "embedding"],
        default="statistical",
        help="Crawling strategy (default: statistical)",
    )
    parser.add_argument(
        "--confidence",
        "-c",
        type=float,
        default=0.7,
        help="Confidence threshold to stop crawling (default: 0.7, range: 0-1)",
    )
    parser.add_argument(
        "--max-pages",
        "-m",
        type=int,
        default=20,
        help="Maximum pages to crawl (default: 20)",
    )
    parser.add_argument(
        "--top-k-links",
        "-k",
        type=int,
        default=3,
        help="Links to follow per page (default: 3)",
    )
    parser.add_argument(
        "--min-gain",
        type=float,
        default=0.1,
        help="Minimum expected information gain to continue (default: 0.1)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=".",
        help="Output directory (default: current directory)",
    )
    parser.add_argument(
        "--save-state", action="store_true", help="Save crawl state for resumption"
    )
    parser.add_argument("--resume-from", help="Resume crawl from saved state file")
    parser.add_argument(
        "--export-kb",
        action="store_true",
        help="Export collected pages as JSONL knowledge base",
    )

    args = parser.parse_args()

    asyncio.run(
        adaptive_crawl(
            start_url=args.start_url,
            query=args.query,
            strategy=args.strategy,
            confidence_threshold=args.confidence,
            max_pages=args.max_pages,
            top_k_links=args.top_k_links,
            min_gain_threshold=args.min_gain,
            output_dir=args.output,
            save_state=args.save_state,
            resume_from=args.resume_from,
            export_kb=args.export_kb,
        )
    )


if __name__ == "__main__":
    main()
