#!/usr/bin/env python3
"""
Test script for the refine routes.
"""

import os
import sys
import unittest
import requests
import json
from pprint import pprint

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Base URL for the API
BASE_URL = "http://localhost:8000"

class TestRefineRoutes(unittest.TestCase):
    """Test cases for refine routes."""

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

    def test_refine_with_selection(self):
        """Test the refine-with-selection endpoint."""
        # Request data
        data = {
            "mdx": self.sample_mdx,
            "question": "Can you add more details about Python's popularity in data science?",
            "selected_text": "Python is a high-level, interpreted programming language known for its simplicity and readability.",
            "topic": "Python Programming"
        }

        try:
            # Make the request
            response = requests.post(
                f"{BASE_URL}/rag/refine-with-selection",
                json=data,
                timeout=2  # Short timeout to fail fast if server is not running
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
            else:
                print("Error:", response.text)
        except requests.exceptions.ConnectionError:
            print("WARNING: API server is not running. Skipping test.")
            self.skipTest("API server is not running")

    def test_refine_with_crawling(self):
        """Test the refine-with-crawling endpoint."""
        # Request data
        data = {
            "mdx": self.sample_mdx,
            "question": "Can you add more details about Python's popularity in data science?",
            "selected_text": "Python is a high-level, interpreted programming language known for its simplicity and readability.",
            "topic": "Python Programming",
            "num_results": 2
        }

        try:
            # Make the request
            response = requests.post(
                f"{BASE_URL}/rag/refine-with-crawling",
                json=data,
                timeout=2  # Short timeout to fail fast if server is not running
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
            else:
                print("Error:", response.text)
        except requests.exceptions.ConnectionError:
            print("WARNING: API server is not running. Skipping test.")
            self.skipTest("API server is not running")

    def test_refine_with_urls(self):
        """Test the refine-with-urls endpoint."""
        # Request data
        data = {
            "mdx": self.sample_mdx,
            "question": "Can you add more details about Python's popularity in data science?",
            "selected_text": "Python is a high-level, interpreted programming language known for its simplicity and readability.",
            "topic": "Python Programming",
            "urls": [
                "https://www.python.org/",
                "https://docs.python.org/3/tutorial/index.html"
            ]
        }

        try:
            # Make the request
            response = requests.post(
                f"{BASE_URL}/rag/refine-with-urls",
                json=data,
                timeout=2  # Short timeout to fail fast if server is not running
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
            else:
                print("Error:", response.text)
        except requests.exceptions.ConnectionError:
            print("WARNING: API server is not running. Skipping test.")
            self.skipTest("API server is not running")

if __name__ == "__main__":
    unittest.main()
