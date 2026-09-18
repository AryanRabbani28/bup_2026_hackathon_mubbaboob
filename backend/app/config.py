import os
from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"
    gemini_fallback_model: str = "gemini-3.5-flash-lite"
    gemini_timeout_seconds: int = 20
    gemini_max_retries: int = 2

    @field_validator("gemini_api_key")
    def clean_api_key(cls, v: str) -> str:
        return v.strip().strip('"').strip("'")

    class Config:
        env_file = ".env"

settings = Settings()
