from enum import Enum
from pydantic import BaseModel, Field, SecretStr

# AppEnvironment
class AppEnvironment(str, Enum):
    local = "local"
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
    host : str = "127.0.0.1"
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
    temperature : float = 0.0

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