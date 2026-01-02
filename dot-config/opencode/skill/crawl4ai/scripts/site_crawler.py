#!/usr/bin/env python3
"""
Site Deep Crawler - Crawl entire site and convert pages to markdown
Usage: python site_crawler.py <start_url> [options]
"""

import asyncio
import sys
import json
import re
from pathlib import Path
from urllib.parse import urlparse, urljoin, urldefrag
from typing import Set, Dict, Optional
from collections import deque
from datetime import datetime

# Version check
MIN_CRAWL4AI_VERSION = "0.7.4"
try:
    from crawl4ai.__version__ import __version__
    from packaging import version

    if version.parse(__version__) < version.parse(MIN_CRAWL4AI_VERSION):
        print(
            f"Warning: Crawl4AI {MIN_CRAWL4AI_VERSION}+ recommended (you have {__version__})"
        )
except ImportError:
    print(f"Crawl4AI {MIN_CRAWL4AI_VERSION}+ required")

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode


class URLManager:
    """Manages URL queue, visited tracking, and normalization"""

    def __init__(self, base_url: str, stay_within_path: bool = True):
        self.base_url = base_url
        self.parsed_base = urlparse(base_url)
        self.base_domain = self.parsed_base.netloc
        self.base_path = self.parsed_base.path.rstrip("/")
        self.stay_within_path = stay_within_path

        self.queue: deque = deque()  # URLs to visit
        self.visited: Set[str] = set()  # Already visited
        self.discovered: Dict[str, dict] = {}  # URL -> metadata

    def normalize_url(self, url: str) -> str:
        """Normalize URL: remove fragments, handle trailing slashes"""
        # Remove fragment
        url, _ = urldefrag(url)
        # Parse and reconstruct
        parsed = urlparse(url)
        # Remove trailing slash for consistency (except root)
        path = parsed.path.rstrip("/") if parsed.path != "/" else "/"
        return f"{parsed.scheme}://{parsed.netloc}{path}"

    def is_valid_url(self, url: str) -> bool:
        """Check if URL should be crawled"""
        parsed = urlparse(url)

        # Must be same domain
        if parsed.netloc != self.base_domain:
            return False

        # Must be http/https
        if parsed.scheme not in ("http", "https"):
            return False

        # Stay within base path if configured
        if self.stay_within_path:
            if not parsed.path.startswith(self.base_path):
                return False

        # Skip file extensions we don't want
        skip_extensions = {
            ".pdf",
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".svg",
            ".zip",
            ".tar",
            ".gz",
            ".mp4",
            ".mp3",
            ".css",
            ".js",
        }
        path_lower = parsed.path.lower()
        if any(path_lower.endswith(ext) for ext in skip_extensions):
            return False

        return True

    def add_url(self, url: str, source_url: str = None) -> bool:
        """Add URL to queue if valid and not visited"""
        normalized = self.normalize_url(url)

        if normalized in self.visited or normalized in [u for u in self.queue]:
            return False

        if not self.is_valid_url(normalized):
            return False

        self.queue.append(normalized)
        self.discovered[normalized] = {
            "discovered_from": source_url,
            "discovered_at": datetime.now().isoformat(),
        }
        return True

    def get_next(self) -> Optional[str]:
        """Get next URL to crawl"""
        while self.queue:
            url = self.queue.popleft()
            if url not in self.visited:
                return url
        return None

    def mark_visited(self, url: str, metadata: dict = None):
        """Mark URL as visited with optional metadata"""
        normalized = self.normalize_url(url)
        self.visited.add(normalized)
        if metadata and normalized in self.discovered:
            self.discovered[normalized].update(metadata)


async def crawl_site(
    start_url: str,
    output_dir: str = "./crawled_site",
    max_pages: int = 100,
    delay: float = 1.0,
    stay_within_path: bool = True,
    headless: bool = False,
    verbose: bool = True,
) -> Dict:
    """
    Crawl entire site starting from start_url

    Args:
        start_url: Starting URL to crawl
        output_dir: Directory to save markdown files
        max_pages: Maximum number of pages to crawl
        delay: Delay between requests in seconds
        stay_within_path: If True, only crawl URLs under start_url's path
        headless: If True, run browser in headless mode
        verbose: If True, print detailed progress

    Returns:
        Dictionary with crawl statistics and results
    """

    # Setup output directory
    output_path = Path(output_dir)
    pages_dir = output_path / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    # Initialize URL manager
    url_manager = URLManager(start_url, stay_within_path)
    url_manager.add_url(start_url)

    # Browser configuration - NON-HEADLESS for visibility by default
    browser_config = BrowserConfig(
        headless=headless, viewport_width=1920, viewport_height=1080, verbose=verbose
    )

    # Crawler configuration
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        remove_overlay_elements=True,
        exclude_external_links=False,  # Keep external links in content, just don't follow
        page_timeout=30000,
        wait_for="css:body",  # Wait for body to be present
    )

    # Statistics
    stats = {
        "start_url": start_url,
        "start_time": datetime.now().isoformat(),
        "pages_crawled": 0,
        "pages_failed": 0,
        "total_links_discovered": 0,
        "pages": [],
    }

    async with AsyncWebCrawler(config=browser_config) as crawler:
        page_num = 0

        while True:
            # Check limits
            if page_num >= max_pages:
                print(f"\nReached max pages limit ({max_pages})")
                break

            # Get next URL
            url = url_manager.get_next()
            if url is None:
                print("\nNo more URLs to crawl")
                break

            page_num += 1
            print(f"\n[{page_num}/{max_pages}] Crawling: {url}")

            try:
                # Crawl the page
                result = await crawler.arun(url=url, config=crawler_config)

                if result.success:
                    # Extract internal links
                    internal_links = result.links.get("internal", [])
                    new_links = 0

                    for link in internal_links:
                        href = link.get("href", "")
                        if href:
                            # Resolve relative URLs
                            absolute_url = urljoin(url, href)
                            if url_manager.add_url(absolute_url, source_url=url):
                                new_links += 1

                    stats["total_links_discovered"] += new_links

                    # Generate safe filename
                    parsed = urlparse(url)
                    safe_name = parsed.path.strip("/").replace("/", "_") or "index"
                    safe_name = re.sub(r"[^\w\-_]", "_", safe_name)
                    filename = f"{page_num:03d}_{safe_name}.md"

                    # Get markdown content
                    markdown_content = str(result.markdown) if result.markdown else ""

                    # Save markdown file
                    file_path = pages_dir / filename
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(f"# {result.metadata.get('title', url)}\n\n")
                        f.write(f"**URL:** {url}\n\n")
                        f.write(f"**Crawled:** {datetime.now().isoformat()}\n\n")
                        f.write("---\n\n")
                        f.write(markdown_content)

                    # Update stats
                    page_info = {
                        "url": url,
                        "title": result.metadata.get("title", ""),
                        "filename": filename,
                        "content_length": len(markdown_content),
                        "internal_links": len(internal_links),
                        "new_links_discovered": new_links,
                    }
                    stats["pages"].append(page_info)
                    stats["pages_crawled"] += 1

                    # Mark as visited
                    url_manager.mark_visited(
                        url,
                        {
                            "title": result.metadata.get("title", ""),
                            "crawled_at": datetime.now().isoformat(),
                            "success": True,
                        },
                    )

                    print(f"   Saved: {filename}")
                    print(f"   Content: {len(markdown_content)} chars")
                    print(f"   New links found: {new_links}")
                    print(f"   Queue size: {len(url_manager.queue)}")

                else:
                    print(f"   Failed: {result.error_message}")
                    stats["pages_failed"] += 1
                    url_manager.mark_visited(
                        url,
                        {
                            "crawled_at": datetime.now().isoformat(),
                            "success": False,
                            "error": result.error_message,
                        },
                    )

            except Exception as e:
                print(f"   Exception: {str(e)}")
                stats["pages_failed"] += 1
                url_manager.mark_visited(
                    url,
                    {
                        "crawled_at": datetime.now().isoformat(),
                        "success": False,
                        "error": str(e),
                    },
                )

            # Delay between requests
            if delay > 0:
                await asyncio.sleep(delay)

    # Finalize stats
    stats["end_time"] = datetime.now().isoformat()
    stats["total_urls_discovered"] = len(url_manager.discovered)
    stats["urls_in_queue_remaining"] = len(url_manager.queue)

    # Save index file
    index_path = output_path / "site_index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump({"stats": stats, "all_urls": url_manager.discovered}, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"Crawl Complete!")
    print(f"   Pages crawled: {stats['pages_crawled']}")
    print(f"   Pages failed: {stats['pages_failed']}")
    print(f"   Total URLs discovered: {stats['total_urls_discovered']}")
    print(f"   URLs remaining in queue: {stats['urls_in_queue_remaining']}")
    print(f"   Output directory: {output_path}")
    print(f"   Index file: {index_path}")
    print(f"{'=' * 60}")

    return stats


async def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Crawl an entire website and convert pages to markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic usage
    python site_crawler.py https://opencode.ai/docs
    
    # With options
    python site_crawler.py https://opencode.ai/docs --max-pages 50 --delay 1.5
    
    # Headless mode (no visible browser)
    python site_crawler.py https://opencode.ai/docs --headless
    
    # Crawl entire domain (not just path)
    python site_crawler.py https://example.com --no-stay-within-path
        """,
    )

    parser.add_argument("url", help="Starting URL to crawl")
    parser.add_argument(
        "--output-dir",
        "-o",
        default="./crawled_site",
        help="Output directory (default: ./crawled_site)",
    )
    parser.add_argument(
        "--max-pages",
        "-m",
        type=int,
        default=100,
        help="Maximum pages to crawl (default: 100)",
    )
    parser.add_argument(
        "--delay",
        "-d",
        type=float,
        default=1.0,
        help="Delay between requests in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (default: visible)",
    )
    parser.add_argument(
        "--no-stay-within-path",
        action="store_true",
        help="Crawl entire domain, not just URLs under start path",
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Reduce output verbosity"
    )

    args = parser.parse_args()

    await crawl_site(
        start_url=args.url,
        output_dir=args.output_dir,
        max_pages=args.max_pages,
        delay=args.delay,
        stay_within_path=not args.no_stay_within_path,
        headless=args.headless,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    asyncio.run(main())
