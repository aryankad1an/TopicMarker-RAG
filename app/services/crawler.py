import asyncio
from crawl4ai import AsyncWebCrawler

async def scrape_with_crawl4ai(url) -> str:
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url)
        print(result.markdown[:300])  # Print first 300 chars
        return result.markdown