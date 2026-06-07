from config import Settings
from qdrant_client import AsyncQdrantClient
from redis.asyncio import Redis
from sentence_transformers import SentenceTransformer

class Container:
    def __init__(self,settings:Settings) -> None:
        self._settings=settings
        self._qdrant = AsyncQdrantClient | None = None
        self._redis : Redis | None = None
        self._pg_pool: asyncpg.Pool | None = None
        self._embedder: SentenceTransformer | None = None
        self._llm: object | None = None



