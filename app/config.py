from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    pinecone_api_key: str
    pinecone_environment: str
    pinecone_index_name: str
    hf_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    hf_llm_model: str = "google/flan-t5-base"
    duckduckgo_result_count: int = 10
    gemini_api_key:str

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        extra="allow"  # 👈 this tells Pydantic to ignore unrelated variables
    )

settings = Settings()
