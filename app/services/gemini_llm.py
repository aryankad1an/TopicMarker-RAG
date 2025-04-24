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
