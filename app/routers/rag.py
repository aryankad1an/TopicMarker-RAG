import uuid
import asyncio
from fastapi import APIRouter
from app.models.schemas import (
    QueryRequest, TopicResponse,
    GenerateMDXRequest, MDXResponse,
    RefineRequest, RefineResponse, TopicHierarchyResponse
)
from app.services.search import search_urls
from app.services.crawler import extract_text_from_url
from app.utils.chunker import chunk_text
from app.services.embeddings import get_embedding
from app.services.vectorstore import upsert_embeddings, query_similar, embed_and_store
from app.services.llm import extract_topics, generate_mdx, refine_content, generate_topic_hierarchy
from app.utils.response import success_response, error_response
from app.services.gemini_llm import generate_content

router = APIRouter()

BATCH_SIZE = 50

# @router.post(
#     "/search-topics",
#     response_model=TopicHierarchyResponse,
#     summary="Generate lesson‑plan topics & subtopics via LLM"
# )
# async def search_topics(request: QueryRequest):
#     if not request.query.strip():
#         return error_response("Query cannot be empty", status_code=400)

#     try:
#         hierarchy = generate_topic_hierarchy(request.query)
#     except Exception as e:
#         return error_response("LLM error", status_code=500, details=str(e))

#     if not hierarchy:
#         return error_response("No topics returned from LLM", status_code=404)

#     return success_response({"topics": hierarchy})

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


@router.post("/generate-mdx", response_model=MDXResponse)
def generate_mdx_endpoint(request: GenerateMDXRequest):
    try:
        all_texts = []
        for topic in request.topics:
            emb = get_embedding(topic)
            matches = query_similar(emb, top_k=request.top_k)
            for m in matches:
                all_texts.append(m['text'])

        combined = "\n\n".join(all_texts)
        mdx = generate_mdx(combined, request.topics)

        return success_response({"mdx": mdx})
    except Exception as e:
        return error_response("Failed to generate MDX", status_code=500, details=str(e))


@router.post("/refine", response_model=RefineResponse)
def refine(request: RefineRequest):
    try:
        ans = refine_content(request.mdx, request.question)
        return success_response({"answer": ans})
    except Exception as e:
        return error_response("Failed to refine content", status_code=500, details=str(e))
