from typing import Annotated
from functools import lru_cache
from pydantic import AnyUrl, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic.networks import UrlConstraints
from app.domain.models import AppEnvironment, QdrantSettings, PostgresSettings, RedisSettings, EmbedderSettings, LLMSettings, ApiSettings

QdrantDsn = Annotated[
    AnyUrl,
    UrlConstraints(allowed_schemes=['http','https','grpc','grpcs'])
]

# Main application settings
class Settings(BaseSettings):
    """Pydantic settings model for the Scholar RAG application."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        env_prefix="APP_",
        extra="ignore",
    )
    
    """Root settings object — the single source of truth for the app."""
    environment : AppEnvironment = AppEnvironment.local
    log_level : str = "INFO"
    service_name : str = "scholar-rag"
    version : str = "0.1.0"

    """External service configurations."""
    qdrant : QdrantSettings = Field(default_factory=QdrantSettings)
    postgres : PostgresSettings = Field(default_factory=PostgresSettings)
    redis : RedisSettings = Field(default_factory=RedisSettings)
    embedder : EmbedderSettings = Field(default_factory=EmbedderSettings)
    llm : LLMSettings = Field(default_factory=LLMSettings)
    api : ApiSettings = Field(default_factory=ApiSettings)

    @property
    def is_production(self) -> bool:
        return self.environment == AppEnvironment.production

    @property
    def docs_enabled(self) -> bool:
        return not self.is_production
    
    @model_validator(mode="after")
    def _validate_cross_fields(self) -> "Settings":
        if self.embedder.dim != self.qdrant.vector_size:
            raise ValueError(f"embedder.dim ({self.embedder.dim}) must equal "f"qdrant.vector_size ({self.qdrant.vector_size})")

        if self.llm.provider != "local" and self.llm.api_key is None:
            raise ValueError("Llm.api_key is required when llm.provider is not local")

        if self.is_production and self.postgres.password is None:
            raise ValueError("postgres.password is required in production")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get the application settings, cached for performance."""
    return Settings()
