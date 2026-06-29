from app.api.schemas import SearchQuery
from app.domain.models import SearchParams, SearchResult
from app.domain.ports.vector_store_port import VectorStorePort

class DocumentRetrievalService:
    def __init__(self,vector_store:VectorStorePort) -> None:
        self.vector_store = vector_store
    
    async def search(self,searchQuery: SearchQuery)-> list[SearchResult]:
        __searchParams: SearchParams = SearchParams(query=searchQuery.query,limit=searchQuery.limit,MetaData=searchQuery.MetaData)
        return await self.vector_store.search(__searchParams)