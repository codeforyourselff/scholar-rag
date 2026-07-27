from typing import Protocol

class EmbedderPort(Protocol):
    async def embed(self, user_query: list[str])-> list[list[float]]:
        """Embeds a batch of text strings into dense vector representations."""
        ...