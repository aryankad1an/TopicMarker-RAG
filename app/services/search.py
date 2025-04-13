from duckduckgo_search import DDGS
from app.config import settings

def search_urls(query: str, limit: int = None) -> list[str]:
    max_results = limit or settings.duckduckgo_result_count
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=max_results)
        return [res['href'] for res in results if 'href' in res]
