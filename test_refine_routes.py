#!/usr/bin/env python3
"""
Test script for the refine routes.
"""

import requests
import json
from pprint import pprint

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_refine_with_selection():
    """
    Test the refine-with-selection endpoint.
    """
    # Sample MDX content
    mdx_content = """---
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

    # Request data
    data = {
        "mdx": mdx_content,
        "question": "Can you add more details about Python's popularity in data science?",
        "selected_text": "Python is a high-level, interpreted programming language known for its simplicity and readability.",
        "topic": "Python Programming"
    }
    
    # Make the request
    response = requests.post(
        f"{BASE_URL}/rag/refine-with-selection",
        json=data
    )
    
    print("Status Code:", response.status_code)
    if response.status_code == 200:
        result = response.json()
        print("\nResponse:")
        pprint(result)
    else:
        print("Error:", response.text)

def test_refine_with_crawling():
    """
    Test the refine-with-crawling endpoint.
    """
    # Sample MDX content
    mdx_content = """---
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

    # Request data
    data = {
        "mdx": mdx_content,
        "question": "Can you add more details about Python's popularity in data science?",
        "selected_text": "Python is a high-level, interpreted programming language known for its simplicity and readability.",
        "topic": "Python Programming",
        "num_results": 2
    }
    
    # Make the request
    response = requests.post(
        f"{BASE_URL}/rag/refine-with-crawling",
        json=data
    )
    
    print("Status Code:", response.status_code)
    if response.status_code == 200:
        result = response.json()
        print("\nResponse:")
        pprint(result)
    else:
        print("Error:", response.text)

def test_refine_with_urls():
    """
    Test the refine-with-urls endpoint.
    """
    # Sample MDX content
    mdx_content = """---
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

    # Request data
    data = {
        "mdx": mdx_content,
        "question": "Can you add more details about Python's popularity in data science?",
        "selected_text": "Python is a high-level, interpreted programming language known for its simplicity and readability.",
        "topic": "Python Programming",
        "urls": [
            "https://www.python.org/",
            "https://docs.python.org/3/tutorial/index.html"
        ]
    }
    
    # Make the request
    response = requests.post(
        f"{BASE_URL}/rag/refine-with-urls",
        json=data
    )
    
    print("Status Code:", response.status_code)
    if response.status_code == 200:
        result = response.json()
        print("\nResponse:")
        pprint(result)
    else:
        print("Error:", response.text)

if __name__ == "__main__":
    print("=== Testing refine-with-selection endpoint ===")
    test_refine_with_selection()
    
    print("\n=== Testing refine-with-crawling endpoint ===")
    test_refine_with_crawling()
    
    print("\n=== Testing refine-with-urls endpoint ===")
    test_refine_with_urls()
