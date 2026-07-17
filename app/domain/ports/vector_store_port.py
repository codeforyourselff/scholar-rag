from typing import Any, Protocol
from app.domain.models import EmbeddedChunk

class VectorStorePort(Protocol):
    async def upsert(self, chunks:list[EmbeddedChunk])-> None:
        ...

    async def search(self, query: list[float], limit: int, MetaData: dict[str,Any])-> list[EmbeddedChunk]:
        ... 