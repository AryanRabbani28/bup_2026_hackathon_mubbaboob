import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    gemini_fallback_model: str = "gemini-1.5-pro"
    gemini_timeout_seconds: int = 15
    gemini_max_retries: int = 2

    class Config:
        env_file = ".env"

settings = Settings()
