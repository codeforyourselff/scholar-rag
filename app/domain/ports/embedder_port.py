from typing import Protocol
from app.domain.models import Chunk

class EmbedderPort(Protocol):
    async def embed(self, user_query: list[Chunk])-> list[list[float]]:
        """Embeds a batch of text strings into dense vector representations."""
        ...