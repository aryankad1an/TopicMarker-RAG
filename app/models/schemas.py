from pydantic import BaseModel
from typing import List

class QueryRequest(BaseModel):
    query: str
    limit: int = 10

class TopicResponse(BaseModel):
    topics: List[str]

class GenerateMDXRequest(BaseModel):
    topics: List[str]
    top_k: int = 5

class MDXResponse(BaseModel):
    mdx: str

class RefineRequest(BaseModel):
    mdx: str
    question: str

class RefineResponse(BaseModel):
    answer: str