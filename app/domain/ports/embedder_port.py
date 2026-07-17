from typing import Protocol

class EmbedderPort(Protocol):
    async def embeded(self,chunks: list[str])-> list[list[float]]:
        """Embeds a batch of text strings into dense vector representations."""
        ...