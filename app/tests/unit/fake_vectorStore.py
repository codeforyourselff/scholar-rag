from cmath import sqrt
from app.domain.models import EmbeddedChunk
from app.domain.ports.vector_store_port import VectorStorePort
from app.utils.math import cosine_similarity

class FakeVectorStore(VectorStorePort):
    """Inject the DocumentRetrievalService to use the consine_similarity method for scoring"""
    def __init__(self)-> None:
        self.db: dict[str,EmbeddedChunk] = {}

    async def upsert(self, chunks: list[EmbeddedChunk]) -> None:
        """Idempotently saves embedded chunks to storage"""
        for chunk in chunks:
            self.db[chunk.chunk_id] = chunk

    async def search(self, searchParams) -> list[EmbeddedChunk]:
        """Searches for embedded chunks based on the provided search parameters."""
        scored_chunks: list[tuple[float,EmbeddedChunk]] = []

        for chunk in self.db.values():
            consine_similarity = cosine_similarity(self,searchParams.query, chunk.vector)
            scored_chunks.append((consine_similarity, chunk))

        # Sort the scored chunks based on the score in descending order
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chunk for score, chunk in scored_chunks[:searchParams.limit]]