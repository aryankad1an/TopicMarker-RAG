import json
from transformers import pipeline
from app.config import settings

_topic_extractor = None
_text_generator = None

def extract_topics(text: str) -> list[str]:
    global _topic_extractor
    if _topic_extractor is None:
        _topic_extractor = pipeline(
            "text2text-generation", model=settings.hf_llm_model
        )
    prompt = (
        f"Extract the main topics from the following text and return a JSON array of strings:\n"  
        f"{text}"  
    )
    out = _topic_extractor(prompt, max_length=200)[0]['generated_text']
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return [line.strip('- ') for line in out.splitlines() if line.strip()]


def generate_mdx(text: str, topics: list[str]) -> str:
    global _text_generator
    if _text_generator is None:
        _text_generator = pipeline(
            "text2text-generation", model=settings.hf_llm_model
        )
    prompt = (
        f"Generate a lesson plan in MDX format for the topics {topics} based on this content:\n{text}"  
    )
    return _text_generator(prompt, max_length=1024)[0]['generated_text']


def refine_content(mdx: str, question: str) -> str:
    global _text_generator
    if _text_generator is None:
        _text_generator = pipeline(
            "text2text-generation", model=settings.hf_llm_model
        )
    prompt = (
        f"Here is MDX content:\n{mdx}\nUser asks: {question}\n"  
        "Please return an updated MDX snippet."  
    )
    return _text_generator(prompt, max_length=512)[0]['generated_text']