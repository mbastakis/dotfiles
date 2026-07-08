# Troubleshooting

Use this reference when a crawl pipeline produces empty content, stops before the boundary is exhausted, needs session state, or extracts malformed data.

## Empty Or Thin Content

First confirm whether the task is ordinary single-page reading. If yes, try defuddle-style extraction before Crawl4AI. Use Crawl4AI when ordinary extraction returns blank, thin, or pre-render HTML for content that should be visible after JavaScript runs.

For JavaScript-rendered pages:

```python
from crawl4ai import CrawlerRunConfig

config = CrawlerRunConfig(
    wait_for="css:.content, main, [role=main]",
    page_timeout=60000,
    remove_overlay_elements=True,
    screenshot=True,
)
```

Completion: extracted markdown/JSON contains the rendered content the ordinary extraction missed, or the failure names the selector/timeout problem.

## Incomplete Site Crawls

For a requested all-pages crawl, inspect `site_index.json`:

- `stats.crawl_complete` should be `true`.
- `stats.urls_in_queue_remaining` should be `0`.
- `stats.pages_failed` should have recorded reasons.

If in-bound URLs remain queued, continue with the same output directory:

```bash
uvx --from crawl4ai python scripts/site_crawler.py <url> -o <output-dir> --resume --complete
```

If the user set `--max-total-pages`, stop at that cap and report the crawl as incomplete by explicit cap.

## Session Or Authenticated Crawls

Use session crawling only with user authorization. Prefer task-provided session state or secrets injected by the environment. Do not print passwords, tokens, cookies, or authorization headers; do not save them in markdown, JSON summaries, screenshots, or logs.

Typical pattern:

```python
from crawl4ai import CrawlerRunConfig

login_config = CrawlerRunConfig(
    session_id="authorized_session",
    wait_for="css:.dashboard",
)

followup_config = CrawlerRunConfig(session_id="authorized_session")
```

Completion: protected pages were reached through an authorized session, artifacts omit credentials, and failures distinguish authentication failure from extraction failure.

## Structured Extraction Failures

For repeated data, prefer CSS/JSON schema extraction. If fields come back empty:

- Test selectors on one representative page.
- Check whether content renders after JavaScript and needs `wait_for`.
- Record missing required fields as failures.
- Use fallback selectors or multiple schemas only when page templates genuinely differ.

Direct LLM extraction is a fallback for irregular one-off content, not the steady-state path for repeated pages.
