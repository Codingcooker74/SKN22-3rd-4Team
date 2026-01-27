"""
Application configuration settings
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Project paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    VECTOR_STORE_DIR: Path = DATA_DIR / "vector_store"
    MODELS_DIR: Path = BASE_DIR / "models"

    # API Keys
    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")

    # Supabase
    SUPABASE_URL: Optional[str] = Field(None, env="SUPABASE_URL")
    SUPABASE_KEY: Optional[str] = Field(None, env="SUPABASE_KEY")

    # Vector Database
    CHROMADB_HOST: str = Field("localhost", env="CHROMADB_HOST")
    CHROMADB_PORT: int = Field(8000, env="CHROMADB_PORT")

    # Finnhub
    FINNHUB_API_KEY: Optional[str] = Field(None, env="FINNHUB_API_KEY")

    # Database
    DATABASE_URL: str = Field("sqlite:///./data/financial_data.db", env="DATABASE_URL")

    # Application Settings
    DEBUG: bool = Field(False, env="DEBUG")
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    MAX_WORKERS: int = Field(4, env="MAX_WORKERS")

    # Model Settings
    EMBEDDING_MODEL: str = Field("text-embedding-3-small", env="EMBEDDING_MODEL")
    LLM_MODEL: str = Field("gpt-4-turbo-preview", env="LLM_MODEL")
    TEMPERATURE: float = Field(0.1, env="TEMPERATURE")
    MAX_TOKENS: int = Field(4096, env="MAX_TOKENS")

    # RAG Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RESULTS: int = 5
    SIMILARITY_THRESHOLD: float = 0.7

    # Graph Settings
    MAX_GRAPH_DEPTH: int = 3
    MIN_RELATIONSHIP_STRENGTH: float = 0.5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = (
            "ignore"  # Ignore extra fields from .env that aren't defined in Settings
        )


# Global settings instance
settings = Settings()

# Ensure directories exist
settings.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
