# Crawl4AI Skill Tests

This directory contains test scripts that verify the accuracy of all code examples in the SKILL.md file.

## Test Files

1. **executable_test_basic_crawling.py** - Tests basic crawling setup with BrowserConfig and CrawlerRunConfig
2. **executable_test_markdown_generation.py** - Tests markdown generation, fit_markdown, and content filters
3. **executable_test_data_extraction.py** - Tests JSON/CSS extraction and LLM extraction strategies
4. **executable_test_advanced_patterns.py** - Tests session management, proxies, and batch crawling
5. **test_site_crawler.py** - Tests URL boundaries, site crawl output, and headless crawling

## Running Tests

### Run all tests:
```bash
python3 executable_literal_run_all_tests.py
```

### Run individual tests:
```bash
python3 executable_test_basic_crawling.py
python3 executable_test_markdown_generation.py
python3 executable_test_data_extraction.py
python3 executable_test_advanced_patterns.py
python3 test_site_crawler.py
```

## Requirements

- Crawl4AI 0.7.4+
- All tests use example.com/example.org for testing
- LLM tests verify structure only (no API key required for basic validation)

## Test Coverage

✅ Basic crawling configuration
✅ Markdown generation and content filtering
✅ Schema-based data extraction
✅ Session management
✅ Proxy configuration structure
✅ Batch/concurrent crawling

## Notes

- Tests verify that SKILL.md examples are accurate and working
- All parameter names, imports, and API usage are cross-checked against actual Crawl4AI documentation
- Tests use live websites (example.com, example.org) for real-world validation
