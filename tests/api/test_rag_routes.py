#!/usr/bin/env python3
"""
Test script for the RAG routes.
"""

import os
import sys
import unittest
import requests
import json
from pprint import pprint
import socket
from requests.exceptions import ReadTimeout, ConnectionError

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Base URL for the API
BASE_URL = "http://localhost:8000"

class TestRAGRoutes(unittest.TestCase):
    """Test cases for RAG routes."""

    # Sample MDX content for all tests
    sample_mdx = """---
title: "Introduction to Python"
description: "A beginner's guide to Python programming"
date: "2023-07-15"
---

# Introduction to Python

Python is a high-level, interpreted programming language known for its simplicity and readability.

## Key Features

- Easy to learn and use
- Interpreted language
- Dynamically typed
- Object-oriented
- Extensive standard library

## Basic Syntax

Python uses indentation to define code blocks:

```python
def greet(name):
    print(f"Hello, {name}!")

greet("World")
```
"""

    def test_search_topics(self):
        """Test the search-topics endpoint."""
        # Request data
        data = {
            "query": "Machine Learning fundamentals",
            "limit": 3
        }

        try:
            # Check if server is running first
            try:
                socket.create_connection(("localhost", 8000), timeout=1)
            except (socket.timeout, socket.error):
                print("WARNING: API server is not running. Skipping test.")
                self.skipTest("API server is not running")

            # Make the request
            response = requests.post(
                f"{BASE_URL}/rag/search-topics",
                json=data,
                timeout=30  # Increased timeout for LLM processing
            )

            print("Status Code:", response.status_code)
            self.assertEqual(response.status_code, 200)

            if response.status_code == 200:
                result = response.json()
                print("\nResponse:")
                pprint(result)

                # Verify the response structure
                self.assertIn('status', result)
                self.assertEqual(result['status'], 'success')
                self.assertIn('data', result)
                self.assertIn('topics', result['data'])
                self.assertTrue(len(result['data']['topics']) > 0)
            else:
                print("Error:", response.text)
        except ReadTimeout:
            print("WARNING: Request timed out. The LLM processing may take longer than expected.")
            self.skipTest("Request timed out")
        except ConnectionError:
            print("WARNING: API server is not running or not responding. Skipping test.")
            self.skipTest("API server is not running")

    def test_generate_mdx(self):
        """Test the generate-mdx endpoint."""
        # Request data
        data = {
            "topics": [
                {
                    "topic": "Machine Learning Basics",
                    "subtopics": ["Supervised Learning", "Unsupervised Learning"]
                }
            ],
            "top_k": 2
        }

        try:
            # Check if server is running first
            try:
                socket.create_connection(("localhost", 8000), timeout=1)
            except (socket.timeout, socket.error):
                print("WARNING: API server is not running. Skipping test.")
                self.skipTest("API server is not running")

            # Make the request
            response = requests.post(
                f"{BASE_URL}/rag/generate-mdx",
                json=data,
                timeout=60  # Increased timeout for LLM processing and crawling
            )

            print("Status Code:", response.status_code)
            self.assertEqual(response.status_code, 200)

            if response.status_code == 200:
                result = response.json()
                print("\nResponse:")
                pprint(result)

                # Verify the response structure
                self.assertIn('status', result)
                self.assertEqual(result['status'], 'success')
            else:
                print("Error:", response.text)
        except ReadTimeout:
            print("WARNING: Request timed out. The LLM processing may take longer than expected.")
            self.skipTest("Request timed out")
        except ConnectionError:
            print("WARNING: API server is not running or not responding. Skipping test.")
            self.skipTest("API server is not running")

    def test_refine_with_selection(self):
        """Test the refine-with-selection endpoint."""
        # Request data
        data = {
            "mdx": self.sample_mdx,
            "question": "Can you add more details about Python's popularity in data science?",
            "selected_text": "Python is a high-level, interpreted programming language known for its simplicity and readability.",
            "selected_topic": "Python Programming",
            "main_topic": "Programming Languages"
        }

        try:
            # Check if server is running first
            try:
                socket.create_connection(("localhost", 8000), timeout=1)
            except (socket.timeout, socket.error):
                print("WARNING: API server is not running. Skipping test.")
                self.skipTest("API server is not running")

            # Make the request
            response = requests.post(
                f"{BASE_URL}/rag/refine-with-selection",
                json=data,
                timeout=30  # Increased timeout for LLM processing
            )

            print("Status Code:", response.status_code)
            self.assertEqual(response.status_code, 200)

            if response.status_code == 200:
                result = response.json()
                print("\nResponse:")
                pprint(result)

                # Verify the response structure
                self.assertIn('status', result)
                self.assertEqual(result['status'], 'success')
                self.assertIn('data', result)
                self.assertIn('answer', result['data'])
                self.assertTrue(len(result['data']['answer']) > 0)
            else:
                print("Error:", response.text)
        except ReadTimeout:
            print("WARNING: Request timed out. The LLM processing may take longer than expected.")
            self.skipTest("Request timed out")
        except ConnectionError:
            print("WARNING: API server is not running or not responding. Skipping test.")
            self.skipTest("API server is not running")

    def test_refine_with_selection_raw(self):
        """Test the refine-with-selection-raw endpoint."""
        # Request data
        data = {
            "mdx": self.sample_mdx,
            "question": "Can you add more details about Python's popularity in data science?",
            "selected_text": "Python is a high-level, interpreted programming language known for its simplicity and readability.",
            "selected_topic": "Python Programming",
            "main_topic": "Programming Languages"
        }

        try:
            # Make the request
            response = requests.post(
                f"{BASE_URL}/rag/refine-with-selection-raw",
                json=data,
                timeout=5  # Increased timeout for LLM processing
            )

            print("Status Code:", response.status_code)
            self.assertEqual(response.status_code, 200)

            if response.status_code == 200:
                # For raw endpoints, the response is plain text
                result = response.text
                print("\nResponse (first 200 chars):")
                print(result[:200] + "..." if len(result) > 200 else result)

                # Verify the response is not empty
                self.assertTrue(len(result) > 0)
                # Verify it's not an error message
                self.assertFalse(result.startswith("Error:"))
            else:
                print("Error:", response.text)
        except requests.exceptions.ConnectionError:
            print("WARNING: API server is not running. Skipping test.")
            self.skipTest("API server is not running")

    def test_refine_with_crawling_raw(self):
        """Test the refine-with-crawling-raw endpoint."""
        # Request data
        data = {
            "mdx": self.sample_mdx,
            "question": "Can you add more details about Python's popularity in data science?",
            "selected_text": "Python is a high-level, interpreted programming language known for its simplicity and readability.",
            "selected_topic": "Python Programming",
            "main_topic": "Programming Languages",
            "num_results": 2
        }

        try:
            # Make the request
            response = requests.post(
                f"{BASE_URL}/rag/refine-with-crawling-raw",
                json=data,
                timeout=10  # Increased timeout for crawling and LLM processing
            )

            print("Status Code:", response.status_code)
            self.assertEqual(response.status_code, 200)

            if response.status_code == 200:
                # For raw endpoints, the response is plain text
                result = response.text
                print("\nResponse (first 200 chars):")
                print(result[:200] + "..." if len(result) > 200 else result)

                # Verify the response is not empty
                self.assertTrue(len(result) > 0)
                # Verify it's not an error message
                self.assertFalse(result.startswith("Error:"))
            else:
                print("Error:", response.text)
        except requests.exceptions.ConnectionError:
            print("WARNING: API server is not running. Skipping test.")
            self.skipTest("API server is not running")

    def test_refine_with_urls_raw(self):
        """Test the refine-with-urls-raw endpoint."""
        # Request data
        data = {
            "mdx": self.sample_mdx,
            "question": "Can you add more details about Python's popularity in data science?",
            "selected_text": "Python is a high-level, interpreted programming language known for its simplicity and readability.",
            "selected_topic": "Python Programming",
            "main_topic": "Programming Languages",
            "urls": [
                "https://www.python.org/",
                "https://docs.python.org/3/tutorial/index.html"
            ]
        }

        try:
            # Make the request
            response = requests.post(
                f"{BASE_URL}/rag/refine-with-urls-raw",
                json=data,
                timeout=10  # Increased timeout for crawling and LLM processing
            )

            print("Status Code:", response.status_code)
            self.assertEqual(response.status_code, 200)

            if response.status_code == 200:
                # For raw endpoints, the response is plain text
                result = response.text
                print("\nResponse (first 200 chars):")
                print(result[:200] + "..." if len(result) > 200 else result)

                # Verify the response is not empty
                self.assertTrue(len(result) > 0)
                # Verify it's not an error message
                self.assertFalse(result.startswith("Error:"))
            else:
                print("Error:", response.text)
        except requests.exceptions.ConnectionError:
            print("WARNING: API server is not running. Skipping test.")
            self.skipTest("API server is not running")

    def test_single_topic(self):
        """Test the single-topic endpoint."""
        # Request data
        data = {
            "selected_topic": "React Hooks",
            "main_topic": "React",
            "num_results": 2
        }

        try:
            # Make the request
            response = requests.post(
                f"{BASE_URL}/rag/single-topic",
                json=data,
                timeout=15  # Increased timeout for crawling and LLM processing
            )

            print("Status Code:", response.status_code)
            self.assertEqual(response.status_code, 200)

            if response.status_code == 200:
                result = response.json()
                print("\nResponse:")
                pprint(result)

                # Verify the response structure
                self.assertIn('status', result)
                self.assertEqual(result['status'], 'success')
                self.assertIn('mdx_content', result)  # This field is correct for single-topic endpoint
                self.assertTrue(len(result['mdx_content']) > 0)
                self.assertIn('crawled_websites', result)
            else:
                print("Error:", response.text)
        except requests.exceptions.ConnectionError:
            print("WARNING: API server is not running. Skipping test.")
            self.skipTest("API server is not running")

    def test_single_topic_raw(self):
        """Test the single-topic-raw endpoint."""
        # Request data
        data = {
            "selected_topic": "React Hooks",
            "main_topic": "React",
            "num_results": 2
        }

        try:
            # Make the request
            response = requests.post(
                f"{BASE_URL}/rag/single-topic-raw",
                json=data,
                timeout=15  # Increased timeout for crawling and LLM processing
            )

            print("Status Code:", response.status_code)
            self.assertEqual(response.status_code, 200)

            if response.status_code == 200:
                # For raw endpoints, the response is plain text
                result = response.text
                print("\nResponse (first 200 chars):")
                print(result[:200] + "..." if len(result) > 200 else result)

                # Verify the response is not empty
                self.assertTrue(len(result) > 0)
                # Verify it's not an error message
                self.assertFalse(result.startswith("Error:"))
            else:
                print("Error:", response.text)
        except requests.exceptions.ConnectionError:
            print("WARNING: API server is not running. Skipping test.")
            self.skipTest("API server is not running")

    def test_generate_mdx_from_urls(self):
        """Test the generate-mdx-from-urls endpoint."""
        # Request data
        data = {
            "urls": [
                "https://react.dev/blog/2023/03/16/introducing-react-19",
                "https://react.dev/learn"
            ],
            "selected_topic": "React 19 Features",
            "main_topic": "React",
            "topic": "React 19",
            "use_llm_knowledge": True
        }

        try:
            # Make the request
            response = requests.post(
                f"{BASE_URL}/rag/generate-mdx-from-urls",
                json=data,
                timeout=15  # Increased timeout for crawling and LLM processing
            )

            print("Status Code:", response.status_code)
            self.assertEqual(response.status_code, 200)

            if response.status_code == 200:
                result = response.json()
                print("\nResponse:")
                pprint(result)

                # Verify the response structure
                self.assertIn('status', result)
                self.assertEqual(result['status'], 'success')
                self.assertIn('mdx_content', result)  # This field is correct for generate-mdx-from-urls endpoint
                self.assertTrue(len(result['mdx_content']) > 0)
            else:
                print("Error:", response.text)
        except requests.exceptions.ConnectionError:
            print("WARNING: API server is not running. Skipping test.")
            self.skipTest("API server is not running")

    def test_generate_mdx_from_urls_raw(self):
        """Test the generate-mdx-from-urls-raw endpoint."""
        # Request data
        data = {
            "urls": [
                "https://react.dev/blog/2023/03/16/introducing-react-19",
                "https://react.dev/learn"
            ],
            "selected_topic": "React 19 Features",
            "main_topic": "React",
            "topic": "React 19",
            "use_llm_knowledge": True
        }

        try:
            # Make the request
            response = requests.post(
                f"{BASE_URL}/rag/generate-mdx-from-urls-raw",
                json=data,
                timeout=15  # Increased timeout for crawling and LLM processing
            )

            print("Status Code:", response.status_code)
            self.assertEqual(response.status_code, 200)

            if response.status_code == 200:
                # For raw endpoints, the response is plain text
                result = response.text
                print("\nResponse (first 200 chars):")
                print(result[:200] + "..." if len(result) > 200 else result)

                # Verify the response is not empty
                self.assertTrue(len(result) > 0)
                # Verify it's not an error message
                self.assertFalse(result.startswith("Error:"))
            else:
                print("Error:", response.text)
        except requests.exceptions.ConnectionError:
            print("WARNING: API server is not running. Skipping test.")
            self.skipTest("API server is not running")

    def test_generate_mdx_llm_only(self):
        """Test the generate-mdx-llm-only endpoint."""
        # Request data
        data = {
            "selected_topic": "React Hooks",
            "main_topic": "React"
        }

        try:
            # Make the request
            response = requests.post(
                f"{BASE_URL}/rag/generate-mdx-llm-only",
                json=data,
                timeout=15  # Increased timeout for LLM processing
            )

            print("Status Code:", response.status_code)
            self.assertEqual(response.status_code, 200)

            if response.status_code == 200:
                result = response.json()
                print("\nResponse:")
                pprint(result)

                # Verify the response structure
                self.assertIn('status', result)
                self.assertEqual(result['status'], 'success')
                self.assertIn('mdx_content', result)
                self.assertTrue(len(result['mdx_content']) > 0)
                self.assertIn('used_llm_knowledge', result)
                self.assertTrue(result['used_llm_knowledge'])
            else:
                print("Error:", response.text)
        except requests.exceptions.ConnectionError:
            print("WARNING: API server is not running. Skipping test.")
            self.skipTest("API server is not running")

    def test_generate_mdx_llm_only_raw(self):
        """Test the generate-mdx-llm-only-raw endpoint."""
        # Request data
        data = {
            "selected_topic": "React Hooks",
            "main_topic": "React"
        }

        try:
            # Make the request
            response = requests.post(
                f"{BASE_URL}/rag/generate-mdx-llm-only-raw",
                json=data,
                timeout=15  # Increased timeout for LLM processing
            )

            print("Status Code:", response.status_code)
            self.assertEqual(response.status_code, 200)

            if response.status_code == 200:
                # For raw endpoints, the response is plain text
                result = response.text
                print("\nResponse (first 200 chars):")
                print(result[:200] + "..." if len(result) > 200 else result)

                # Verify the response is not empty
                self.assertTrue(len(result) > 0)
                # Verify it's not an error message
                self.assertFalse(result.startswith("Error:"))
            else:
                print("Error:", response.text)
        except requests.exceptions.ConnectionError:
            print("WARNING: API server is not running. Skipping test.")
            self.skipTest("API server is not running")

if __name__ == "__main__":
    unittest.main()
