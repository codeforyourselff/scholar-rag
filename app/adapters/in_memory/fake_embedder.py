from app.domain.models import DocumentChunk, EmbeddedChunk
from app.domain.ports.embedder_port import EmbedderPort

class FakeEmbedder(EmbedderPort):
    def embed_chunks(self,chunks:list[DocumentChunk]) -> list[EmbeddedChunk]:
        return [
            EmbeddedChunk(**chunk.model_dump(),vector=[0.0]*384) for chunk in chunks
        ]

    def embed_query(self, text: str) -> list[float]:
        return [0.0]*384
