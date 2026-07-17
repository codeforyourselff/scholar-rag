from app.domain.models import EmbeddedChunk
from app.domain.ports.embedder_port import EmbedderPort
from app.domain.ports.vector_store_port import VectorStorePort

class DocumentRetrievalService:
    def __init__(self,vector_store:VectorStorePort, embedder:EmbedderPort) -> None:
        self.vector_store = vector_store
        self.embedder = embedder

    async def execute(self, user_query: str, limit: int)-> list[EmbeddedChunk]:
        embedded_query = self.embedder.embed_query(user_query)
        return await self.vector_store.search(embedded_query,limit,MetaData={})





    