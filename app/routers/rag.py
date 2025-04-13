from fastapi import APIRouter
from app.models.schemas import (
    QueryRequest, TopicResponse,
    GenerateMDXRequest, MDXResponse,
    RefineRequest, RefineResponse
)
from app.services.search import search_urls
from app.services.crawler import crawl_url
from app.utils.chunker import chunk_text
from app.services.embeddings import get_embedding
from app.services.vectorstore import upsert_embeddings, query_similar
from app.services.llm import extract_topics, generate_mdx, refine_content

router = APIRouter()

@router.post("/search-topics", response_model=TopicResponse)
async def search_topics(request: QueryRequest):
    urls = search_urls(request.query, limit=request.limit)

    print("URLs found:")
    for url in urls:
        print("url:------>>>", url)
    
    topics = []
    for url in urls:
        md = await crawl_url(url)
        print("Crawled content:")
        # print("md:------>>>", md)
        topics += extract_topics(md)
    # dedupe
    return {"topics": list(dict.fromkeys(topics))}

@router.post("/generate-mdx", response_model=MDXResponse)
def generate_mdx_endpoint(request: GenerateMDXRequest):
    all_texts = []
    for topic in request.topics:
        emb = get_embedding(topic)
        matches = query_similar(emb, top_k=request.top_k)
        for m in matches:
            all_texts.append(m['text'])
    combined = "\n\n".join(all_texts)
    mdx = generate_mdx(combined, request.topics)
    return {"mdx": mdx}

@router.post("/refine", response_model=RefineResponse)
def refine(request: RefineRequest):
    ans = refine_content(request.mdx, request.question)
    return {"answer": ans}