"""Core configuration for NEXUS."""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Gemini API / Model Routing
    gemini_api_key: str = Field(default="", description="Google Gemini API key")
    gemini_reasoning_model: str = Field(
        default="gemini-2.5-pro",
        description="Reasoning Gemini model for planning, synthesis, novelty, and red-team",
        validation_alias="GEMINI_REASONING_MODEL"
    )
    gemini_fast_model: str = Field(
        default="gemini-2.5-flash",
        description="Fast Gemini model for triage, extraction, and candidate generation",
        validation_alias="GEMINI_FAST_MODEL"
    )
    # Legacy alias support
    gemini_model: Optional[str] = Field(
        default=None,
        description="Legacy model alias (falls back to reasoning model if set)",
        validation_alias="GEMINI_MODEL"
    )

    # Embedding
    embedding_model: str = Field(default="all-MiniLM-L6-v2", description="Sentence transformer model")

    # Academic APIs
    openalex_email: str = Field(default="", description="Email for OpenAlex polite pool")
    semantic_scholar_api_key: str = Field(default="", description="Semantic Scholar API key")
    crossref_email: str = Field(default="", description="Email for Crossref polite pool")

    # Database
    database_url: str = Field(default="sqlite:///./data/nexus.db", description="Database URL")

    # Application
    demo_mode: bool = Field(default=True, description="Enable demo mode with synthetic data")
    log_level: str = Field(default="INFO", description="Logging level")
    backend_port: int = Field(default=8000, description="Backend server port")

    # Rate Limiting
    max_papers_deep_analysis: int = Field(default=15, description="Max papers for deep analysis")
    max_concurrent_llm_calls: int = Field(default=3, description="Max concurrent LLM calls")
    llm_rate_limit_per_minute: int = Field(default=15, description="LLM requests per minute")

    # Paths
    data_dir: Path = Field(default=Path("data"), description="Data directory")
    cache_dir: Path = Field(default=Path("data/cache"), description="Cache directory")
    upload_dir: Path = Field(default=Path("data/uploads"), description="Upload directory")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    def ensure_directories(self):
        """Create required directories."""
        for d in [self.data_dir, self.cache_dir, self.upload_dir]:
            d.mkdir(parents=True, exist_ok=True)


# Singleton
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.ensure_directories()
    return _settings
