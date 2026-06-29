from typing import Protocol
from app.domain.models import DocumentChunk, EmbeddedChunk

class EmbedderPort(Protocol):
    def embed_chunks(self,chunks: list[DocumentChunk])-> list[EmbeddedChunk]:
        """Idempotently saves embedded chunks to storage"""
        ...