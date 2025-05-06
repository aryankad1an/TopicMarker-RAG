import fastapi
from fastapi import APIRouter
from app.models.schemas import (
    QueryRequest, RefineRequest, RefineResponse,
    SearchRequest, SingleTopicRequest,
    GenerateMDXFromURLRequest, GenerateMDXFromURLsRequest,
    RefineWithSelectionRequest, RefineWithCrawlingRequest, RefineWithURLsRequest
)
from app.utils.response import success_response, error_response
from app.services.gemini_llm import generate_content, refine_content_with_gemini
from googlesearch import search
from app.services.crawler import (
    generate_single_topic_mdx_async, generate_mdx_document_async,
    generate_mdx_from_url_async, generate_mdx_from_urls_async,
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
            # Search main topic
            for url in search(topic_data.topic, num_results=query.top_k):
                all_urls.add(url)

            # Search subtopics
            for subtopic in topic_data.subtopics:
                for url in search(subtopic, num_results=query.top_k):
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


@router.post("/refine", response_model=RefineResponse)
async def refine(request: RefineRequest):
    try:
        # Use the Gemini-based refine function instead of the transformers-based one
        ans = refine_content_with_gemini(request.mdx, request.question)
        return success_response({"answer": ans})
    except Exception as e:
        return error_response("Failed to refine content", status_code=500, details=str(e))

@router.post("/refine-with-selection", response_model=RefineResponse)
async def refine_with_selection(request: RefineWithSelectionRequest):
    """
    Refine MDX content with LLM using selected text and topic context.

    This endpoint:
    1. Takes MDX content, a question, selected text, and topic name
    2. Uses the LLM to refine the content based on these inputs
    3. Returns the refined MDX content
    """
    try:
        # Create a more detailed prompt that includes the selected text and topic
        prompt = f"""
        Here is MDX content about the topic "{request.topic}":

        {request.mdx}

        The user has selected this specific text:
        "{request.selected_text}"

        User asks: {request.question}

        Please return an updated MDX snippet that addresses the user's question or request,
        focusing specifically on improving or modifying the selected text.
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
    1. Takes MDX content, a question, selected text, and topic name
    2. Finds and crawls 2 relevant websites based on the topic and question
    3. Sends the crawled content to the LLM along with the original request
    4. Returns the refined MDX content
    """
    try:
        # Find relevant websites based on the topic and question
        search_query = f"{request.topic} {request.question}"
        relevant_websites = find_relevant_websites(search_query, num_results=request.num_results)

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
        Here is MDX content about the topic "{request.topic}":

        {request.mdx}

        The user has selected this specific text:
        "{request.selected_text}"

        User asks: {request.question}

        I've gathered additional information from relevant websites:

        {crawled_content}

        Using this additional information, please return an updated MDX snippet that addresses
        the user's question or request, focusing specifically on improving or modifying the selected text.
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
    1. Takes MDX content, a question, selected text, topic name, and a list of URLs
    2. Crawls the provided URLs
    3. Sends the crawled content to the LLM along with the original request
    4. Returns the refined MDX content
    """
    try:
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
        Here is MDX content about the topic "{request.topic}":

        {request.mdx}

        The user has selected this specific text:
        "{request.selected_text}"

        User asks: {request.question}

        I've gathered additional information from the URLs provided by the user:

        {crawled_content}

        Using this additional information, please return an updated MDX snippet that addresses
        the user's question or request, focusing specifically on improving or modifying the selected text.
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
    1. Takes MDX content, a question, selected text, and topic name
    2. Uses the LLM to refine the content based on these inputs
    3. Returns the raw refined MDX content as plain text
    """
    try:
        # Create a more detailed prompt that includes the selected text and topic
        prompt = f"""
        Here is MDX content about the topic "{request.topic}":

        {request.mdx}

        The user has selected this specific text:
        "{request.selected_text}"

        User asks: {request.question}

        Please return an updated MDX snippet that addresses the user's question or request,
        focusing specifically on improving or modifying the selected text.
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
    1. Takes MDX content, a question, selected text, and topic name
    2. Finds and crawls 2 relevant websites based on the topic and question
    3. Sends the crawled content to the LLM along with the original request
    4. Returns the raw refined MDX content as plain text
    """
    try:
        # Find relevant websites based on the topic and question
        search_query = f"{request.topic} {request.question}"
        relevant_websites = find_relevant_websites(search_query, num_results=request.num_results)

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
        Here is MDX content about the topic "{request.topic}":

        {request.mdx}

        The user has selected this specific text:
        "{request.selected_text}"

        User asks: {request.question}

        I've gathered additional information from relevant websites:

        {crawled_content}

        Using this additional information, please return an updated MDX snippet that addresses
        the user's question or request, focusing specifically on improving or modifying the selected text.
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
    1. Takes MDX content, a question, selected text, topic name, and a list of URLs
    2. Crawls the provided URLs
    3. Sends the crawled content to the LLM along with the original request
    4. Returns the raw refined MDX content as plain text
    """
    try:
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
        Here is MDX content about the topic "{request.topic}":

        {request.mdx}

        The user has selected this specific text:
        "{request.selected_text}"

        User asks: {request.question}

        I've gathered additional information from the URLs provided by the user:

        {crawled_content}

        Using this additional information, please return an updated MDX snippet that addresses
        the user's question or request, focusing specifically on improving or modifying the selected text.
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
    1. Takes a single topic name
    2. Checks if the LLM has up-to-date information
    3. If not, automatically finds and crawls relevant websites
    4. Also searches for additional relevant web content if needed
    5. Generates a comprehensive, properly formatted MDX document

    The response has no double newlines to ensure clean formatting.
    """
    try:
        if not request.topic.strip():
            return error_response("Topic cannot be empty", status_code=400)

        # Generate MDX for the single topic using the async version directly
        result = await generate_single_topic_mdx_async(
            topic=request.topic,
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
            "topic": request.topic,
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



@router.post("/generate-mdx-from-url")
async def generate_mdx_from_url_endpoint(request: GenerateMDXFromURLRequest):
    """
    Generate MDX content directly from a URL using crawl4ai and LLM.

    This endpoint:
    1. Takes a URL and a topic
    2. Crawls the URL using crawl4ai
    3. Generates MDX content using the LLM
    4. Returns the MDX content

    If crawling fails and use_llm_knowledge is True, it will use the LLM's existing knowledge to generate content.
    """
    try:
        # Generate MDX from the URL using the updated function
        mdx_content = await generate_mdx_from_url_async(request.url, request.topic, request.use_llm_knowledge)

        # Check if there was an error
        if mdx_content.startswith("Error"):
            return {
                "status": "error",
                "message": "Failed to generate MDX from URL",
                "details": mdx_content
            }

        return {
            "status": "success",
            "url": request.url,
            "topic": request.topic,
            "mdx_content": mdx_content,
            "used_llm_knowledge": request.use_llm_knowledge
        }

    except Exception as e:
        return {
            "status": "error",
            "message": "Failed to generate MDX from URL",
            "details": str(e)
        }

@router.post("/generate-mdx-from-url-raw", response_class=fastapi.responses.PlainTextResponse)
async def generate_mdx_from_url_raw_endpoint(request: GenerateMDXFromURLRequest):
    """
    Generate MDX content directly from a URL using crawl4ai and LLM.
    Returns the raw MDX content as plain text instead of JSON.

    This endpoint:
    1. Takes a URL and a topic
    2. Crawls the URL using crawl4ai
    3. Generates MDX content using the LLM
    4. Returns the raw MDX content as plain text

    If crawling fails and use_llm_knowledge is True, it will use the LLM's existing knowledge to generate content.
    """
    try:
        # Generate MDX from the URL using the updated function
        mdx_content = await generate_mdx_from_url_async(request.url, request.topic, request.use_llm_knowledge)

        # Return the raw MDX content as plain text
        return mdx_content

    except Exception as e:
        # Since we're returning plain text, we'll format the error as text
        return f"Error: Failed to generate MDX from URL - {str(e)}"

@router.post("/single-topic-raw", response_class=fastapi.responses.PlainTextResponse)
async def generate_single_topic_raw(request: SingleTopicRequest):
    """
    Generate MDX content for a single topic and return it as raw text.

    This endpoint:
    1. Takes a single topic name
    2. Checks if the LLM has up-to-date information
    3. If not, automatically finds and crawls relevant websites
    4. Also searches for additional relevant web content if needed
    5. Generates a comprehensive, properly formatted MDX document
    6. Returns the raw MDX content as plain text
    """
    try:
        if not request.topic.strip():
            return "Error: Topic cannot be empty"

        # Generate MDX for the single topic using the async version directly
        result = await generate_single_topic_mdx_async(
            topic=request.topic,
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
    1. Takes a list of URLs and a topic
    2. Crawls all URLs using crawl4ai
    3. Combines the content and generates MDX using the LLM
    4. Returns the MDX content

    If crawling fails and use_llm_knowledge is True, it will use the LLM's existing knowledge to generate content.
    """
    try:
        # Generate MDX from the URLs using the new function
        mdx_content = await generate_mdx_from_urls_async(request.urls, request.topic, request.use_llm_knowledge)

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
            "topic": request.topic,
            "mdx_content": mdx_content,
            "used_llm_knowledge": request.use_llm_knowledge
        }

    except Exception as e:
        return {
            "status": "error",
            "message": "Failed to generate MDX from URLs",
            "details": str(e)
        }

@router.post("/generate-mdx-from-urls-raw", response_class=fastapi.responses.PlainTextResponse)
async def generate_mdx_from_urls_raw_endpoint(request: GenerateMDXFromURLsRequest):
    """
    Generate MDX content from multiple URLs using crawl4ai and LLM.
    Returns the raw MDX content as plain text instead of JSON.

    This endpoint:
    1. Takes a list of URLs and a topic
    2. Crawls all URLs using crawl4ai
    3. Combines the content and generates MDX using the LLM
    4. Returns the raw MDX content as plain text

    If crawling fails and use_llm_knowledge is True, it will use the LLM's existing knowledge to generate content.
    """
    try:
        # Generate MDX from the URLs using the new function
        mdx_content = await generate_mdx_from_urls_async(request.urls, request.topic, request.use_llm_knowledge)

        # Return the raw MDX content as plain text
        return mdx_content

    except Exception as e:
        # Since we're returning plain text, we'll format the error as text
        return f"Error: Failed to generate MDX from URLs - {str(e)}"