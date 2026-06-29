from app.domain.models import EmbeddedChunk
from app.domain.ports.vector_store_port import VectorStorePort

class FakeVectorStore(VectorStorePort):
    def __init__(self)-> None:
        self.db: dict[str,EmbeddedChunk] = {}

    def upsert(self, chunks: list[EmbeddedChunk]) -> None:
        """Idempotently saves embedded chunks to storage"""
        for chunk in chunks:
            self.db[chunk.chunk_id] = chunk