import asyncio
from crawl4ai import AsyncWebCrawler

async def extract_text_from_url(url) -> str:
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url)
        print(result.markdown[:300])  # Print first 300 chars
        return result.markdown