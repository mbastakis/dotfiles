#!/usr/bin/env python3
"""
Basic Crawl4AI crawler template with optional BM25 query filtering.

Usage:
    python basic_crawler.py <url>
    python basic_crawler.py <url> --bm25-query "your search query"
    python basic_crawler.py <url> --bm25-query "your search query" --bm25-threshold 1.5
    python basic_crawler.py <url> --pruning --pruning-threshold 0.5
"""

import argparse
import asyncio
import sys

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

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.content_filter_strategy import BM25ContentFilter, PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


async def crawl_basic(
    url: str,
    bm25_query: str | None = None,
    bm25_threshold: float = 1.0,
    use_pruning: bool = False,
    pruning_threshold: float = 0.48,
):
    """Basic crawling with markdown output and optional content filtering."""

    # Configure browser
    browser_config = BrowserConfig(
        headless=True, viewport_width=1920, viewport_height=1080
    )

    # Configure content filter if requested
    md_generator = None
    filter_type = None

    if bm25_query:
        # BM25 relevance-based filtering
        content_filter = BM25ContentFilter(
            user_query=bm25_query, bm25_threshold=bm25_threshold
        )
        md_generator = DefaultMarkdownGenerator(content_filter=content_filter)
        filter_type = f"BM25 (query='{bm25_query}', threshold={bm25_threshold})"
    elif use_pruning:
        # Pruning-based filtering (removes low-quality content)
        content_filter = PruningContentFilter(
            threshold=pruning_threshold, threshold_type="dynamic", min_word_threshold=5
        )
        md_generator = DefaultMarkdownGenerator(content_filter=content_filter)
        filter_type = f"Pruning (threshold={pruning_threshold})"

    # Configure crawler
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        remove_overlay_elements=True,
        wait_for_images=True,
        screenshot=True,
        markdown_generator=md_generator,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=crawler_config)

        if result.success:
            print(f"✅ Crawled: {result.url}")
            print(f"   Title: {result.metadata.get('title', 'N/A')}")
            print(
                f"   Links found: {len(result.links.get('internal', []))} internal, {len(result.links.get('external', []))} external"
            )
            print(
                f"   Media found: {len(result.media.get('images', []))} images, {len(result.media.get('videos', []))} videos"
            )

            # Handle markdown output based on filter type
            if filter_type:
                print(f"   Filter: {filter_type}")
                raw_len = (
                    len(result.markdown.raw_markdown)
                    if hasattr(result.markdown, "raw_markdown")
                    else len(str(result.markdown))
                )
                fit_len = (
                    len(result.markdown.fit_markdown)
                    if hasattr(result.markdown, "fit_markdown")
                    else 0
                )

                print(f"   Raw markdown: {raw_len} chars")
                print(f"   Fit markdown: {fit_len} chars")

                if fit_len > 0:
                    reduction = ((raw_len - fit_len) / raw_len) * 100
                    print(f"   Content reduction: {reduction:.1f}%")

                # Save both versions
                with open("output_raw.md", "w") as f:
                    f.write(
                        result.markdown.raw_markdown
                        if hasattr(result.markdown, "raw_markdown")
                        else str(result.markdown)
                    )
                with open("output_fit.md", "w") as f:
                    f.write(
                        result.markdown.fit_markdown
                        if hasattr(result.markdown, "fit_markdown")
                        else ""
                    )
                print("📄 Saved to output_raw.md and output_fit.md")
            else:
                content = str(result.markdown)
                print(f"   Content length: {len(content)} chars")
                with open("output.md", "w") as f:
                    f.write(content)
                print("📄 Saved to output.md")

            # Save screenshot if available
            if result.screenshot:
                if isinstance(result.screenshot, str):
                    import base64

                    screenshot_data = base64.b64decode(result.screenshot)
                else:
                    screenshot_data = result.screenshot
                with open("screenshot.png", "wb") as f:
                    f.write(screenshot_data)
                print("📸 Saved screenshot.png")
        else:
            print(f"❌ Failed: {result.error_message}")

        return result


def main():
    parser = argparse.ArgumentParser(
        description="Basic Crawl4AI crawler with optional BM25/Pruning content filtering.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic crawl
  python basic_crawler.py https://example.com

  # BM25 query-based filtering (extract only relevant content)
  python basic_crawler.py https://docs.python.org --bm25-query "async await"

  # Stricter BM25 filtering (higher threshold = fewer but more relevant results)
  python basic_crawler.py https://news.ycombinator.com --bm25-query "AI startups" --bm25-threshold 1.5

  # Pruning filter (removes low-quality content without a query)
  python basic_crawler.py https://blog.example.com --pruning

  # Stricter pruning
  python basic_crawler.py https://blog.example.com --pruning --pruning-threshold 0.6
        """,
    )
    parser.add_argument("url", help="URL to crawl")
    parser.add_argument(
        "--bm25-query",
        help="Query for BM25 relevance filtering (extracts only content relevant to query)",
    )
    parser.add_argument(
        "--bm25-threshold",
        type=float,
        default=1.0,
        help="BM25 threshold (default: 1.0, higher = stricter filtering)",
    )
    parser.add_argument(
        "--pruning",
        action="store_true",
        help="Use pruning filter to remove low-quality content",
    )
    parser.add_argument(
        "--pruning-threshold",
        type=float,
        default=0.48,
        help="Pruning threshold (default: 0.48, higher = more aggressive pruning)",
    )

    args = parser.parse_args()

    if args.bm25_query and args.pruning:
        print("⚠️  Warning: Both --bm25-query and --pruning specified. Using BM25.")

    asyncio.run(
        crawl_basic(
            url=args.url,
            bm25_query=args.bm25_query,
            bm25_threshold=args.bm25_threshold,
            use_pruning=args.pruning,
            pruning_threshold=args.pruning_threshold,
        )
    )


if __name__ == "__main__":
    main()
