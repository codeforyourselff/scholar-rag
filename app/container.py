import asyncio
import logging
import asyncpg
from app.config import Settings, get_settings
from qdrant_client import AsyncQdrantClient
from redis.asyncio import Redis
from sentence_transformers import SentenceTransformer
logger = logging.getLogger(__name__)

class Container:
    def __init__(self,settings:Settings = get_settings()) -> None:
        self._settings=settings or get_settings()
        self._qdrant: AsyncQdrantClient | None = None
        self._redis : Redis | None = None
        self._pg_pool: asyncpg.Pool | None = None
        self._embedder: SentenceTransformer | None = None
        self._llm: object | None = None

    @property
    def settings(self) -> Settings:
        return self._settings
    
    @property
    def qdrant(self) -> AsyncQdrantClient:
        if self._qdrant is None:
            raise RuntimeError("Container not standard: call startup() first")
        return self._qdrant
    
    @property
    def redis(self) -> Redis:
        if self._redis is None:
            raise RuntimeError("Container not standard: call startup() first")
        return self._redis
    
    @property
    def pg_pool(self) -> asyncpg.Pool:
        if self._pg_pool is None:
            raise RuntimeError("Container not standard: call startup() first")
        return self._pg_pool
        
    @property
    def embedder(self) -> SentenceTransformer:
        if self._embedder is None:
            raise RuntimeError("Container not standard: call startup() first")
        return self._embedder
        
    async def startup(self) -> None:
        settings = self._settings
        logger.info("Starting container (env=%s)",settings.environment.value)

        # Qdrant
        self._qdrant = AsyncQdrantClient(
            url=settings.qdrant.host,
            api_key=settings.qdrant.api_key.get_secret_value() if settings.qdrant.api_key else None
        )

        # Redis
        self._redis = Redis.from_url(settings.redis.url, decode_responses=True)

        # Postgres
        self._pg_pool = await asyncpg.create_pool(
            dsn=settings.postgres.dsn,
            min_size=settings.postgres.pool_min_size,
            max_size=settings.postgres.pool_max_size
        )

        # Embeding model - loading is blocking , so keep it off the event loop
        self._embedder = await asyncio.to_thread(
            SentenceTransformer, settings.embedder.model_name, device=settings.embedder.device
        )

        # LLM Client 
        if settings.llm.provider == "openai":
            from openai import AsyncOpenAI

            self._llm = AsyncOpenAI(
                api_key=settings.llm.api_key.get_secret_value() if settings.llm.api_key else None,
                base_url=settings.llm.base_url
            )

        logger.info("Conainer started")

    async def shutdown(self) -> None:
        logger.info("Shutting down container")
        if self._qdrant is not None:
            await self._qdrant.close()
        if self._redis is not None:
            await self._redis.close()
        if self._pg_pool is not None:
            await self.pg_pool.close()
        if self._llm is not None and hasattr(self._llm, " close"):
            await self._llm.close()
        logger.info("Container shut down")

    async def check_readiness(self) -> dict[str,bool]:
        checks :dict[str,bool] = {}

        try:
            await self.qdrant.get_collections()
            checks["qdrant"]  = True
        except Exception:
            checks["qdrant"] = False

        try:
            checks["redis"] = bool(await self.redis.ping())
        except Exception:
            checks["redis"] = False

        try:
            async with self.pg_pool.acquire() as conn:
                await conn.execute("SELECT 1")
            checks["postgres"] = True
        except Exception:
            checks["postgres"] = False

        checks["embedder"] = self._embedder is not None
        return checks

def build_container(settings:Settings) -> Container:
    return Container(settings)



