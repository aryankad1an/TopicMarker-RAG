from pydantic import BaseModel
from typing import List

class QueryRequest(BaseModel):
    query: str
    limit: int = 2

class TopicResponse(BaseModel):
    topics: List[str]

class GenerateMDXRequest(BaseModel):
    topics: List[str]
    top_k: int = 2

class MDXResponse(BaseModel):
    mdx: str

class RefineRequest(BaseModel):
    mdx: str
    question: str

class RefineResponse(BaseModel):
    answer: str

# Enhanced refine request with selected text and topic
class RefineWithSelectionRequest(BaseModel):
    mdx: str
    question: str
    selected_text: str
    topic: str

# Refine with crawling request
class RefineWithCrawlingRequest(BaseModel):
    mdx: str
    question: str
    selected_text: str
    topic: str
    num_results: int = 2

# Refine with specific URLs request
class RefineWithURLsRequest(BaseModel):
    mdx: str
    question: str
    selected_text: str
    topic: str
    urls: List[str]

class TopicItem(BaseModel):
    topic: str
    subtopics: List[str]

class TopicHierarchyResponse(BaseModel):
    topics: List[TopicItem]

class GenerateMDXRequest(BaseModel):
    topics: List[TopicItem]
    top_k: int = 2

class MDXTopicResponse(BaseModel):
    topic: str
    mdx: str

class GenerateMDXResponse(BaseModel):
    results: List[MDXTopicResponse]

class Topic(BaseModel):
    topic: str
    subtopics: List[str]

class SearchRequest(BaseModel):
    topics: List[Topic]
    top_k: int = 2

class SingleTopicRequest(BaseModel):
    topic: str
    num_results: int = 2



class GenerateMDXFromURLRequest(BaseModel):
    url: str
    topic: str
    use_llm_knowledge: bool = True

class GenerateMDXFromURLsRequest(BaseModel):
    urls: List[str]
    topic: str
    use_llm_knowledge: bool = True

class MDXContent(BaseModel):
    """
    Model for MDX content with proper handling of newlines.
    """
    content: str

    class Config:
        json_encoders = {
            str: lambda v: v.replace('\n', '\\n')
        }