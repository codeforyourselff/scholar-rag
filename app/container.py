import asyncio
import logging
import asyncpg
from typing import cast
from openai import AsyncOpenAI
from app.adapters.embedder_adapter import EmbedderAdapter
from app.config import AppEnvironment, Settings, get_settings
from redis.asyncio import Redis
from qdrant_client import AsyncQdrantClient
from sentence_transformers import SentenceTransformer
from app.adapters.qdrant_adapter import QdrantAdapter
from app.domain.ports.vector_store_port import VectorStorePort
from app.modules.ingestion.chunking import TokenChunker
from app.modules.ingestion.service import DocumentIngestionService
from app.modules.retrieval.service import DocumentRetrievalService
from app.tests.unit.fake_vector_store import FakeVectorStore

logger = logging.getLogger(__name__)

class Container:
    def __init__(self,settings:Settings = get_settings()) -> None:
        self._settings=settings or get_settings()
        self._qdrant: AsyncQdrantClient | None = None
        self._redis : Redis | None = None
        self._pg_pool: asyncpg.Pool | None = None
        self._embedder: SentenceTransformer | None = None
        self._llm: AsyncOpenAI | None = None

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
        if self.settings.environment != AppEnvironment.local:
            self._qdrant = AsyncQdrantClient(
                url=settings.qdrant.url,
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
        if self._llm is not None and hasattr(self._llm, "close"):
            await self._llm.close()
        logger.info("Container shut down")

    async def check_readiness(self) -> dict[str,bool]:
        checks :dict[str,bool] = {}

        try:
            if self.settings.environment != AppEnvironment.local:
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
    
    # def get_document_retrieval_service(self)-> DocumentRetrievalService:
    #     adapter: QdrantAdapter = QdrantAdapter(client=self.qdrant,collection_name=self._settings.qdrant.collection)
    #     embedder: EmbedderAdapter = EmbedderAdapter
    #     return DocumentRetrievalService(vector_store=adapter,)

    def get_document_ingestion_service(self) -> DocumentIngestionService:
        token_chunker: TokenChunker = TokenChunker(chunk_size=500, chunk_overlap=50, model_name="cl100k_base")
        embedder_adapter: EmbedderAdapter = EmbedderAdapter(client=self.embedder)
        if self.settings.environment == AppEnvironment.local:
            qdrant_adapter: VectorStorePort = FakeVectorStore()
        else:
            qdrant_adapter = cast(VectorStorePort, QdrantAdapter(
                client=self.qdrant,
                collection_name=self.settings.qdrant.collection
            ))
        return DocumentIngestionService(embedder=embedder_adapter, vector_store=qdrant_adapter, chunker=token_chunker, batch_size=500)


def build_container(settings:Settings) -> Container:
    return Container(settings)