"""
PG-AGI Configuration Module
Loads all settings from environment variables for secure credential management.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # NVIDIA NIM API
    NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
    NVIDIA_MODEL_NAME: str = os.getenv("NVIDIA_MODEL_NAME", "qwen/qwen3-coder-480b-a35b-instruct")
    NVIDIA_BASE_URL: str = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

    # PostgreSQL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/pgagi_db")

    # ChromaDB
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")

    # CORS
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000")

    # Difficulty gate weights for accuracy scoring
    W1_COSINE: float = 0.7  # Weight for cosine similarity
    W2_TERM: float = 0.3    # Weight for term overlap

    # Difficulty thresholds
    SIMPLE_THRESHOLD: float = 0.0
    MODERATE_THRESHOLD: float = 0.5
    COMPLEX_THRESHOLD: float = 0.75

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
