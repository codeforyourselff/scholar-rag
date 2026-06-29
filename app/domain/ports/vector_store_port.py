from typing import Protocol
from app.domain.models import EmbeddedChunk, SearchParams, SearchResult

class VectorStorePort(Protocol):
    
    async def upsert(self,points:list[EmbeddedChunk])-> None:
        ...

    async def search(self,searchParams:SearchParams)-> list[SearchResult]:
        ...