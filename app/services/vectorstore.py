from pinecone import Pinecone, ServerlessSpec, PineconeApiException
from app.config import settings
from pinecone.exceptions import PineconeException
# Import Pinecone exceptions for error handling
# Instantiate the Pinecone client with both API key and environment
pc = Pinecone(
    api_key=settings.pinecone_api_key,
    environment=settings.pinecone_environment  # e.g., "us-east-1"
)

_index = None

def init_pinecone():
    global _index
    index_name = settings.pinecone_index_name

    try:
        # Check if index already exists
        existing_indexes = [index.name for index in pc.list_indexes()]
        if index_name not in existing_indexes:
            pc.create_index(
                name=index_name,
                dimension=1024,  # matches your actual embedding dimension
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
    except PineconeApiException as e:
        if e.status != 409:
            raise  # Ignore "already exists" error, raise anything else

    _index = pc.Index(index_name)

def upsert_embeddings(vectors: list[dict]):
    """
    vectors: list of dicts like
      { 'id': str,
        'values': [float, …],  # your 1024‑dim embedding
        'metadata': { 'text': str, … }
      }
    """
    _index.upsert(vectors=vectors)

def query_similar(vector: list[float], top_k: int = 5):
    """
    Returns the top_k most similar items to `vector`.
    """
    res = _index.query(
        vector=vector,
        top_k=top_k,
        include_metadata=True
    )
    return [
        {"id": m["id"], "text": m["metadata"]["text"], "score": m["score"]}
        for m in res["matches"]
    ]
