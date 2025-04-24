import uuid
import asyncio
from fastapi import APIRouter, HTTPException, Request
from app.models.schemas import (
    QueryRequest, TopicResponse,
    GenerateMDXRequest, MDXResponse,
    RefineRequest, RefineResponse, TopicHierarchyResponse, TopicItem,
    GenerateMDXResponse, MDXTopicResponse
)
from app.services.search import search_urls
from app.utils.chunker import chunk_text
from app.services.embeddings import get_embedding
from app.services.vectorstore import upsert_embeddings, query_similar, embed_and_store
from app.services.llm import extract_topics, generate_mdx, refine_content, generate_topic_hierarchy
from app.utils.response import success_response, error_response
from app.services.gemini_llm import generate_content
from typing import List
from googlesearch import search
from app.services.crawler import scrape_with_crawl4ai
from pydantic import BaseModel
from app.models.schemas import SearchRequest
from app.services.crawler import generate_mdx_document

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
        
        # Generate MDX from the collected URLs and topics
        mdx_code = generate_mdx_document(list(all_urls), topics_data)

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
def refine(request: RefineRequest):
    try:
        ans = refine_content(request.mdx, request.question)
        return success_response({"answer": ans})
    except Exception as e:
        return error_response("Failed to refine content", status_code=500, details=str(e))
