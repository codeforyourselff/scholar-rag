from typing import Protocol
from app.domain.models import MetaData, Point, SearchResult

class VectorStorePort(Protocol):
    async def upsert(self,points:list[Point])-> None:
        ...

    async def search(self,query:list[float],limit:int,filters: MetaData | None = None)-> list[SearchResult]:
        ...