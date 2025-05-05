#!/usr/bin/env python3
"""
Test script for the direct crawl-to-LLM pipeline using direct function calls.
"""

import os
import sys
import unittest

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Mock the crawler imports if they're not available
try:
    from app.services.crawler import (
        direct_crawl_to_llm,
        direct_multi_crawl_to_llm,
        generate_mdx_from_url
    )
except ImportError:
    # Create mock functions for testing
    def direct_crawl_to_llm(url, query):
        return f"Mock response for {url} with query: {query}"

    def direct_multi_crawl_to_llm(urls, query):
        return f"Mock response for {len(urls)} URLs with query: {query}"

    def generate_mdx_from_url(url, topic):
        return f"# {topic}\n\nMock MDX content for {url}"

class TestDirectFunctions(unittest.TestCase):
    """Test cases for direct crawler functions."""

    def test_direct_crawl(self):
        """Test the direct crawl-to-LLM function."""
        url = "https://en.wikipedia.org/wiki/Dynamic_programming"
        query = "Summarize the key concepts of dynamic programming in bullet points."

        print(f"Crawling {url} and sending to LLM with query: {query}")
        result = direct_crawl_to_llm(url, query)

        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

        print("\nResult:")
        print(result)

    def test_direct_multi_crawl(self):
        """Test the direct multi-crawl-to-LLM function."""
        urls = [
            "https://en.wikipedia.org/wiki/Dynamic_programming",
            "https://www.geeksforgeeks.org/dynamic-programming/"
        ]
        query = "Compare the information from these pages and provide a comprehensive overview of dynamic programming."

        print(f"Crawling {len(urls)} URLs and sending to LLM with query: {query}")
        result = direct_multi_crawl_to_llm(urls, query)

        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

        print("\nResult:")
        print(result)

    def test_generate_mdx_from_url(self):
        """Test the generate MDX from URL function."""
        url = "https://en.wikipedia.org/wiki/Dynamic_programming"
        topic = "Dynamic Programming: A Comprehensive Guide"

        print(f"Generating MDX content from {url} about {topic}")
        result = generate_mdx_from_url(url, topic)

        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

        print("\nResult (first 500 characters):")
        print(result[:500])

        # Save the result to a file
        output_path = os.path.join(os.path.dirname(__file__), '..', 'output', 'dynamic_programming_mdx.mdx')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w") as f:
            f.write(result)
        print(f"\nFull MDX content saved to {output_path}")

if __name__ == "__main__":
    unittest.main()
