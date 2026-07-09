from typing import Protocol
from app.domain.models import DocumentChunk, EmbeddedChunk

class EmbedderPort(Protocol):
    async def embed_chunks(self,chunks: list[DocumentChunk])-> list[EmbeddedChunk]:
        """Idempotently saves embedded chunks to storage"""
        ...
    def embed_query(self,text: str)-> list[float]:
        """Embeds a single text string into dense vector representation"""
        ...