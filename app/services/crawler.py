import asyncio
import re
import os
from crawl4ai import AsyncWebCrawler, CacheMode
from app.services.gemini_llm import generate_content
from app.services.crawler_config import get_browser_config, get_crawler_config

# Disable Node.js debugger
os.environ["NODE_OPTIONS"] = "--no-warnings --no-deprecation"

async def scrape_with_crawl4ai(url) -> str:
    """
    Scrape a single URL using crawl4ai and return the markdown content.
    """
    browser_config = get_browser_config(headless=True, verbose=False)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        crawler_config = get_crawler_config()
        result = await crawler.arun(url, config=crawler_config)
        print(f"Scraped {url}: {result.markdown[:300]}...")  # Print first 300 chars
        return result.markdown

async def crawl_url_with_crawl4ai(url) -> str:
    """
    Scrape a single URL using crawl4ai and return the markdown content.
    """
    try:
        browser_config = get_browser_config(headless=True, verbose=False)
        async with AsyncWebCrawler(config=browser_config) as crawler:
            crawler_config = get_crawler_config(
                cache_mode=CacheMode.BYPASS,  # Ensure fresh content
                word_count_threshold=1  # Ensure we get all content
            )
            result = await crawler.arun(url, config=crawler_config)
            if result.success:
                return result.markdown
            else:
                return f"Error scraping {url}: {result.error_message}"
    except Exception as e:
        return f"Error scraping {url}: {e}"

async def crawl_urls_async(urls: list) -> dict:
    """
    Scrape multiple URLs asynchronously using crawl4ai and return their markdown content.
    """
    tasks = [crawl_url_with_crawl4ai(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return {url: result for url, result in zip(urls, results)}

def crawl_urls(urls: list) -> dict:
    """
    Scrape multiple URLs and return their text content in a dictionary keyed by URL.
    This is a synchronous wrapper around the async function.
    """
    return asyncio.run(crawl_urls_async(urls))

def clean_markdown(text):
    """
    Clean and format MDX content to ensure proper formatting.

    This function:
    1. Removes escaped newlines and quotes
    2. Removes nested code blocks (```mdx...```)
    3. Ensures only one front matter section
    4. Normalizes newlines for proper MDX formatting
    """
    # Remove any leading/trailing whitespace
    text = text.strip()

    # Remove escaped newlines and quotes
    text = text.replace('\\n', '\n').replace('\\"', '"')

    # Remove nested MDX code blocks
    if '```mdx' in text:
        # Extract content from within the mdx code block
        match = re.search(r'```mdx\n(.*?)\n```', text, re.DOTALL)
        if match:
            text = match.group(1)

    # Ensure only one front matter section
    front_matter_count = text.count('---')
    if front_matter_count > 2:
        # Find the second closing --- and keep everything after that
        parts = text.split('---', 2)
        if len(parts) >= 3:
            # Reconstruct with only one front matter section
            text = '---' + parts[1] + '---' + parts[2]

    # Normalize newlines for proper MDX formatting:
    # 1. Replace excessive newlines (3+) with double newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 2. Ensure paragraphs are separated by double newlines
    text = re.sub(r'(\w+[.!?])\n([A-Z])', r'\1\n\n\2', text)

    # 3. Ensure headings have proper spacing
    text = re.sub(r'\n(#{1,6} )', r'\n\n\1', text)

    # 4. Ensure proper spacing after headings
    text = re.sub(r'(#{1,6} .+)\n([^#\n])', r'\1\n\n\2', text)

    # 5. Ensure proper spacing for lists
    text = re.sub(r'\n(- |\* |[0-9]+\. )', r'\n\n\1', text)

    # 6. Ensure no literal \n characters in the text (they should be actual newlines)
    text = text.replace('\\n', '\n')

    # 7. Remove any extra newlines at the beginning of the front matter
    if text.startswith('\n---'):
        text = text.replace('\n---', '---', 1)

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

async def generate_mdx_document_async(urls: list, topics_data: list) -> str:
    """
    Crawl the given list of URLs using crawl4ai, extract content relevant to each subtopic in topics_data,
    and convert it to a well-formatted MDX string using the generate_content function.
    This is the async version of the function.
    """
    mdx_output = "# Lesson Plan\n\n"
    # Crawl all URLs at once using crawl4ai
    scraped_data = await crawl_urls_async(urls)
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
                if isinstance(content, str) and not content.startswith("Error scraping"):
                    try:
                        # Use Gemini LLM to extract relevant content for the subtopic
                        prompt = f"Extract content relevant to the subtopic '{sub}' from the following markdown:\n\n{content}"
                        print(f"Extracting content for subtopic '{sub}' from {url[:50]}...")
                        relevant_content = generate_content(prompt)
                        all_relevant_content += clean_markdown(relevant_content) + "\n"
                    except Exception as e:
                        print(f"Error extracting content for {url}: {e}")

            # If we found something, call generate_content; else note no content found
            if all_relevant_content.strip():
                try:
                    prompt = create_mdx_prompt(topic, sub, all_relevant_content)
                    print(f"Generating MDX for subtopic '{sub}'...")
                    generated_mdx = generate_content(prompt)
                    mdx_output += clean_markdown(generated_mdx) + "\n\n"
                except Exception as e:
                    mdx_output += f"*Error generating content for this subtopic: {e}.*\n\n"
            else:
                mdx_output += "*Content not found for this subtopic.*\n\n"

    return mdx_output

def generate_mdx_document(urls: list, topics_data: list) -> str:
    """
    Crawl the given list of URLs, extract content relevant to each subtopic in topics_data,
    and convert it to a well-formatted MDX string using the generate_content function.
    This is a synchronous wrapper around the async function.
    """
    return asyncio.run(generate_mdx_document_async(urls, topics_data))

def find_relevant_websites(topic: str, num_results: int = 2) -> list:
    """
    Find relevant websites for a given topic.

    Args:
        topic: The topic to find websites for
        num_results: Number of websites to find

    Returns:
        List of relevant website URLs
    """
    try:
        # Use Google search to find relevant websites
        from googlesearch import search
        websites = []

        # Search for official websites or documentation
        for url in search(f"{topic} official site OR documentation", num_results=num_results):
            websites.append(url)

        # Search for recent news or updates
        for url in search(f"{topic} latest news OR updates 2025", num_results=num_results):
            if url not in websites:  # Avoid duplicates
                websites.append(url)

        return websites
    except Exception as e:
        print(f"Error finding relevant websites: {e}")
        return []

async def generate_single_topic_mdx_async(topic: str, num_results: int = 5) -> dict:
    """
    Generate MDX content for a single topic, checking if the LLM has up-to-date information first.
    If not, find and crawl relevant websites for the latest information.
    This is the async version of the function.

    Args:
        topic: The topic to generate content for
        num_results: Number of search results to use

    Returns:
        Dictionary with MDX formatted content and metadata
    """
    # Disable debugger for this operation
    os.environ["NODE_OPTIONS"] = "--no-warnings --no-deprecation"
    # First, check if the LLM has up-to-date information on the topic
    currency_check_prompt = f"""
    Do you have up-to-date information about the topic: "{topic}"?

    Please respond with only "YES" if you have current information (from the last 6 months),
    or "NO" if your information might be outdated or incomplete.
    """

    try:
        currency_response = generate_content(currency_check_prompt).strip().upper()
        has_current_info = "YES" in currency_response
        print(f"LLM has current info on {topic}: {has_current_info}")
    except Exception as e:
        print(f"Error checking currency: {e}")
        has_current_info = False

    # If we need to crawl for additional information
    all_content = ""
    crawled_websites = []

    if not has_current_info:
        # Find relevant websites to crawl
        relevant_websites = find_relevant_websites(topic, num_results=2)
        crawled_websites = relevant_websites

        if relevant_websites:
            print(f"Crawling relevant websites for {topic}: {relevant_websites}")
            # Crawl the identified websites using crawl4ai
            scraped_data = await crawl_urls_async(relevant_websites)

            # Combine content from relevant websites
            for url, content in scraped_data.items():
                if isinstance(content, str) and not content.startswith("Error scraping"):
                    all_content += f"Content from {url}:\n{content}\n\n"

    # Also get some general search results if needed
    if not has_current_info or len(all_content.strip()) < 500:  # If we don't have much content
        urls = []
        from googlesearch import search
        for url in search(topic, num_results=num_results):
            if url in crawled_websites:
                continue  # Skip if we already crawled this URL
            urls.append(url)

        if urls:
            print(f"Crawling additional search results for {topic}")
            # Crawl the URLs using crawl4ai
            scraped_data = await crawl_urls_async(urls)

            # Add content from search results
            for url, content in scraped_data.items():
                if isinstance(content, str) and not content.startswith("Error scraping"):
                    all_content += f"Content from {url}:\n{content}\n\n"
                    crawled_websites.append(url)

    # Generate MDX using Gemini
    import datetime
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')

    prompt = f"""
    You are a documentation writer specializing in MDX format. Create a comprehensive MDX document about: {topic}.

    {"Use the following content as reference:" if all_content else "Use your knowledge to create content about this topic:"}
    {all_content}

    IMPORTANT: DO NOT wrap your response in ```mdx code blocks. I need the raw MDX content directly.

    Your response MUST be valid MDX format starting with:
    ---
    title: "{topic}"
    description: "Comprehensive guide about {topic}"
    date: "{current_date}"
    ---

    Then include a main heading with the topic name, followed by well-structured content with:
    - Proper heading hierarchy (##, ###, etc.)
    - Paragraphs separated by double newlines (blank line between paragraphs)
    - Lists using - or * for unordered lists and 1. 2. etc. for ordered lists
    - Code blocks using triple backticks with language specification if applicable
    - A summary or conclusion section at the end

    CRITICAL FORMATTING REQUIREMENTS:
    - DO NOT include ```mdx and ``` around your content
    - DO NOT escape quotes or newlines (no \" or \\n)
    - Use proper MDX formatting with double newlines between paragraphs and sections
    - Make sure the MDX is properly formatted and would render correctly in a React/Next.js application
    - Include appropriate MDX components like <Callout> or <Tabs> if they would enhance the content
    - Ensure headings have a blank line before them
    - Ensure lists have a blank line before them
    """

    try:
        # Generate the MDX content
        mdx_content = generate_content(prompt)

        # Clean and format the content
        mdx_content = clean_markdown(mdx_content)

        # Ensure the content has proper front matter
        if not mdx_content.startswith("---"):
            mdx_content = f"""---
title: "{topic}"
description: "Comprehensive guide about {topic}"
date: "{current_date}"
---

{mdx_content}"""

        # Add a newline after the front matter if needed
        if "---\n---" in mdx_content:
            mdx_content = mdx_content.replace("---\n---", "---\n\n---")

        # Ensure there's a newline after the front matter section
        if "---\n#" in mdx_content:
            mdx_content = mdx_content.replace("---\n#", "---\n\n#")

        # Ensure there's a double newline after the front matter closing
        mdx_content = re.sub(r'---\n([^-\n])', r'---\n\n\1', mdx_content)

        # Return both the MDX content and the list of crawled websites
        return {
            "mdx_content": mdx_content,
            "crawled_websites": crawled_websites,
            "has_current_info": has_current_info
        }
    except Exception as e:
        return {
            "error": f"Error generating MDX content: {e}",
            "crawled_websites": crawled_websites,
            "has_current_info": has_current_info
        }

def generate_single_topic_mdx(topic: str, num_results: int = 5) -> dict:
    """
    Generate MDX content for a single topic, checking if the LLM has up-to-date information first.
    If not, find and crawl relevant websites for the latest information.
    This is a synchronous wrapper around the async function.

    Args:
        topic: The topic to generate content for
        num_results: Number of search results to use

    Returns:
        Dictionary with MDX formatted content and metadata
    """
    return asyncio.run(generate_single_topic_mdx_async(topic, num_results))

async def direct_crawl_to_llm_async(url: str, query: str) -> str:
    """
    Direct pipeline from crawl4ai to LLM without BeautifulSoup processing.

    Args:
        url: The URL to crawl
        query: The query or instruction for the LLM

    Returns:
        The LLM-generated content
    """
    try:
        # Configure the crawler with debugger disabled
        browser_config = get_browser_config(headless=True, verbose=False)
        async with AsyncWebCrawler(config=browser_config) as crawler:
            crawler_config = get_crawler_config(
                cache_mode=CacheMode.BYPASS,  # Ensure fresh content
                word_count_threshold=1  # Ensure we get all content
            )

            # Crawl the URL
            print(f"Crawling {url}...")
            result = await crawler.arun(url, config=crawler_config)

            if not result.success:
                return f"Error crawling {url}: {result.error_message}"

            # Get the markdown content
            markdown_content = result.markdown

            # Send directly to LLM
            print(f"Sending content to LLM with query: {query}")
            prompt = f"""
            Based on the following content from {url}:

            {markdown_content}

            {query}
            """

            # Generate content with LLM
            llm_response = generate_content(prompt)
            return llm_response

    except Exception as e:
        return f"Error in direct crawl to LLM pipeline: {e}"

def direct_crawl_to_llm(url: str, query: str) -> str:
    """
    Direct pipeline from crawl4ai to LLM without BeautifulSoup processing.
    This is a synchronous wrapper around the async function.

    Args:
        url: The URL to crawl
        query: The query or instruction for the LLM

    Returns:
        The LLM-generated content
    """
    return asyncio.run(direct_crawl_to_llm_async(url, query))

async def direct_multi_crawl_to_llm_async(urls: list, query: str) -> str:
    """
    Direct pipeline from crawl4ai to LLM for multiple URLs without BeautifulSoup processing.

    Args:
        urls: List of URLs to crawl
        query: The query or instruction for the LLM

    Returns:
        The LLM-generated content
    """
    try:
        # Disable debugger for this operation
        os.environ["NODE_OPTIONS"] = "--no-warnings --no-deprecation"

        # Crawl all URLs
        print(f"Crawling {len(urls)} URLs...")
        scraped_data = await crawl_urls_async(urls)

        # Combine all content
        all_content = ""
        for url, content in scraped_data.items():
            if isinstance(content, str) and not content.startswith("Error scraping"):
                all_content += f"Content from {url}:\n{content}\n\n"

        # Send directly to LLM
        print(f"Sending content from {len(urls)} URLs to LLM with query: {query}")
        prompt = f"""
        Based on the following content from multiple sources:

        {all_content}

        {query}
        """

        # Generate content with LLM
        llm_response = generate_content(prompt)
        return llm_response

    except Exception as e:
        return f"Error in direct multi-crawl to LLM pipeline: {e}"

def direct_multi_crawl_to_llm(urls: list, query: str) -> str:
    """
    Direct pipeline from crawl4ai to LLM for multiple URLs without BeautifulSoup processing.
    This is a synchronous wrapper around the async function.

    Args:
        urls: List of URLs to crawl
        query: The query or instruction for the LLM

    Returns:
        The LLM-generated content
    """
    return asyncio.run(direct_multi_crawl_to_llm_async(urls, query))

async def generate_mdx_from_url_async(url: str, topic: str, use_llm_knowledge: bool = True) -> str:
    """
    Generate MDX content directly from a URL using crawl4ai and LLM.
    Uses the same approach as generate_single_topic_mdx_async but for a specific URL.

    Args:
        url: The URL to crawl
        topic: The topic for the MDX content
        use_llm_knowledge: Whether to use the LLM's existing knowledge if crawling fails

    Returns:
        The MDX content
    """
    # Disable debugger for this operation
    os.environ["NODE_OPTIONS"] = "--no-warnings --no-deprecation"

    try:
        # Crawl the URL directly using the crawl_url_with_crawl4ai function
        print(f"Crawling {url}...")
        content = await crawl_url_with_crawl4ai(url)

        # Check if crawling failed
        crawling_failed = content.startswith("Error scraping")

        # If crawling failed and we're not using LLM knowledge, return error
        if crawling_failed and not use_llm_knowledge:
            return f"Error crawling {url}: {content}"

        # Generate MDX using Gemini
        import datetime
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')

        # Adjust prompt based on whether we have content or need to use LLM knowledge
        if crawling_failed:
            print(f"Crawling failed for {url}, using LLM knowledge instead")
            reference_text = f"Use your knowledge to create content about this topic: {topic}"
        else:
            reference_text = f"Use the following content as reference:\n{content}"

        prompt = f"""
        You are a documentation writer specializing in MDX format. Create a comprehensive MDX document about: {topic}.

        {reference_text}

        IMPORTANT: DO NOT wrap your response in ```mdx code blocks. I need the raw MDX content directly.

        Your response MUST be valid MDX format starting with:
        ---
        title: "{topic}"
        description: "Comprehensive guide about {topic}"
        date: "{current_date}"
        ---

        Then include a main heading with the topic name, followed by well-structured content with:
        - Proper heading hierarchy (##, ###, etc.)
        - Paragraphs separated by double newlines (blank line between paragraphs)
        - Lists using - or * for unordered lists and 1. 2. etc. for ordered lists
        - Code blocks using triple backticks with language specification if applicable
        - A summary or conclusion section at the end

        CRITICAL FORMATTING REQUIREMENTS:
        - DO NOT include ```mdx and ``` around your content
        - DO NOT escape quotes or newlines (no \" or \\n)
        - Use proper MDX formatting with double newlines between paragraphs and sections
        - Make sure the MDX is properly formatted and would render correctly in a React/Next.js application
        - Include appropriate MDX components like <Callout> or <Tabs> if they would enhance the content
        - Ensure headings have a blank line before them
        - Ensure lists have a blank line before them
        """

        # Generate content with LLM
        mdx_content = generate_content(prompt)

        # Clean and format the content
        mdx_content = clean_markdown(mdx_content)

        # Ensure the content has proper front matter
        if not mdx_content.startswith("---"):
            mdx_content = f"""---
title: "{topic}"
description: "Comprehensive guide about {topic}"
date: "{current_date}"
---

{mdx_content}"""

        # Add a newline after the front matter if needed
        if "---\n---" in mdx_content:
            mdx_content = mdx_content.replace("---\n---", "---\n\n---")

        # Ensure there's a newline after the front matter section
        if "---\n#" in mdx_content:
            mdx_content = mdx_content.replace("---\n#", "---\n\n#")

        # Ensure there's a double newline after the front matter closing
        mdx_content = re.sub(r'---\n([^-\n])', r'---\n\n\1', mdx_content)

        return mdx_content

    except Exception as e:
        if use_llm_knowledge:
            # If an exception occurred but we're allowed to use LLM knowledge, try to generate content without crawling
            try:
                print(f"Error crawling {url}, falling back to LLM knowledge")
                import datetime
                current_date = datetime.datetime.now().strftime('%Y-%m-%d')

                prompt = f"""
                You are a documentation writer specializing in MDX format. Create a comprehensive MDX document about: {topic}.

                Use your knowledge to create content about this topic.

                IMPORTANT: DO NOT wrap your response in ```mdx code blocks. I need the raw MDX content directly.

                Your response MUST be valid MDX format starting with:
                ---
                title: "{topic}"
                description: "Comprehensive guide about {topic}"
                date: "{current_date}"
                ---

                Then include a main heading with the topic name, followed by well-structured content with:
                - Proper heading hierarchy (##, ###, etc.)
                - Paragraphs separated by double newlines (blank line between paragraphs)
                - Lists using - or * for unordered lists and 1. 2. etc. for ordered lists
                - Code blocks using triple backticks with language specification if applicable
                - A summary or conclusion section at the end

                CRITICAL FORMATTING REQUIREMENTS:
                - DO NOT include ```mdx and ``` around your content
                - DO NOT escape quotes or newlines (no \" or \\n)
                - Use proper MDX formatting with double newlines between paragraphs and sections
                - Make sure the MDX is properly formatted and would render correctly in a React/Next.js application
                - Include appropriate MDX components like <Callout> or <Tabs> if they would enhance the content
                - Ensure headings have a blank line before them
                - Ensure lists have a blank line before them
                """

                # Generate content with LLM
                mdx_content = generate_content(prompt)

                # Clean and format the content
                mdx_content = clean_markdown(mdx_content)

                # Ensure the content has proper front matter
                if not mdx_content.startswith("---"):
                    mdx_content = f"""---
title: "{topic}"
description: "Comprehensive guide about {topic}"
date: "{current_date}"
---

{mdx_content}"""

                # Add a newline after the front matter if needed
                if "---\n---" in mdx_content:
                    mdx_content = mdx_content.replace("---\n---", "---\n\n---")

                # Ensure there's a newline after the front matter section
                if "---\n#" in mdx_content:
                    mdx_content = mdx_content.replace("---\n#", "---\n\n#")

                # Ensure there's a double newline after the front matter closing
                mdx_content = re.sub(r'---\n([^-\n])', r'---\n\n\1', mdx_content)

                return mdx_content
            except Exception as inner_e:
                return f"Error generating MDX from URL: {e}. Fallback also failed: {inner_e}"
        else:
            return f"Error generating MDX from URL: {e}"

def generate_mdx_from_url(url: str, topic: str, use_llm_knowledge: bool = True) -> str:
    """
    Generate MDX content directly from a URL using crawl4ai and LLM.
    This is a synchronous wrapper around the async function.

    Args:
        url: The URL to crawl
        topic: The topic for the MDX content
        use_llm_knowledge: Whether to use the LLM's existing knowledge if crawling fails

    Returns:
        The MDX content
    """
    return asyncio.run(generate_mdx_from_url_async(url, topic, use_llm_knowledge))

async def generate_mdx_from_urls_async(urls: list, topic: str, use_llm_knowledge: bool = True) -> str:
    """
    Generate MDX content from multiple URLs using crawl4ai and LLM.
    Similar to generate_single_topic_mdx_async but for specific URLs.

    Args:
        urls: List of URLs to crawl
        topic: The topic for the MDX content
        use_llm_knowledge: Whether to use the LLM's existing knowledge if crawling fails

    Returns:
        The MDX content
    """
    # Disable debugger for this operation
    os.environ["NODE_OPTIONS"] = "--no-warnings --no-deprecation"

    try:
        # Crawl all URLs
        print(f"Crawling {len(urls)} URLs...")
        scraped_data = await crawl_urls_async(urls)

        # Combine all content
        all_content = ""
        for url, content in scraped_data.items():
            if isinstance(content, str) and not content.startswith("Error scraping"):
                all_content += f"Content from {url}:\n{content}\n\n"

        # Check if we got any valid content
        if not all_content.strip():
            if not use_llm_knowledge:
                return f"Error: Could not extract valid content from any of the provided URLs"
            else:
                print(f"No valid content extracted from URLs, using LLM knowledge instead")
                # Continue with LLM knowledge

        # Generate MDX using Gemini
        import datetime
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')

        # Adjust prompt based on whether we have content or need to use LLM knowledge
        if not all_content.strip():
            reference_text = f"Use your knowledge to create content about this topic: {topic}"
        else:
            reference_text = f"Use the following content as reference:\n{all_content}"

        prompt = f"""
        You are a documentation writer specializing in MDX format. Create a comprehensive MDX document about: {topic}.

        {reference_text}

        IMPORTANT: DO NOT wrap your response in ```mdx code blocks. I need the raw MDX content directly.

        Your response MUST be valid MDX format starting with:
        ---
        title: "{topic}"
        description: "Comprehensive guide about {topic}"
        date: "{current_date}"
        ---

        Then include a main heading with the topic name, followed by well-structured content with:
        - Proper heading hierarchy (##, ###, etc.)
        - Paragraphs separated by double newlines (blank line between paragraphs)
        - Lists using - or * for unordered lists and 1. 2. etc. for ordered lists
        - Code blocks using triple backticks with language specification if applicable
        - A summary or conclusion section at the end

        CRITICAL FORMATTING REQUIREMENTS:
        - DO NOT include ```mdx and ``` around your content
        - DO NOT escape quotes or newlines (no \" or \\n)
        - Use proper MDX formatting with double newlines between paragraphs and sections
        - Make sure the MDX is properly formatted and would render correctly in a React/Next.js application
        - Include appropriate MDX components like <Callout> or <Tabs> if they would enhance the content
        - Ensure headings have a blank line before them
        - Ensure lists have a blank line before them
        """

        # Generate content with LLM
        mdx_content = generate_content(prompt)

        # Clean and format the content
        mdx_content = clean_markdown(mdx_content)

        # Ensure the content has proper front matter
        if not mdx_content.startswith("---"):
            mdx_content = f"""---
title: "{topic}"
description: "Comprehensive guide about {topic}"
date: "{current_date}"
---

{mdx_content}"""

        # Add a newline after the front matter if needed
        if "---\n---" in mdx_content:
            mdx_content = mdx_content.replace("---\n---", "---\n\n---")

        # Ensure there's a newline after the front matter section
        if "---\n#" in mdx_content:
            mdx_content = mdx_content.replace("---\n#", "---\n\n#")

        # Ensure there's a double newline after the front matter closing
        mdx_content = re.sub(r'---\n([^-\n])', r'---\n\n\1', mdx_content)

        return mdx_content

    except Exception as e:
        if use_llm_knowledge:
            # If an exception occurred but we're allowed to use LLM knowledge, try to generate content without crawling
            try:
                print(f"Error crawling URLs, falling back to LLM knowledge")
                import datetime
                current_date = datetime.datetime.now().strftime('%Y-%m-%d')

                prompt = f"""
                You are a documentation writer specializing in MDX format. Create a comprehensive MDX document about: {topic}.

                Use your knowledge to create content about this topic.

                IMPORTANT: DO NOT wrap your response in ```mdx code blocks. I need the raw MDX content directly.

                Your response MUST be valid MDX format starting with:
                ---
                title: "{topic}"
                description: "Comprehensive guide about {topic}"
                date: "{current_date}"
                ---

                Then include a main heading with the topic name, followed by well-structured content with:
                - Proper heading hierarchy (##, ###, etc.)
                - Paragraphs separated by double newlines (blank line between paragraphs)
                - Lists using - or * for unordered lists and 1. 2. etc. for ordered lists
                - Code blocks using triple backticks with language specification if applicable
                - A summary or conclusion section at the end

                CRITICAL FORMATTING REQUIREMENTS:
                - DO NOT include ```mdx and ``` around your content
                - DO NOT escape quotes or newlines (no \" or \\n)
                - Use proper MDX formatting with double newlines between paragraphs and sections
                - Make sure the MDX is properly formatted and would render correctly in a React/Next.js application
                - Include appropriate MDX components like <Callout> or <Tabs> if they would enhance the content
                - Ensure headings have a blank line before them
                - Ensure lists have a blank line before them
                """

                # Generate content with LLM
                mdx_content = generate_content(prompt)

                # Clean and format the content
                mdx_content = clean_markdown(mdx_content)

                # Ensure the content has proper front matter
                if not mdx_content.startswith("---"):
                    mdx_content = f"""---
title: "{topic}"
description: "Comprehensive guide about {topic}"
date: "{current_date}"
---

{mdx_content}"""

                # Add a newline after the front matter if needed
                if "---\n---" in mdx_content:
                    mdx_content = mdx_content.replace("---\n---", "---\n\n---")

                # Ensure there's a newline after the front matter section
                if "---\n#" in mdx_content:
                    mdx_content = mdx_content.replace("---\n#", "---\n\n#")

                # Ensure there's a double newline after the front matter closing
                mdx_content = re.sub(r'---\n([^-\n])', r'---\n\n\1', mdx_content)

                return mdx_content
            except Exception as inner_e:
                return f"Error generating MDX from URLs: {e}. Fallback also failed: {inner_e}"
        else:
            return f"Error generating MDX from URLs: {e}"

def generate_mdx_from_urls(urls: list, topic: str, use_llm_knowledge: bool = True) -> str:
    """
    Generate MDX content from multiple URLs using crawl4ai and LLM.
    This is a synchronous wrapper around the async function.

    Args:
        urls: List of URLs to crawl
        topic: The topic for the MDX content
        use_llm_knowledge: Whether to use the LLM's existing knowledge if crawling fails

    Returns:
        The MDX content
    """
    return asyncio.run(generate_mdx_from_urls_async(urls, topic, use_llm_knowledge))
