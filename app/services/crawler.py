from crawl4ai import AsyncWebCrawler
from app.services.gemini_llm import generate_content
# from crawl4ai import crawl_url
import re

async def scrape_with_crawl4ai(url) -> str:
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url)
        print(result.markdown[:300])  # Print first 300 chars
        return result.markdown
    
import requests
from bs4 import BeautifulSoup

def crawl_urls(urls: list) -> dict:
    """
    Scrape multiple URLs and return their text content in a dictionary keyed by URL.
    """
    scraped_data = {}
    for url in urls:
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            paragraphs = soup.find_all('p')
            page_content = "\n".join([para.get_text() for para in paragraphs])
            scraped_data[url] = page_content
        except Exception as e:
            scraped_data[url] = f"Error scraping {url}: {e}"
    return scraped_data

def clean_markdown(text):
    # Basic cleaning & markdown safety
    text = re.sub(r'\n{2,}', '\n\n', text)
    return text.strip()

def create_mdx_prompt(topic: str, subtopic: str, relevant_content: str) -> str:
    """
    Generates a refined prompt that ensures a single valid MDX code block,
    including front matter and headings. The output can be directly rendered.
    """
    return f"""You are a documentation formatter. 
Please generate a single MDX code block that starts with ```mdx, includes a front matter block (using triple dashes),
and then the headings and body in properly formatted MDX, ending with triple backticks. 
Do not include any extra backticks or code blocks outside the main one. 
Use the content provided below as the main body.

Topic: {topic}
Subtopic: {subtopic}

Relevant content:
{relevant_content}
"""

def generate_mdx_document(urls: list, topics_data: list) -> str:
    """
    Crawl the given list of URLs, extract content relevant to each subtopic in topics_data,
    and convert it to a well-formatted MDX string using the generate_content function.
    """
    mdx_output = "# Lesson Plan\n\n"
    # Crawl all URLs at once
    scraped_data = crawl_urls(urls)
    # print(scraped_data)

    for topic_block in topics_data:
        topic = topic_block["topic"]
        subtopics = topic_block["subtopics"]
        mdx_output += f"## {topic}\n\n"

        for sub in subtopics:
            print(f"Processing subtopic: {sub}")
            all_relevant_content = ""

            # Gather relevant content from each crawled page using Gemini LLM
            for url, content in scraped_data.items():
                if isinstance(content, str):
                    try:
                        # print(content)
                        # Use Gemini LLM to extract relevant content for the subtopic
                        prompt = f"Extract content relevant to the subtopic '{sub}' from the following text:\n\n{content}"
                        print(prompt)
                        relevant_content = generate_content(prompt)
                        all_relevant_content += clean_markdown(relevant_content) + "\n"
                    except Exception as e:
                        print(f"Error extracting content for {url}: {e}")
            
            # print("All relevant content:", all_relevant_content[:300])  # Print first 300 chars

            # If we found something, call generate_content; else note no content found
            if all_relevant_content.strip():
                try:
                    prompt = create_mdx_prompt(topic, sub, all_relevant_content)
                    print("MDX prompt:", prompt)
                    generated_mdx = generate_content(prompt)
                    mdx_output += clean_markdown(generated_mdx) + "\n\n"
                except Exception as e:
                    mdx_output += f"*Error generating content for this subtopic: {e}.*\n\n"
            else:
                mdx_output += "*Content not found for this subtopic.*\n\n"

    return mdx_output
