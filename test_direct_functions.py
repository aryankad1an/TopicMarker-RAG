#!/usr/bin/env python3
"""
Test script for the direct crawl-to-LLM pipeline using direct function calls.
"""

import asyncio
from app.services.crawler import (
    direct_crawl_to_llm,
    direct_multi_crawl_to_llm,
    generate_mdx_from_url
)

def test_direct_crawl():
    """
    Test the direct crawl-to-LLM function.
    """
    url = "https://en.wikipedia.org/wiki/Dynamic_programming"
    query = "Summarize the key concepts of dynamic programming in bullet points."
    
    print(f"Crawling {url} and sending to LLM with query: {query}")
    result = direct_crawl_to_llm(url, query)
    
    print("\nResult:")
    print(result)

def test_direct_multi_crawl():
    """
    Test the direct multi-crawl-to-LLM function.
    """
    urls = [
        "https://en.wikipedia.org/wiki/Dynamic_programming",
        "https://www.geeksforgeeks.org/dynamic-programming/"
    ]
    query = "Compare the information from these pages and provide a comprehensive overview of dynamic programming."
    
    print(f"Crawling {len(urls)} URLs and sending to LLM with query: {query}")
    result = direct_multi_crawl_to_llm(urls, query)
    
    print("\nResult:")
    print(result)

def test_generate_mdx_from_url():
    """
    Test the generate MDX from URL function.
    """
    url = "https://en.wikipedia.org/wiki/Dynamic_programming"
    topic = "Dynamic Programming: A Comprehensive Guide"
    
    print(f"Generating MDX content from {url} about {topic}")
    result = generate_mdx_from_url(url, topic)
    
    print("\nResult (first 500 characters):")
    print(result[:500])
    
    # Save the result to a file
    with open("dynamic_programming_mdx.mdx", "w") as f:
        f.write(result)
    print("\nFull MDX content saved to dynamic_programming_mdx.mdx")

if __name__ == "__main__":
    print("=== Test 1: Direct Crawl to LLM ===")
    test_direct_crawl()
    
    print("\n=== Test 2: Direct Multi-Crawl to LLM ===")
    test_direct_multi_crawl()
    
    print("\n=== Test 3: Generate MDX from URL ===")
    test_generate_mdx_from_url()
