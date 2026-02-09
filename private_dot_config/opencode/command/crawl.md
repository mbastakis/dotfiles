---
description: Crawl websites using crawl4ai and return structured results
---

Crawl web pages and persist content to ai-docs/.

## Arguments

- `<url>` — URL to crawl (required)
- `--full` — Crawl entire site (all pages in domain/subdomains)
- `--query "<text>"` — Adaptive search - finds relevant content and stops
- `--max-pages <n>` — Limit pages for --full crawls (default: 250)

## Workflow

### Step 1: Parse $ARGUMENTS

Extract from $ARGUMENTS:

- URL (required) — the target URL to crawl
- `--full` flag (boolean) — if present, crawl entire site
- `--query` value (optional string) — if present, use adaptive search
- `--max-pages` value (optional number, default 250) — page limit

If no URL is provided, return an error:

```json
{
  "status": "error",
  "error": "URL is required. Usage: /crawl <url> [--full] [--query \"<text>\"] [--max-pages <n>]"
}
```

### Step 2: Derive output directory

Extract tool name from URL domain:

- `hono.dev` → `ai-docs/hono/`
- `docs.astro.build` → `ai-docs/astro/`
- `react.dev` → `ai-docs/react/`

Rule: Strip `docs.`, `www.`, and TLD to get base name.

### Step 3: Determine crawl script

| Flags Present | Script to Use         |
| ------------- | --------------------- |
| `--query`     | `adaptive_crawler.py` |
| `--full`      | `site_crawler.py`     |
| (neither)     | `basic_crawler.py`    |

### Step 4: Delegate to @crawl subagent

Use the Task tool to invoke the crawl subagent:

```
task({
  subagent_type: "crawl",
  description: "Crawl <domain>",
  prompt: `
Crawl the following URL and save content to the specified directory.

URL: <url>
Output directory: ai-docs/<tool-name>/
Crawl type: <basic | full site | adaptive search>
Options:
- --full: <true/false>
- --query: <query text or "none">
- --max-pages: <number or "default">

Execute the appropriate crawler script based on crawl type.
Return JSON result only - no explanatory text.
`
})
```

### Step 5: Return result

Output the JSON response from the subagent exactly as received.

## Examples

**Single page:**

```
/crawl https://hono.dev/docs/getting-started
```

**Full site crawl:**

```
/crawl --full https://hono.dev/docs
```

**Adaptive search:**

```
/crawl --query "authentication middleware" https://hono.dev/docs
```

**Full crawl with limit:**

```
/crawl --full --max-pages 100 https://docs.astro.build
```

<user-request>
$ARGUMENTS
</user-request>
