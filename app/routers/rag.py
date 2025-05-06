import fastapi
from fastapi import APIRouter
from app.models.schemas import (
    QueryRequest, RefineResponse,
    SearchRequest, SingleTopicRequest, LLMOnlyRequest,
    GenerateMDXFromURLsRequest,
    RefineWithSelectionRequest, RefineWithCrawlingRequest, RefineWithURLsRequest
)
from app.utils.response import success_response, error_response
from app.services.gemini_llm import generate_content, refine_content_with_gemini
from googlesearch import search
from app.services.crawler import (
    generate_single_topic_mdx_async, generate_mdx_document_async,
    generate_mdx_from_urls_async,
    find_relevant_websites, crawl_urls_async
)

router = APIRouter()


@router.post(
    "/search-topics",
)
async def search_topics(request: QueryRequest):
    print("hererere")
    if not request.query.strip():
        return error_response("Query cannot be empty", status_code=400)

    try:
        prompt = f"""
        Given the following query: "{request.query}", generate a structured list of main topics and their respective subtopics suitable for a lesson plan.

        Format the response as a JSON list of objects like:
        [
        {{
        "topic": "Main Topic",
        "subtopics": ["Subtopic 1", "Subtopic 2"]
        }},
        ...
        ]
        """
        hierarchy = generate_content(prompt)
        # print("Generated hierarchy:", hierarchy)
    except Exception as e:
        return error_response("LLM error", status_code=500, details=str(e))

    if not hierarchy:
        return error_response("No topics returned from LLM", status_code=404)

    return success_response({"topics": hierarchy})

# @router.post(
#     "/generate-mdx",
# )
# async def generate_mdx_endpoint(request: Request):
#     try:
#         data= await request.json()
#         print("Received data:", data)

#         data=data.get("topics", [])
#         print("Parsed data:", data)

#         # results: List[MDXTopicResponse] = []

#         all_urls = []
#         for item in data:
#             topic = item.get("topic")
#             subtopics = item.get("subtopics", [])

#             # 1) discover relevant URLs for the main topic
#             urls = search_urls(topic,2)
#             all_urls.extend(urls)

#         #     all_texts: List[str] = []
#         #     for url in urls:
#         #         # 2) scrape the page
#         #         raw = scrape_with_crawl4ai(url)
#         #         all_texts.append(raw)

#                 # 3) preprocess (clean / chunk)
#                 # cleaned = preprocess_text(raw)

#                 # 4) embed + retrieve similar passages
#                 # emb = get_embedding(cleaned)
#                 # matches = query_similar(emb, top_k=req.top_k)
#                 # for m in matches:
#                 #     all_texts.append(m["text"])

#             # 5) combine & generate MDX (pass subtopics along)
#             # combined = "\n\n".join(all_texts)
#             # mdx = generate_mdx(combined, topic=topic, subtopics=subtopics)

#             # results.append(MDXTopicResponse(topic=topic, mdx=mdx))

#         return {"results": all_urls}

#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to generate MDX: {e}"
#         )

@router.post("/generate-mdx")
async def generate_mdx_endpoint(query: SearchRequest):
    try:
        all_urls = set()

        for topic_data in query.topics:
            # The main topic is the topic field in each topic_data
            main_topic = topic_data.topic

            # Search for main topic - this is critical for proper context
            main_topic_query = f"{main_topic} official documentation OR guide"
            for url in search(main_topic_query, num_results=query.top_k):
                all_urls.add(url)

            # Search for each subtopic with the main topic for context
            for subtopic in topic_data.subtopics:
                # Create a more targeted search query that combines subtopic with main topic
                # The main_topic provides essential context for understanding the subtopic
                combined_query = f"{subtopic} in {main_topic} tutorial OR guide"
                for url in search(combined_query, num_results=query.top_k):
                    all_urls.add(url)

                # Also search for the relationship between the subtopic and main topic
                # This relationship is critical for accurate content generation
                relationship_query = f"{subtopic} {main_topic} relationship OR examples"
                for url in search(relationship_query, num_results=query.top_k):
                    all_urls.add(url)

                # Add a more specific search for how the subtopic fits within the main topic context
                context_query = f"{subtopic} in context of {main_topic} explanation OR importance"
                for url in search(context_query, num_results=query.top_k):
                    all_urls.add(url)

        # Convert topics to list of dictionaries (required by generate_mdx_from_links)
        topics_data = [topic.model_dump() for topic in query.topics]

        # Generate MDX from the collected URLs and topics using the async version directly
        mdx_code = await generate_mdx_document_async(list(all_urls), topics_data)

        return {
            "status": "success",
            "url_count": len(all_urls),
            "urls": list(all_urls),
            "mdx_code": mdx_code  # Return MDX code in the response
        }

    except Exception as e:
        return {
            "status": "error",
            "message": "Failed to generate URLs",
            "details": str(e)
        }




@router.post("/refine-with-selection", response_model=RefineResponse)
async def refine_with_selection(request: RefineWithSelectionRequest):
    """
    Refine MDX content with LLM using selected text and topic context.

    This endpoint:
    1. Takes MDX content, selected text, selected topic, main topic, and a question
    2. Uses the LLM to refine the content based on these inputs
    3. Returns the refined MDX content
    """
    try:
        # For backward compatibility, use topic if selected_topic is not provided
        topic = request.selected_topic if request.selected_topic else request.topic

        # Create a more detailed prompt that includes the selected text and topic
        prompt = f"""
        Here is MDX content about the selected topic "{topic}" which is part of the main topic "{request.main_topic}":

        {request.mdx}

        The user has selected this specific text:
        "{request.selected_text}"

        User asks: {request.question}

        Please return an updated MDX snippet that addresses the user's question or request,
        focusing specifically on improving or modifying the selected text.

        IMPORTANT: Make sure to emphasize how the selected topic "{topic}" relates to and fits within
        the context of the main topic "{request.main_topic}". This relationship is critical for providing
        accurate and contextually relevant information.

        Make sure to maintain proper MDX formatting in your response.
        """

        # Generate the refined content
        refined_content = generate_content(prompt)

        return success_response({"answer": refined_content})
    except Exception as e:
        return error_response("Failed to refine content with selection", status_code=500, details=str(e))

@router.post("/refine-with-crawling", response_model=RefineResponse)
async def refine_with_crawling(request: RefineWithCrawlingRequest):
    """
    Refine MDX content by first crawling relevant websites and then using the LLM.

    This endpoint:
    1. Takes MDX content, selected text, selected topic, main topic, a question, and num_results
    2. Finds and crawls relevant websites based on the topic and question
    3. Sends the crawled content to the LLM along with the original request
    4. Returns the refined MDX content
    """
    try:
        # For backward compatibility, use topic if selected_topic is not provided
        topic = request.selected_topic if request.selected_topic else request.topic

        # Find relevant websites based on the topic, main_topic, and question
        relevant_websites = find_relevant_websites(
            topic=topic,
            main_topic=request.main_topic,
            question=request.question,
            num_results=request.num_results
        )

        if not relevant_websites:
            return error_response("Could not find relevant websites to crawl", status_code=404)

        # Crawl the websites
        print(f"Crawling websites for refinement: {relevant_websites}")
        scraped_data = await crawl_urls_async(relevant_websites)

        # Combine the crawled content
        crawled_content = ""
        for url, content in scraped_data.items():
            if isinstance(content, str) and not content.startswith("Error scraping"):
                crawled_content += f"Content from {url}:\n{content}\n\n"

        # Create a prompt that includes the crawled content
        prompt = f"""
        Here is MDX content about the selected topic "{topic}" which is part of the main topic "{request.main_topic}":

        {request.mdx}

        The user has selected this specific text:
        "{request.selected_text}"

        User asks: {request.question}

        I've gathered additional information from relevant websites:

        {crawled_content}

        Using this additional information, please return an updated MDX snippet that addresses
        the user's question or request, focusing specifically on improving or modifying the selected text.

        IMPORTANT: Make sure to emphasize how the selected topic "{topic}" relates to and fits within
        the context of the main topic "{request.main_topic}". This relationship is critical for providing
        accurate and contextually relevant information. The main topic provides essential context that
        should guide your response.

        Make sure to maintain proper MDX formatting in your response.
        """

        # Generate the refined content
        refined_content = generate_content(prompt)

        return success_response({
            "answer": refined_content,
            "crawled_websites": relevant_websites
        })
    except Exception as e:
        return error_response("Failed to refine content with crawling", status_code=500, details=str(e))

@router.post("/refine-with-urls", response_model=RefineResponse)
async def refine_with_urls(request: RefineWithURLsRequest):
    """
    Refine MDX content by crawling specific URLs provided by the user.

    This endpoint:
    1. Takes MDX content, selected text, selected topic, main topic, a question, and a list of URLs
    2. Crawls the provided URLs
    3. Sends the crawled content to the LLM along with the original request
    4. Returns the refined MDX content
    """
    try:
        # For backward compatibility, use topic if selected_topic is not provided
        topic = request.selected_topic if request.selected_topic else request.topic

        if not request.urls:
            return error_response("No URLs provided for crawling", status_code=400)

        # Crawl the provided URLs
        print(f"Crawling user-provided URLs for refinement: {request.urls}")
        scraped_data = await crawl_urls_async(request.urls)

        # Combine the crawled content
        crawled_content = ""
        successful_urls = []
        for url, content in scraped_data.items():
            if isinstance(content, str) and not content.startswith("Error scraping"):
                crawled_content += f"Content from {url}:\n{content}\n\n"
                successful_urls.append(url)

        if not crawled_content.strip():
            return error_response("Could not extract valid content from any of the provided URLs", status_code=404)

        # Create a prompt that includes the crawled content
        prompt = f"""
        Here is MDX content about the selected topic "{topic}" which is part of the main topic "{request.main_topic}":

        {request.mdx}

        The user has selected this specific text:
        "{request.selected_text}"

        User asks: {request.question}

        I've gathered additional information from the URLs provided by the user:

        {crawled_content}

        Using this additional information, please return an updated MDX snippet that addresses
        the user's question or request, focusing specifically on improving or modifying the selected text.

        IMPORTANT: Make sure to emphasize how the selected topic "{topic}" relates to and fits within
        the context of the main topic "{request.main_topic}". This relationship is critical for providing
        accurate and contextually relevant information. The main topic provides essential context that
        should guide your response.

        Make sure to maintain proper MDX formatting in your response.
        """

        # Generate the refined content
        refined_content = generate_content(prompt)

        return success_response({
            "answer": refined_content,
            "crawled_websites": successful_urls
        })
    except Exception as e:
        return error_response("Failed to refine content with provided URLs", status_code=500, details=str(e))

@router.post("/refine-with-selection-raw", response_class=fastapi.responses.PlainTextResponse)
async def refine_with_selection_raw(request: RefineWithSelectionRequest):
    """
    Refine MDX content with LLM using selected text and topic context.
    Returns the raw MDX content as plain text instead of JSON.

    This endpoint:
    1. Takes MDX content, selected text, selected topic, main topic, and a question
    2. Uses the LLM to refine the content based on these inputs
    3. Returns the raw refined MDX content as plain text
    """
    try:
        # For backward compatibility, use topic if selected_topic is not provided
        topic = request.selected_topic if request.selected_topic else request.topic

        # Create a more detailed prompt that includes the selected text and topic
        prompt = f"""
        Here is MDX content about the selected topic "{topic}" which is part of the main topic "{request.main_topic}":

        {request.mdx}

        The user has selected this specific text:
        "{request.selected_text}"

        User asks: {request.question}

        Please return an updated MDX snippet that addresses the user's question or request,
        focusing specifically on improving or modifying the selected text.

        IMPORTANT: Make sure to emphasize how the selected topic "{topic}" relates to and fits within
        the context of the main topic "{request.main_topic}". This relationship is critical for providing
        accurate and contextually relevant information.

        Make sure to maintain proper MDX formatting in your response.
        """

        # Generate the refined content
        refined_content = generate_content(prompt)

        # Return the raw MDX content as plain text
        return refined_content
    except Exception as e:
        return f"Error: Failed to refine content with selection - {str(e)}"

@router.post("/refine-with-crawling-raw", response_class=fastapi.responses.PlainTextResponse)
async def refine_with_crawling_raw(request: RefineWithCrawlingRequest):
    """
    Refine MDX content by first crawling relevant websites and then using the LLM.
    Returns the raw MDX content as plain text instead of JSON.

    This endpoint:
    1. Takes MDX content, selected text, selected topic, main topic, a question, and num_results
    2. Finds and crawls relevant websites based on the topic and question
    3. Sends the crawled content to the LLM along with the original request
    4. Returns the raw refined MDX content as plain text
    """
    try:
        # For backward compatibility, use topic if selected_topic is not provided
        topic = request.selected_topic if request.selected_topic else request.topic

        # Find relevant websites based on the topic, main_topic, and question
        relevant_websites = find_relevant_websites(
            topic=topic,
            main_topic=request.main_topic,
            question=request.question,
            num_results=request.num_results
        )

        if not relevant_websites:
            return "Error: Could not find relevant websites to crawl"

        # Crawl the websites
        print(f"Crawling websites for refinement: {relevant_websites}")
        scraped_data = await crawl_urls_async(relevant_websites)

        # Combine the crawled content
        crawled_content = ""
        for url, content in scraped_data.items():
            if isinstance(content, str) and not content.startswith("Error scraping"):
                crawled_content += f"Content from {url}:\n{content}\n\n"

        # Create a prompt that includes the crawled content
        prompt = f"""
        Here is MDX content about the selected topic "{topic}" which is part of the main topic "{request.main_topic}":

        {request.mdx}

        The user has selected this specific text:
        "{request.selected_text}"

        User asks: {request.question}

        I've gathered additional information from relevant websites:

        {crawled_content}

        Using this additional information, please return an updated MDX snippet that addresses
        the user's question or request, focusing specifically on improving or modifying the selected text.

        IMPORTANT: Make sure to emphasize how the selected topic "{topic}" relates to and fits within
        the context of the main topic "{request.main_topic}". This relationship is critical for providing
        accurate and contextually relevant information. The main topic provides essential context that
        should guide your response.

        Make sure to maintain proper MDX formatting in your response.
        """

        # Generate the refined content
        refined_content = generate_content(prompt)

        # Return the raw MDX content as plain text
        return refined_content
    except Exception as e:
        return f"Error: Failed to refine content with crawling - {str(e)}"

@router.post("/refine-with-urls-raw", response_class=fastapi.responses.PlainTextResponse)
async def refine_with_urls_raw(request: RefineWithURLsRequest):
    """
    Refine MDX content by crawling specific URLs provided by the user.
    Returns the raw MDX content as plain text instead of JSON.

    This endpoint:
    1. Takes MDX content, selected text, selected topic, main topic, a question, and a list of URLs
    2. Crawls the provided URLs
    3. Sends the crawled content to the LLM along with the original request
    4. Returns the raw refined MDX content as plain text
    """
    try:
        # For backward compatibility, use topic if selected_topic is not provided
        topic = request.selected_topic if request.selected_topic else request.topic

        if not request.urls:
            return "Error: No URLs provided for crawling"

        # Crawl the provided URLs
        print(f"Crawling user-provided URLs for refinement: {request.urls}")
        scraped_data = await crawl_urls_async(request.urls)

        # Combine the crawled content
        crawled_content = ""
        for url, content in scraped_data.items():
            if isinstance(content, str) and not content.startswith("Error scraping"):
                crawled_content += f"Content from {url}:\n{content}\n\n"

        if not crawled_content.strip():
            return "Error: Could not extract valid content from any of the provided URLs"

        # Create a prompt that includes the crawled content
        prompt = f"""
        Here is MDX content about the selected topic "{topic}" which is part of the main topic "{request.main_topic}":

        {request.mdx}

        The user has selected this specific text:
        "{request.selected_text}"

        User asks: {request.question}

        I've gathered additional information from the URLs provided by the user:

        {crawled_content}

        Using this additional information, please return an updated MDX snippet that addresses
        the user's question or request, focusing specifically on improving or modifying the selected text.

        IMPORTANT: Make sure to emphasize how the selected topic "{topic}" relates to and fits within
        the context of the main topic "{request.main_topic}". This relationship is critical for providing
        accurate and contextually relevant information. The main topic provides essential context that
        should guide your response.

        Make sure to maintain proper MDX formatting in your response.
        """

        # Generate the refined content
        refined_content = generate_content(prompt)

        # Return the raw MDX content as plain text
        return refined_content
    except Exception as e:
        return f"Error: Failed to refine content with provided URLs - {str(e)}"

@router.post("/single-topic")
async def generate_single_topic(request: SingleTopicRequest):
    """
    Generate MDX content for a single topic.

    This endpoint:
    1. Takes a selected topic (subtopic) and main topic
    2. Checks if the LLM has up-to-date information
    3. If not, automatically finds and crawls relevant websites
    4. Also searches for additional relevant web content if needed
    5. Generates a comprehensive, properly formatted MDX document

    The response has no double newlines to ensure clean formatting.
    """
    try:
        # For backward compatibility, use topic if selected_topic is not provided
        topic = request.selected_topic if request.selected_topic else request.topic

        if not topic or not topic.strip():
            return error_response("Selected topic or topic cannot be empty", status_code=400)

        # Generate MDX for the single topic using the async version directly
        result = await generate_single_topic_mdx_async(
            topic=topic,
            main_topic=request.main_topic,
            num_results=request.num_results
        )

        # Check if there was an error
        if "error" in result:
            return {
                "status": "error",
                "message": "Failed to generate valid MDX content",
                "details": result["error"],
                "crawled_websites": result.get("crawled_websites", []),
                "used_llm_knowledge": result.get("has_current_info", False)
            }

        return {
            "status": "success",
            "selected_topic": request.selected_topic,
            "main_topic": request.main_topic,
            "mdx_content": result["mdx_content"],
            "crawled_websites": result.get("crawled_websites", []),
            "used_llm_knowledge": result.get("has_current_info", False)
        }

    except Exception as e:
        return {
            "status": "error",
            "message": "Failed to generate MDX for the topic",
            "details": str(e)
        }





@router.post("/single-topic-raw", response_class=fastapi.responses.PlainTextResponse)
async def generate_single_topic_raw(request: SingleTopicRequest):
    """
    Generate MDX content for a single topic and return it as raw text.

    This endpoint:
    1. Takes a selected topic (subtopic) and main topic
    2. Checks if the LLM has up-to-date information
    3. If not, automatically finds and crawls relevant websites
    4. Also searches for additional relevant web content if needed
    5. Generates a comprehensive, properly formatted MDX document
    6. Returns the raw MDX content as plain text
    """
    try:
        # For backward compatibility, use topic if selected_topic is not provided
        topic = request.selected_topic if request.selected_topic else request.topic

        if not topic or not topic.strip():
            return "Error: Selected topic or topic cannot be empty"

        # Generate MDX for the single topic using the async version directly
        result = await generate_single_topic_mdx_async(
            topic=topic,
            main_topic=request.main_topic,
            num_results=request.num_results
        )

        # Check if there was an error
        if "error" in result:
            return f"Error: {result['error']}"

        # Return the raw MDX content
        return result["mdx_content"]

    except Exception as e:
        return f"Error: Failed to generate MDX for the topic - {str(e)}"

@router.post("/generate-mdx-from-urls", response_class=fastapi.responses.JSONResponse)
async def generate_mdx_from_urls_endpoint(request: GenerateMDXFromURLsRequest):
    """
    Generate MDX content from multiple URLs using crawl4ai and LLM.

    This endpoint:
    1. Takes a list of URLs (1 to 5), selected topic (subtopic), main topic, and use_llm_knowledge flag
    2. Crawls all URLs using crawl4ai
    3. Combines the content and generates MDX using the LLM
    4. Returns the MDX content

    If crawling fails and use_llm_knowledge is True, it will use the LLM's existing knowledge to generate content.
    """
    try:
        # Validate URL count
        if len(request.urls) > 5:
            return {
                "status": "error",
                "message": "Too many URLs provided",
                "details": "Maximum 5 URLs are allowed"
            }

        # Generate MDX from the URLs using the new function
        mdx_content = await generate_mdx_from_urls_async(
            request.urls,
            request.selected_topic,
            request.main_topic,
            request.topic,
            request.use_llm_knowledge
        )

        # Check if there was an error
        if mdx_content.startswith("Error"):
            return {
                "status": "error",
                "message": "Failed to generate MDX from URLs",
                "details": mdx_content
            }

        return {
            "status": "success",
            "urls": request.urls,
            "selected_topic": request.selected_topic,
            "main_topic": request.main_topic,
            "mdx_content": mdx_content,
            "used_llm_knowledge": request.use_llm_knowledge
        }

    except Exception as e:
        return {
            "status": "error",
            "message": "Failed to generate MDX from URLs",
            "details": str(e)
        }

@router.post("/generate-mdx-llm-only")
async def generate_mdx_llm_only(request: LLMOnlyRequest):
    """
    Generate MDX content using only the LLM's knowledge (no web crawling).

    This endpoint:
    1. Takes a selected topic (subtopic) and main topic
    2. Uses the LLM's existing knowledge to generate content
    3. Returns the MDX content in a JSON response
    """
    try:
        if not request.selected_topic.strip():
            return error_response("Selected topic cannot be empty", status_code=400)

        if not request.main_topic.strip():
            return error_response("Main topic cannot be empty", status_code=400)

        # Generate MDX using Gemini
        import datetime
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')

        prompt = f"""
        You are a documentation writer specializing in MDX format. Create a comprehensive MDX document about the selected topic: {request.selected_topic}, which is part of the main topic: {request.main_topic}.

        Use your knowledge to create content about this topic. Do not make up information.

        IMPORTANT: DO NOT wrap your response in ```mdx code blocks. I need the raw MDX content directly.

        Your response MUST be valid MDX format starting with:
        ---
        title: "{request.selected_topic}"
        description: "Comprehensive guide about {request.selected_topic} in {request.main_topic}"
        date: "{current_date}"
        ---

        # {request.selected_topic}

        Then continue with well-structured content about the topic. Include:
        - Clear explanations
        - Examples where appropriate
        - Code snippets if relevant
        - Proper headings and subheadings
        - Lists and tables where they help organize information

        Make sure the content is comprehensive, accurate, and well-organized.
        """

        # Generate the MDX content
        from app.services.gemini_llm import generate_content
        from app.services.crawler import clean_markdown

        mdx_content = generate_content(prompt)
        mdx_content = clean_markdown(mdx_content)

        # Ensure the content has proper front matter
        if not mdx_content.startswith("---"):
            mdx_content = f"""---
title: "{request.selected_topic}"
description: "Comprehensive guide about {request.selected_topic} in {request.main_topic}"
date: "{current_date}"
---

# {request.selected_topic}

{mdx_content}
"""

        return {
            "status": "success",
            "selected_topic": request.selected_topic,
            "main_topic": request.main_topic,
            "mdx_content": mdx_content,
            "used_llm_knowledge": True
        }

    except Exception as e:
        return {
            "status": "error",
            "message": "Failed to generate MDX using LLM only",
            "details": str(e)
        }

@router.post("/generate-mdx-llm-only-raw", response_class=fastapi.responses.PlainTextResponse)
async def generate_mdx_llm_only_raw(request: LLMOnlyRequest):
    """
    Generate MDX content using only the LLM's knowledge (no web crawling) and return it as raw text.

    This endpoint:
    1. Takes a selected topic (subtopic) and main topic
    2. Uses the LLM's existing knowledge to generate content
    3. Returns the raw MDX content as plain text
    """
    try:
        if not request.selected_topic.strip():
            return "Error: Selected topic cannot be empty"

        if not request.main_topic.strip():
            return "Error: Main topic cannot be empty"

        # Generate MDX using Gemini
        import datetime
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')

        prompt = f"""
        You are a documentation writer specializing in MDX format. Create a comprehensive MDX document about the selected topic: {request.selected_topic}, which is part of the main topic: {request.main_topic}.

        Use your knowledge to create content about this topic. Do not make up information.

        IMPORTANT: DO NOT wrap your response in ```mdx code blocks. I need the raw MDX content directly.

        Your response MUST be valid MDX format starting with:
        ---
        title: "{request.selected_topic}"
        description: "Comprehensive guide about {request.selected_topic} in {request.main_topic}"
        date: "{current_date}"
        ---

        # {request.selected_topic}

        Then continue with well-structured content about the topic. Include:
        - Clear explanations
        - Examples where appropriate
        - Code snippets if relevant
        - Proper headings and subheadings
        - Lists and tables where they help organize information

        Make sure the content is comprehensive, accurate, and well-organized.
        """

        # Generate the MDX content
        from app.services.gemini_llm import generate_content
        from app.services.crawler import clean_markdown

        mdx_content = generate_content(prompt)
        mdx_content = clean_markdown(mdx_content)

        # Ensure the content has proper front matter
        if not mdx_content.startswith("---"):
            mdx_content = f"""---
title: "{request.selected_topic}"
description: "Comprehensive guide about {request.selected_topic} in {request.main_topic}"
date: "{current_date}"
---

# {request.selected_topic}

{mdx_content}
"""

        # Return the raw MDX content
        return mdx_content

    except Exception as e:
        return f"Error: Failed to generate MDX using LLM only - {str(e)}"

@router.post("/generate-mdx-from-urls-raw", response_class=fastapi.responses.PlainTextResponse)
async def generate_mdx_from_urls_raw_endpoint(request: GenerateMDXFromURLsRequest):
    """
    Generate MDX content from multiple URLs using crawl4ai and LLM.
    Returns the raw MDX content as plain text instead of JSON.

    This endpoint:
    1. Takes a list of URLs (1 to 5), selected topic (subtopic), main topic, and use_llm_knowledge flag
    2. Crawls all URLs using crawl4ai
    3. Combines the content and generates MDX using the LLM
    4. Returns the raw MDX content as plain text

    If crawling fails and use_llm_knowledge is True, it will use the LLM's existing knowledge to generate content.
    """
    try:
        # Validate URL count
        if len(request.urls) > 5:
            return "Error: Too many URLs provided. Maximum 5 URLs are allowed."

        # Generate MDX from the URLs using the new function
        mdx_content = await generate_mdx_from_urls_async(
            request.urls,
            request.selected_topic,
            request.main_topic,
            request.topic,
            request.use_llm_knowledge
        )

        # Return the raw MDX content as plain text
        return mdx_content

    except Exception as e:
        # Since we're returning plain text, we'll format the error as text
        return f"Error: Failed to generate MDX from URLs - {str(e)}"