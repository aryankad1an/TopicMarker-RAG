import uuid
import asyncio
import fastapi
from fastapi import APIRouter
from app.models.schemas import (
    QueryRequest, RefineRequest, RefineResponse,
    SearchRequest, SingleTopicRequest,
    DirectCrawlRequest, DirectMultiCrawlRequest,
    GenerateMDXFromURLRequest, GenerateMDXFromURLsRequest
)
from app.utils.response import success_response, error_response
from app.services.gemini_llm import generate_content, refine_content_with_gemini
from googlesearch import search
from app.services.crawler import (
    generate_single_topic_mdx_async, generate_mdx_document_async,
    generate_mdx_from_url_async, generate_mdx_from_urls_async
)

router = APIRouter()


@router.post(
    "/search-topics",
)
async def search_topics(request: QueryRequest):
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
        print("Generated hierarchy:", hierarchy)
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

@router.post("/direct-crawl")
async def direct_crawl_endpoint(request: DirectCrawlRequest):
    """
    Direct pipeline from crawl4ai to LLM without BeautifulSoup processing.

    This endpoint:
    1. Takes a URL and a query
    2. Crawls the URL using crawl4ai
    3. Sends the content directly to the LLM with the query
    4. Returns the LLM-generated content
    """
    try:
        # Import here to avoid circular imports
        from app.services.crawler import direct_crawl_to_llm_async

        # Use the direct crawl-to-LLM pipeline
        result = await direct_crawl_to_llm_async(request.url, request.query)

        return {
            "status": "success",
            "url": request.url,
            "query": request.query,
            "result": result
        }

    except Exception as e:
        return {
            "status": "error",
            "message": "Failed to process direct crawl to LLM",
            "details": str(e)
        }

@router.post("/direct-multi-crawl")
async def direct_multi_crawl_endpoint(request: DirectMultiCrawlRequest):
    """
    Direct pipeline from crawl4ai to LLM for multiple URLs without BeautifulSoup processing.

    This endpoint:
    1. Takes a list of URLs and a query
    2. Crawls all URLs using crawl4ai
    3. Sends the combined content directly to the LLM with the query
    4. Returns the LLM-generated content
    """
    try:
        # Import here to avoid circular imports
        from app.services.crawler import direct_multi_crawl_to_llm_async

        # Use the direct multi-crawl-to-LLM pipeline
        result = await direct_multi_crawl_to_llm_async(request.urls, request.query)

        return {
            "status": "success",
            "urls": request.urls,
            "query": request.query,
            "result": result
        }

    except Exception as e:
        return {
            "status": "error",
            "message": "Failed to process direct multi-crawl to LLM",
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