from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Neo4j Graph Database
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"


    # LLM APIs
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None


    # Defaults
    DEFAULT_LLM_PROVIDER: str = "groq"
    DEFAULT_MODEL: str = "openai/gpt-oss-120b"


    # Document Processing Defaults
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200


    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


# Global settings instance
settings = Settings()