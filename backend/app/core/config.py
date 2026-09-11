from pathlib import Path
from typing import Optional
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings powered by pydantic-settings.
    Loads environment variables from .env file or system environment.
    """
    # Project Settings
    PROJECT_NAME: str = "LLM + Knowledge Graph Research Assistant API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # Security & Auth Settings
    SECRET_KEY: str = "super_secret_jwt_key_change_me_in_production_32bytes!"
    JWT_SECRET: str = "super_secret_jwt_key_change_me_in_production_32bytes!"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # PostgreSQL + pgvector Configuration
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "kg_research_db"
    DATABASE_URL: Optional[str] = None

    # Neo4j Database Configuration
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM & Embedding Settings
    LLM_PROVIDER: str = "groq"  # Options: 'groq', 'gemini', 'llama'
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # File Storage Settings
    MAX_UPLOAD_SIZE_MB: int = 50
    UPLOAD_DIR: str = "data/uploads"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    def get_database_url(self) -> str:
        """Returns computed async postgres database URL if not explicitly set."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()

# Ensure Upload Directory exists
upload_path = Path(settings.UPLOAD_DIR)
upload_path.mkdir(parents=True, exist_ok=True)
