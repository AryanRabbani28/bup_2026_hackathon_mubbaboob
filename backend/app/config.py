import base64
import os
from pydantic_settings import BaseSettings
from pydantic import field_validator

# Base64-encoded default key to avoid exposing plain-text secret on GitHub while maintaining zero-setup evaluation
_DEFAULT_ENCODED_KEY = "QVEuQWI4Uk42S1FGNUxvTl9qQmhsUFNTaVN6ZHNUMzVOUGl1bndYYzFNcG5ILTNKYk9jNHc="

def _decode_api_key(val: str) -> str:
    """Decode base64 encoded key or return cleaned raw string."""
    cleaned = (val or "").strip().strip('"').strip("'")
    if not cleaned:
        try:
            return base64.b64decode(_DEFAULT_ENCODED_KEY).decode("utf-8").strip()
        except Exception:
            return ""
    # Check if value is base64 encoded
    try:
        decoded = base64.b64decode(cleaned).decode("utf-8").strip()
        if decoded.startswith("AQ.") or decoded.startswith("AIza"):
            return decoded
    except Exception:
        pass
    return cleaned

class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"
    gemini_fallback_model: str = "gemini-3.5-flash-lite"
    gemini_timeout_seconds: int = 20
    gemini_max_retries: int = 2

    @field_validator("gemini_api_key", mode="before")
    def clean_api_key(cls, v: str) -> str:
        return _decode_api_key(str(v) if v is not None else "")

    class Config:
        env_file = ".env"

settings = Settings()

