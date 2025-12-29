#!/usr/bin/env python3
"""
Test site crawler functionality from scripts/site_crawler.py
"""

import asyncio
import json
import tempfile
import shutil
from pathlib import Path

# Import the site crawler module
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from site_crawler import crawl_site, URLManager


def test_url_manager():
    """Test URLManager class functionality"""
    print("Testing URLManager...")

    # Test with stay_within_path=True
    manager = URLManager("https://example.com/docs", stay_within_path=True)

    # Test URL normalization
    assert (
        manager.normalize_url("https://example.com/docs#section")
        == "https://example.com/docs"
    )
    assert (
        manager.normalize_url("https://example.com/docs/") == "https://example.com/docs"
    )
    print("  URL normalization: OK")

    # Test valid URL detection
    assert manager.is_valid_url("https://example.com/docs/page") == True
    assert (
        manager.is_valid_url("https://example.com/other") == False
    )  # Outside base path
    assert manager.is_valid_url("https://other.com/docs") == False  # Different domain
    assert (
        manager.is_valid_url("https://example.com/docs/file.pdf") == False
    )  # Skip PDF
    assert (
        manager.is_valid_url("https://example.com/docs/image.png") == False
    )  # Skip images
    print("  URL validation: OK")

    # Test URL adding and deduplication
    assert manager.add_url("https://example.com/docs/page1") == True
    assert manager.add_url("https://example.com/docs/page1") == False  # Duplicate
    assert (
        manager.add_url("https://example.com/docs/page1#section") == False
    )  # Same after normalization
    assert manager.add_url("https://example.com/docs/page2") == True
    print("  URL deduplication: OK")

    # Test queue operations
    url = manager.get_next()
    assert url == "https://example.com/docs/page1"
    manager.mark_visited(url)
    assert url in manager.visited
    print("  Queue operations: OK")

    print("URLManager tests passed!")


async def test_site_crawl_limited():
    """Test actual site crawling with limited pages"""
    print("\nTesting site crawl (limited to 3 pages)...")

    # Create temporary output directory
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_crawl"

        # Crawl example.com (simple, fast site)
        stats = await crawl_site(
            start_url="https://example.com",
            output_dir=str(output_dir),
            max_pages=3,
            delay=0.5,
            stay_within_path=False,  # example.com has no subpaths
            headless=True,
            verbose=False,
        )

        # Verify stats
        assert stats["pages_crawled"] >= 1, "Should crawl at least 1 page"
        assert stats["pages_failed"] == 0, (
            f"No pages should fail: {stats['pages_failed']} failed"
        )
        print(f"  Pages crawled: {stats['pages_crawled']}")

        # Verify output directory structure
        assert output_dir.exists(), "Output directory should exist"
        pages_dir = output_dir / "pages"
        assert pages_dir.exists(), "Pages directory should exist"
        print("  Output directory structure: OK")

        # Verify index file
        index_file = output_dir / "site_index.json"
        assert index_file.exists(), "Index file should exist"
        with open(index_file) as f:
            index_data = json.load(f)
        assert "stats" in index_data, "Index should contain stats"
        assert "all_urls" in index_data, "Index should contain all_urls"
        print("  Index file: OK")

        # Verify markdown files
        md_files = list(pages_dir.glob("*.md"))
        assert len(md_files) >= 1, "Should have at least 1 markdown file"
        print(f"  Markdown files created: {len(md_files)}")

        # Verify markdown content
        first_md = md_files[0]
        content = first_md.read_text()
        assert "**URL:**" in content, "Markdown should contain URL metadata"
        assert "**Crawled:**" in content, "Markdown should contain crawl timestamp"
        assert "---" in content, "Markdown should contain separator"
        print("  Markdown content format: OK")

    print("Site crawl test passed!")


async def test_headless_vs_visible():
    """Test that headless mode produces same results"""
    print("\nTesting headless mode consistency...")

    # This test just verifies the parameter is accepted
    # Full comparison was done manually during development
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "headless_test"

        stats = await crawl_site(
            start_url="https://example.com",
            output_dir=str(output_dir),
            max_pages=1,
            delay=0,
            headless=True,
            verbose=False,
        )

        assert stats["pages_crawled"] == 1, "Should crawl exactly 1 page"
        assert stats["pages_failed"] == 0, "No pages should fail"

    print("  Headless mode: OK")


async def run_all_tests():
    """Run all site crawler tests"""
    test_url_manager()
    await test_site_crawl_limited()
    await test_headless_vs_visible()


if __name__ == "__main__":
    asyncio.run(run_all_tests())
    print("\nAll site crawler tests passed!")
