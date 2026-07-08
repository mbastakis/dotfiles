#!/usr/bin/env python3
"""
Crawl4AI extraction pipeline - Three approaches:
1. Generate schema with LLM (one-time) then use CSS extraction (most efficient)
2. Manual CSS/JSON schema extraction
3. Direct LLM extraction (for complex/irregular content)

Usage examples:
  Generate schema: python extraction_pipeline.py --generate-schema <url> "<instruction>"
  Use generated schema: python extraction_pipeline.py --use-schema <url> schema.json
  Manual CSS: python extraction_pipeline.py --css <url> "<css_selector>"
  Direct LLM: python extraction_pipeline.py --llm <url> "<instruction>"
"""

import asyncio
import sys
import json
from pathlib import Path

# Version check
MIN_CRAWL4AI_VERSION = "0.7.4"
try:
    from crawl4ai.__version__ import __version__
    from packaging import version
    if version.parse(__version__) < version.parse(MIN_CRAWL4AI_VERSION):
        print(f"⚠️  Warning: Crawl4AI {MIN_CRAWL4AI_VERSION}+ recommended (you have {__version__})")
except ImportError:
    print(f"ℹ️  Crawl4AI {MIN_CRAWL4AI_VERSION}+ required")

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import (
    LLMExtractionStrategy,
    JsonCssExtractionStrategy,
    CosineStrategy
)


def resolve_output_path(output_dir: str, filename: str) -> Path:
    """Resolve an artifact path, preserving absolute filenames."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    path = Path(filename)
    return path if path.is_absolute() else output_path / path

# =============================================================================
# APPROACH 1: Generate Schema (Most Efficient for Repetitive Patterns)
# =============================================================================

async def generate_schema(
    url: str,
    instruction: str,
    output_file: str = "generated_schema.json",
    output_dir: str = ".",
):
    """
    Step 1: Generate a reusable schema using LLM (one-time cost)
    Best for: E-commerce sites, blogs, news sites with repetitive patterns
    """
    print("🔍 Generating extraction schema using LLM...")

    browser_config = BrowserConfig(headless=True)

    # Use LLM to analyze the page structure and generate schema
    extraction_strategy = LLMExtractionStrategy(
        provider="openai/gpt-4o-mini",  # Can use any LLM provider
        instruction=f"""
        Analyze this webpage and generate a CSS/JSON extraction schema.
        Task: {instruction}

        Return a JSON schema with CSS selectors that can extract the required data.
        Format:
        {{
            "name": "items",
            "selector": "main_container_selector",
            "fields": [
                {{"name": "field1", "selector": "css_selector", "type": "text"}},
                {{"name": "field2", "selector": "css_selector", "type": "link"}},
                // more fields...
            ]
        }}

        Make selectors as specific as possible to avoid false matches.
        """
    )

    crawler_config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy,
        wait_for="css:body",
        remove_overlay_elements=True
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=crawler_config)

        if result.success and result.extracted_content:
            try:
                # Parse and save the generated schema
                schema = json.loads(result.extracted_content)

                # Validate and enhance schema
                if "name" not in schema:
                    schema["name"] = "items"
                if "fields" not in schema:
                    print("⚠️ Generated schema missing fields, using fallback")
                    schema = {
                        "name": "items",
                        "baseSelector": "div.item, article, .product",
                        "fields": [
                            {"name": "title", "selector": "h1, h2, h3", "type": "text"},
                            {"name": "description", "selector": "p", "type": "text"},
                            {"name": "link", "selector": "a", "type": "attribute", "attribute": "href"}
                        ]
                    }

                # Save schema
                output_path = resolve_output_path(output_dir, output_file)
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(schema, f, indent=2)

                print(f"✅ Schema generated and saved to: {output_path}")
                print(f"📋 Schema structure:")
                print(json.dumps(schema, indent=2))

                return schema

            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse generated schema: {e}")
                print("Raw output:", result.extracted_content[:500])
                return None
        else:
            print(f"❌ Failed to generate schema: {result.error_message if result else 'Unknown error'}")
            return None

async def use_generated_schema(url: str, schema_file: str, output_dir: str = "."):
    """
    Step 2: Use the generated schema for fast, repeated extractions
    No LLM calls needed - pure CSS extraction
    """
    print(f"📂 Loading schema from: {schema_file}")

    try:
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = json.load(f)
    except FileNotFoundError:
        print(f"❌ Schema file not found: {schema_file}")
        print("💡 Generate a schema first using: python extraction_pipeline.py --generate-schema <url> \"<instruction>\"")
        return None

    print("🚀 Extracting data using generated schema (no LLM calls)...")

    extraction_strategy = JsonCssExtractionStrategy(
        schema=schema,
        verbose=True
    )

    crawler_config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy,
        wait_for="css:body"
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=crawler_config)

        if result.success and result.extracted_content:
            data = json.loads(result.extracted_content)
            items = data.get(schema.get("name", "items"), [])

            print(f"✅ Extracted {len(items)} items using schema")

            # Save results
            output_path = resolve_output_path(output_dir, "extracted_data.json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"💾 Saved to {output_path}")

            # Show sample
            if items:
                print("\n📋 Sample (first item):")
                print(json.dumps(items[0], indent=2))

            return data
        else:
            print(f"❌ Extraction failed: {result.error_message if result else 'Unknown error'}")
            return None

# =============================================================================
# APPROACH 2: Manual Schema Definition
# =============================================================================

async def extract_with_manual_schema(url: str, schema: dict = None, output_dir: str = "."):
    """
    Use a manually defined CSS/JSON schema
    Best for: When you know the exact structure of the website
    """

    if not schema:
        # Example schema for general content extraction
        schema = {
            "name": "content",
            "baseSelector": "body",  # Changed from 'selector' to 'baseSelector'
            "fields": [
                {"name": "title", "selector": "h1", "type": "text"},
                {"name": "paragraphs", "selector": "p", "type": "text", "all": True},
                {"name": "links", "selector": "a", "type": "attribute", "attribute": "href", "all": True}
            ]
        }

    print("📐 Using manual CSS/JSON schema for extraction...")

    extraction_strategy = JsonCssExtractionStrategy(
        schema=schema,
        verbose=True
    )

    crawler_config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=crawler_config)

        if result.success and result.extracted_content:
            data = json.loads(result.extracted_content)
            # Handle both list and dict formats
            if isinstance(data, list):
                items = data
            else:
                items = data.get(schema["name"], [])

            print(f"✅ Extracted {len(items)} items using manual schema")

            output_path = resolve_output_path(output_dir, "manual_extracted.json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"💾 Saved to {output_path}")

            return data
        else:
            print(f"❌ Extraction failed")
            return None

# =============================================================================
# APPROACH 3: Direct LLM Extraction
# =============================================================================

async def extract_with_llm(url: str, instruction: str, output_dir: str = "."):
    """
    Direct LLM extraction - uses LLM for every request
    Best for: Complex, irregular content or one-time extractions
    Note: Most expensive approach, use sparingly
    """
    print("🤖 Using direct LLM extraction...")

    browser_config = BrowserConfig(headless=True)

    extraction_strategy = LLMExtractionStrategy(
        provider="openai/gpt-4o-mini",  # Can change to ollama/llama3, anthropic/claude, etc.
        instruction=instruction,
        schema={
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"type": "object"}
                },
                "summary": {"type": "string"}
            }
        }
    )

    crawler_config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy,
        wait_for="css:body",
        remove_overlay_elements=True
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=crawler_config)

        if result.success and result.extracted_content:
            try:
                data = json.loads(result.extracted_content)
                items = data.get('items', [])

                print(f"✅ LLM extracted {len(items)} items")
                print(f"📝 Summary: {data.get('summary', 'N/A')}")

                output_path = resolve_output_path(output_dir, "llm_extracted.json")
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                print(f"💾 Saved to {output_path}")

                if items:
                    print("\n📋 Sample (first item):")
                    print(json.dumps(items[0], indent=2))

                return data
            except json.JSONDecodeError:
                print("⚠️ Could not parse LLM output as JSON")
                print(result.extracted_content[:500])
                return None
        else:
            print(f"❌ LLM extraction failed")
            return None

# =============================================================================
# Main CLI Interface
# =============================================================================

async def main():
    args = sys.argv[1:]
    output_dir = "."
    for flag in ("--output-dir", "-o"):
        if flag in args:
            idx = args.index(flag)
            if idx + 1 >= len(args):
                print(f"Error: Missing value for {flag}")
                sys.exit(1)
            output_dir = args[idx + 1]
            del args[idx:idx + 2]
            break

    if len(args) < 2:
        print("""
Crawl4AI Extraction Pipeline - Three Approaches

1️⃣  GENERATE & USE SCHEMA (Most Efficient for Repetitive Patterns):
    Step 1: Generate schema (one-time LLM cost)
    python extraction_pipeline.py --generate-schema <url> "<what to extract>" --output-dir ./extract-output

    Step 2: Use schema for fast extraction (no LLM)
    python extraction_pipeline.py --use-schema <url> generated_schema.json --output-dir ./extract-output

2️⃣  MANUAL SCHEMA (When You Know the Structure):
    python extraction_pipeline.py --manual <url>
    (Edit the schema in the script for your needs)

3️⃣  DIRECT LLM (For Complex/Irregular Content):
    python extraction_pipeline.py --llm <url> "<extraction instruction>"

Examples:
    # E-commerce products
    python extraction_pipeline.py --generate-schema https://shop.com "Extract all products with name, price, image"
    python extraction_pipeline.py --use-schema https://shop.com generated_schema.json

    # News articles
    python extraction_pipeline.py --generate-schema https://news.com "Extract headlines, dates, and summaries"

    # Complex content
    python extraction_pipeline.py --llm https://complex-site.com "Extract financial data and quarterly reports"
""")
        sys.exit(1)

    mode = args[0]
    url = args[1]

    if mode == "--generate-schema":
        if len(args) < 3:
            print("Error: Missing extraction instruction")
            print("Usage: python extraction_pipeline.py --generate-schema <url> \"<instruction>\" [output_schema.json] [--output-dir DIR]")
            sys.exit(1)
        instruction = args[2]
        output_file = args[3] if len(args) > 3 else "generated_schema.json"
        await generate_schema(url, instruction, output_file, output_dir=output_dir)

    elif mode == "--use-schema":
        if len(args) < 3:
            print("Error: Missing schema file")
            print("Usage: python extraction_pipeline.py --use-schema <url> <schema.json> [--output-dir DIR]")
            sys.exit(1)
        schema_file = args[2]
        await use_generated_schema(url, schema_file, output_dir=output_dir)

    elif mode == "--manual":
        await extract_with_manual_schema(url, output_dir=output_dir)

    elif mode == "--llm":
        if len(args) < 3:
            print("Error: Missing extraction instruction")
            print("Usage: python extraction_pipeline.py --llm <url> \"<instruction>\" [--output-dir DIR]")
            sys.exit(1)
        instruction = args[2]
        await extract_with_llm(url, instruction, output_dir=output_dir)

    else:
        print(f"Unknown mode: {mode}")
        print("Use --generate-schema, --use-schema, --manual, or --llm")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
