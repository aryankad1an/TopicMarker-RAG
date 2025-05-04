#!/usr/bin/env python3
"""
Test script for the direct crawl-to-LLM pipeline.
"""

import asyncio
import json
import requests
from pprint import pprint

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_direct_crawl():
    """
    Test the direct crawl-to-LLM endpoint.
    """
    url = "https://docs.crawl4ai.com/"
    query = "Summarize the key features of crawl4ai in bullet points."
    
    response = requests.post(
        f"{BASE_URL}/rag/direct-crawl",
        json={"url": url, "query": query}
    )
    
    print("Status Code:", response.status_code)
    if response.status_code == 200:
        data = response.json()
        print("\nResponse:")
        pprint(data)
    else:
        print("Error:", response.text)

def test_direct_multi_crawl():
    """
    Test the direct multi-crawl-to-LLM endpoint.
    """
    urls = [
        "https://docs.crawl4ai.com/",
        "https://docs.crawl4ai.com/core/quickstart/"
    ]
    query = "Compare the information from these pages and provide a comprehensive overview of crawl4ai."
    
    response = requests.post(
        f"{BASE_URL}/rag/direct-multi-crawl",
        json={"urls": urls, "query": query}
    )
    
    print("Status Code:", response.status_code)
    if response.status_code == 200:
        data = response.json()
        print("\nResponse:")
        pprint(data)
    else:
        print("Error:", response.text)

def test_generate_mdx_from_url():
    """
    Test the generate-mdx-from-url endpoint.
    """
    url = "https://docs.crawl4ai.com/"
    topic = "Crawl4AI: A Modern Web Crawler"
    
    response = requests.post(
        f"{BASE_URL}/rag/generate-mdx-from-url",
        json={"url": url, "topic": topic}
    )
    
    print("Status Code:", response.status_code)
    if response.status_code == 200:
        data = response.json()
        print("\nResponse (first 500 characters of MDX content):")
        if "mdx_content" in data:
            print(data["mdx_content"][:500])
            
            # Save the MDX content to a file
            with open("crawl4ai_mdx_from_api.mdx", "w") as f:
                f.write(data["mdx_content"])
            print("\nFull MDX content saved to crawl4ai_mdx_from_api.mdx")
        else:
            pprint(data)
    else:
        print("Error:", response.text)

if __name__ == "__main__":
    print("=== Test 1: Direct Crawl to LLM ===")
    test_direct_crawl()
    
    print("\n=== Test 2: Direct Multi-Crawl to LLM ===")
    test_direct_multi_crawl()
    
    print("\n=== Test 3: Generate MDX from URL ===")
    test_generate_mdx_from_url()
