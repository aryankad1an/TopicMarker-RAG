# import google.generativeai as genai
# from app.config import settings

# gemini_api_key = settings.gemini_api_key
# if not gemini_api_key:
#     raise ValueError("Gemini API key is not set in the environment variables.")

# client = genai.configure(api_key=gemini_api_key)

# # response = client.models.generate_content(
# #     model="gemini-2.0-flash", contents="Explain how AI works in a few words"
# # )
# # print(response.text)

# def generate_content(prompt: str) -> str:
#     try:
#         response = client.models.generate_content(
#             model="gemini-2.0-flash", contents=prompt
#         )
#         # print("📌 Gemini LLM Output:", response.text)
#         return response.text
#     except Exception as e:
#         # print("❌ Error generating content:", e)
#         raise RuntimeError(f"Content generation failed: {e}")


import google.generativeai as genai
from app.config import settings

# Configure Gemini with your API key
gemini_api_key = settings.gemini_api_key
if not gemini_api_key:
    raise ValueError("Gemini API key is not set in the environment variables.")

genai.configure(api_key=gemini_api_key)

def generate_content(prompt: str) -> str:
    try:
        model = genai.GenerativeModel(model_name="gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        raise RuntimeError(f"Content generation failed: {e}")

def refine_content_with_gemini(mdx: str, question: str) -> str:
    """
    Refines MDX content based on a user question using Gemini API.

    Args:
        mdx: The original MDX content
        question: The user's question or request for refinement

    Returns:
        The refined MDX content
    """
    prompt = f"""
    Here is MDX content:

    {mdx}

    User asks: {question}

    Please return an updated MDX snippet that addresses the user's question or request.
    Make sure to maintain proper MDX formatting in your response.
    """

    try:
        return generate_content(prompt)
    except Exception as e:
        print(f"❌ Error refining MDX content with Gemini: {e}")
        raise RuntimeError(f"Refinement with Gemini failed: {e}")
