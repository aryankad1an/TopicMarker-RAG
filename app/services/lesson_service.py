import time
from app.utils import llm_client, scraper

def generate_lesson(topic: str, difficulty: str):
    # Step 1: Fetch URLs related to the topic using the LLM client
    urls = llm_client.fetch_resource_urls(topic, difficulty)
    
    mdx_content = ""
    for url in urls:
        # Step 2: Scrape content from each website
        content = scraper.scrape_website(url)
        # Step 3: Improve content iteratively using the LLM
        improved_content = llm_client.improve_content(content)
        # Append the improved content to the final MDX output
        mdx_content += f"\n\n---\n\n{improved_content}"
        # Optional: delay between processing requests
        time.sleep(1)
    
    # Final step: Log the final MDX content or store it in the database
    print("Final MDX Content Generated:\n", mdx_content)
