from app.domain.models import EmbeddedChunk
from app.domain.ports.embedder_port import EmbedderPort
from app.domain.ports.vector_store_port import VectorStorePort

class DocumentRetrievalService:
    def __init__(self, vector_store:VectorStorePort, embedder:EmbedderPort) -> None:
        self.vector_store = vector_store
        self.embedder = embedder

    async def execute(self, user_query: str, limit: int)-> list[EmbeddedChunk]:
        # Await the call, wrap the single query in a list for the batch interface
        vector_batches = await self.embedder.embed(user_query=[user_query])

        # extract the single vector from the batch
        query_vector = vector_batches[0] 

        # search the database
        return await self.vector_store.search(query=query_vector,limit=limit,meta_data={})