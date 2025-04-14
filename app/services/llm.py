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
        "Extract the main topics from the following text and return a list of strings:\n"
        f"{text}"
    )

    try:
        output = _topic_extractor(prompt, max_length=10)[0]['generated_text']
        print("📌 Topic Extraction Output:", output)

        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return [line.strip('-•* ') for line in output.splitlines() if line.strip()]
    except Exception as e:
        print("❌ Error during topic extraction:", e)
        raise RuntimeError(f"Topic extraction failed: {e}")


def generate_mdx(text: str, topics: list[str]) -> str:
    global _text_generator
    if _text_generator is None:
        _text_generator = pipeline(
            "text2text-generation", model=settings.hf_llm_model
        )

    prompt = (
        f"Generate a lesson plan in MDX format for the topics {topics} based on this content:\n{text}"
    )

    try:
        return _text_generator(prompt, max_length=1024)[0]['generated_text']
    except Exception as e:
        print("❌ Error generating MDX:", e)
        raise RuntimeError(f"MDX generation failed: {e}")


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

    try:
        return _text_generator(prompt, max_length=512)[0]['generated_text']
    except Exception as e:
        print("❌ Error refining MDX content:", e)
        raise RuntimeError(f"Refinement failed: {e}")


def generate_topic_hierarchy(query: str) -> list[dict]:
    global _text_generator
    if _text_generator is None:
        _text_generator = pipeline(
            "text2text-generation", model=settings.hf_llm_model
        )

    prompt = (
        f"Generate a list of main topics and subtopics for a lesson plan "
        f"based on the query: \"{query}\".\n"
        f"Return the result as a JSON array of objects, each with:\n"
        f"  - \"topic\": string\n"
        f"  - \"subtopics\": array of strings\n"
        f"Example output:\n"
        f"[{{\"topic\": \"Photosynthesis\", \"subtopics\": [\"Light Reactions\", \"Calvin Cycle\"]}}, ...]\n"
    )

    try:
        output = _text_generator(prompt, max_length=256)[0]["generated_text"]
        print("📘 Hierarchy Output:", output)
        return json.loads(output)
    except json.JSONDecodeError as json_err:
        print("⚠️ JSON decode error in hierarchy output:", json_err)
        return []
    except Exception as e:
        print("❌ Error generating topic hierarchy:", e)
        raise RuntimeError(f"Topic hierarchy generation failed: {e}")
