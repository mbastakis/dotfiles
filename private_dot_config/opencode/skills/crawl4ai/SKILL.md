---
name: crawl4ai
description: Crawl4AI crawl pipeline for multi-page crawls, full-site scraping, JavaScript-rendered pages that ordinary extraction cannot read, authenticated/session crawling with user authorization, structured repeated extraction, and persisted web data collection. Use defuddle for ordinary single-page reading; use this for /crawl archival, full scrape/extract all pages, schemas, sessions, or browser-rendered fallback.
version: 0.7.4
crawl4ai_version: ">=0.7.4"
last_updated: 2026-07-07
---

# Crawl4AI

Use this skill to choose and run a repeatable **crawl pipeline**. Do not use it as the default reader for one normal web page.

## Routing

| Request | Route |
|---|---|
| Read, summarize, or clean markdown from one ordinary page | Use defuddle-style single-page extraction first |
| One page failed ordinary extraction because content is browser-rendered JavaScript | Use Crawl4AI browser-rendered fallback |
| Search, compare, or synthesize web sources | Use `web-researcher`; escalate here only for crawl pipelines |
| Explicit `/crawl <url>` or save/archive into `ai-docs/` | Use Crawl4AI through `@crawl`; this is persisted archival intent |
| Crawl all pages, full scrape, extract all pages, docs archival | Use `site_crawler.py` with an explicit crawl boundary |
| Crawl a supplied list of URLs | Use `batch_crawler.py` |
| Repeated structured extraction from listings/cards/tables | Use schema-based extraction first |
| Authenticated/session crawl | Use only with user authorization; see troubleshooting/session reference |

If the user says "crawl" ambiguously, ask whether they want a persisted crawl artifact/pipeline or ordinary page reading.

## Pipeline Choice

Run scripts from this skill directory unless the task gives another path.

| Pipeline | Use When | Command Shape |
|---|---|---|
| Single-page fallback or archival | One URL needs browser rendering, filtering, screenshot, or explicit `/crawl` archival | `uvx --from crawl4ai python scripts/basic_crawler.py <url> -o <output-dir>` |
| Exhaustive bounded site crawl | User asks for all pages under a docs path or same-domain boundary | `uvx --from crawl4ai python scripts/site_crawler.py <url> -o <output-dir> --complete --headless` |
| Query-bounded crawl | User asks to collect enough relevant docs for a question | `uvx --from crawl4ai python scripts/adaptive_crawler.py <url> --query "<query>" -o <output-dir>` |
| Supplied URL set | User gives many URLs or a URL file | `uvx --from crawl4ai python scripts/batch_crawler.py urls.txt -o <output-dir>` |
| Repeated structured data | Product cards, listings, tables, API indexes, rerunnable scrape | `uvx --from crawl4ai python scripts/extraction_pipeline.py --generate-schema <url> "<fields>" -o <output-dir>` then `--use-schema` |

Use task-specific output directories. Only `/crawl`/`@crawl` forces `ai-docs/`; other pipelines save wherever the user or task specifies.

## Crawl Boundary

Exhaustive means exhaustive inside a boundary, not an unbounded whole-web crawl. Pick one boundary before running:

- Start path by default, such as all URLs under `/docs`.
- Whole same-domain crawl only when the user asks for full-domain behavior.
- Supplied URL list for batch mode.
- Query-defined relevance boundary for adaptive mode.

For raw `site_crawler.py` use, `--max-pages` is a safety chunk when `--complete` is set. Continue until `site_index.json` reports no queued in-bound URLs. If a hard cap such as `--max-total-pages` stops the crawl, report it as incomplete. The `/crawl` command treats an explicitly supplied `--max-pages <n>` as that hard cap.

## Completion Criteria

Every run must end with artifacts checked, not just a command executed.

- Single-page fallback: markdown or structured output is non-empty, browser-rendered content is materially better than the failed ordinary extraction, and failures are reported instead of treated as success.
- Site crawl: `site_index.json` exists, pages are written under `pages/`, `stats.crawl_complete` is true, `stats.urls_in_queue_remaining` is `0`, and every failure/skip has a reason.
- Site crawl that stops early: resume with `--resume` or rerun with `--complete` until the boundary is exhausted, unless the user set an explicit hard cap.
- Adaptive crawl: `crawl_summary.json` exists, relevant pages are saved, and the final confidence/relevance status is reported.
- Batch crawl: `batch_results.json` exists, markdown files exist for successful URLs, and failed URLs are listed with errors.
- Structured extraction: schema and extracted JSON/CSV artifacts exist, expected fields/items are present, and empty required fields are reported as extraction failures.

## Structured Extraction

Default to schema-based extraction for repeated data:

1. Generate or hand-write a CSS/JSON schema from representative pages.
2. Validate it on one or a few pages.
3. Reuse it across the batch/site without per-page LLM calls.
4. Use direct LLM extraction only for irregular one-off content or when schema extraction cannot express the task.

## Safety And Politeness

- Use same-domain/path boundaries by default.
- Keep delays and modest concurrency unless the user explicitly needs otherwise.
- Respect failures, rate limits, robots/policy signals, and terms that prohibit crawling.
- Crawl authenticated/private content only when the user confirms authorization.
- Never ask for or print raw credentials; never persist credentials in crawl artifacts.

## References

- `references/complete-sdk-reference.md`: SDK details, parameters, advanced Crawl4AI APIs.
- `references/troubleshooting.md`: empty output, JavaScript rendering, incomplete/resume crawls, sessions, extraction failures.
- `references/anti-detection-and-proxies.md`: proxy configuration, user-agent/viewport tuning, visible browser mode, and bot-detection troubleshooting for authorized crawls.
