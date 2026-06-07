from enum import Enum
from functools import lru_cache
from pydantic import SecretStr, PostgresDsn, QdrantDsn, Field, BaseModel,RedisDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Define the application environment
class AppEnvironment(str, Enum):
    local = "development"
    development = "development"
    production = "production"

# Configuration for Qdrant vector database
class QdrantSettings(BaseModel):
    host : str = "localhost" 
    port : int = 6333
    api_key : SecretStr | None = None
    collection : str = "scholar_rag"
    vector_size : int = 384
    https : bool = False

    @property
    def url(self) -> str:
        __scheme = "https" if self.https else "http"
        return f"{__scheme}://{self.host}:{self.port}"

# Configuration for PostgreSQL database
class PostgresSettings(BaseModel):
    host : str = "localhost"
    port : int = 5432
    user : str = "scholar"
    password : SecretStr | None = None
    database : str = "scholar_rag"
    pool_min_size : int = 1
    pool_max_size : int = 10
    
    @property
    def dsn(self) -> str:
        __pwd = self.password.get_secret_value() if self.password else ""
        return f"postgresql://{self.user}:{__pwd}@{self.host}:{self.port}/{self.database}"

# Configuration for Redis
class RedisSettings(BaseModel):
    host : str = "localhost"
    port : int = 6379
    db : int = 0
    password : SecretStr | None = None
    ttl_seconds : int = 3600

    @property
    def url(self) -> str:
        __auth = f":{self.password.get_secret_value()}@" if self.password else ""
        return f"redis://{__auth}{self.host}:{self.port}/{self.db}"

# Configuration for the embedding model
class EmbedderSettings(BaseModel):
    model_name : str = "sentence-transformers/all-MiniLM-L6-v2"
    dim: int = 384
    batch_size: int = 64
    device: str = "cpu"

# Configuration for the LLM (Language Model)
class LLMSettings(BaseModel):
    provider : str = "openai"
    api_key : SecretStr | None = None
    model : str = "gpt-4.0-mini"
    base_url : str | None = None
    max_tokens : int = 2048
    temprature : float = 0.0

# Configuration for the API server
class ApiSettings(BaseModel):
    title : str = "Scholar RAG Web App"
    description : str = "A web application for the Scholar RAG system."
    version : str = "1.0.0"
    host : str = "localhost"
    port : int = 8000
    rate_limit_per_minute : int = 60
    cors_origins : list[str] = Field(default_factory=list)
    request_timeout_seconds : int = 30

# Main application settings
class Settings(BaseSettings):
    """Pydantic settings model for the Scholar RAG application."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
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


@lru_cache()
def get_settings() -> Settings:
    """Get the application settings, cached for performance."""
    return Settings()