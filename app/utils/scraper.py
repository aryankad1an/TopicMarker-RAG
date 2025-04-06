import requests
from bs4 import BeautifulSoup

def scrape_website(url: str) -> str:
    """
    Scrape the provided URL and extract text content.
    """
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            paragraphs = soup.find_all("p")
            content = "\n".join(p.get_text() for p in paragraphs)
            return content
        else:
            return f"Error fetching content from {url}"
    except Exception as e:
        return f"Exception occurred: {e}"
