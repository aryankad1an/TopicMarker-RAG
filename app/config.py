from pydantic import BaseSettings
from dotenv import load_dotenv
import os

# Load variables from .env file
load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_API_ENDPOINT: str = os.getenv("LLM_API_ENDPOINT", "https://api.llmprovider.com")

    class Config:
        env_file = ".env"

settings = Settings()
