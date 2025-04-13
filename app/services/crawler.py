from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def crawl_url(url: str) -> str:
    # Configure a generous page timeout
    run_config = CrawlerRunConfig(
        page_timeout=60_000,            # 60 s max for navigation + JS
        delay_before_return_html=2.0    # optional extra wait before extraction
    )

    async with AsyncWebCrawler() as crawler:
        try:
            result = await crawler.arun(url=url, config=run_config)
        except Exception as e:
            # Network error, Playwright timeout, etc.—skip this URL
            print(f"⚠️ Skipping {url}: {e}")
            return ""  

        # Even if no exception, the crawl might still “fail” (e.g. 404, blocked)
        if not result.success:
            print(f"⚠️ Skipping {url}: {result.error_message} (status {result.status_code})")
            return ""

        # Otherwise return the cleaned-up markdown
        return result.markdown
