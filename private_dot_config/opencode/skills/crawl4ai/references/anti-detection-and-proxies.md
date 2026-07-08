# Anti-Detection And Proxies

Use this reference only for authorized crawling when normal browser rendering is blocked by bot detection, corporate egress requirements, proxy routing, or rate-limit troubleshooting. Do not use it to bypass access controls, paywalls, or site policies.

## Proxy Configuration

```python
from crawl4ai import BrowserConfig

browser_config = BrowserConfig(
    headless=True,
    proxy_config={
        "server": "http://proxy.server:8080",
        "username": "user",
        "password": "pass",
    },
)
```

Do not print proxy credentials or write them into crawl artifacts. Prefer environment-injected secrets when credentials are required.

## Visible Browser Mode

Some sites behave differently in headless mode. Retry with a visible browser only when headless extraction fails:

```bash
uvx --from crawl4ai python scripts/site_crawler.py <url> -o <output-dir> --visible
```

For one-page debugging, adapt `BrowserConfig(headless=False)` in a task-local script.

## User Agent And Viewport Tuning

```python
from crawl4ai import BrowserConfig

browser_config = BrowserConfig(
    headless=True,
    viewport_width=1920,
    viewport_height=1080,
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
)
```

For stealth/undetected browsing, consider:

- Rotating user agents via `user_agent`.
- Using realistic viewport sizes.
- Adding delays between requests.
- Reducing concurrency for rate-sensitive sites.

## Rate Limiting

```python
import asyncio

for url in urls:
    result = await crawler.arun(url)
    await asyncio.sleep(2)
```

Completion: the crawl succeeds without aggressive retries, failures/rate limits are reported, and the pipeline remains within the authorized crawl boundary.
