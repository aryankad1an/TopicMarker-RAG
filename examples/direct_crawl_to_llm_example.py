#!/usr/bin/env python3
"""
Example script demonstrating the direct pipeline from crawl4ai to LLM.
"""

import asyncio
from app.services.crawler import (
    direct_crawl_to_llm,
    direct_multi_crawl_to_llm,
    generate_mdx_from_url
)

def example_direct_crawl_to_llm():
    """
    Example of direct crawl to LLM pipeline.
    """
    url = "https://docs.crawl4ai.com/"
    query = "Summarize the key features of crawl4ai in bullet points."
    
    print(f"Crawling {url} and sending to LLM with query: {query}")
    result = direct_crawl_to_llm(url, query)
    
    print("\nResult:")
    print(result)

def example_direct_multi_crawl_to_llm():
    """
    Example of direct multi-crawl to LLM pipeline.
    """
    urls = [
        "https://docs.crawl4ai.com/",
        "https://docs.crawl4ai.com/core/quickstart/"
    ]
    query = "Compare the information from these pages and provide a comprehensive overview of crawl4ai."
    
    print(f"Crawling {len(urls)} URLs and sending to LLM with query: {query}")
    result = direct_multi_crawl_to_llm(urls, query)
    
    print("\nResult:")
    print(result)

def example_generate_mdx_from_url():
    """
    Example of generating MDX content directly from a URL.
    """
    url = "https://docs.crawl4ai.com/"
    topic = "Crawl4AI: A Modern Web Crawler"
    
    print(f"Generating MDX content from {url} about {topic}")
    result = generate_mdx_from_url(url, topic)
    
    print("\nResult (first 500 characters):")
    print(result[:500])
    
    # Save the result to a file
    with open("crawl4ai_mdx.mdx", "w") as f:
        f.write(result)
    print("\nFull MDX content saved to crawl4ai_mdx.mdx")

if __name__ == "__main__":
    print("=== Example 1: Direct Crawl to LLM ===")
    example_direct_crawl_to_llm()
    
    print("\n=== Example 2: Direct Multi-Crawl to LLM ===")
    example_direct_multi_crawl_to_llm()
    
    print("\n=== Example 3: Generate MDX from URL ===")
    example_generate_mdx_from_url()
