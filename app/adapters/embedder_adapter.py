import asyncio
from sentence_transformers import SentenceTransformer

class EmbedderAdapter:
    def __init__(self, client: SentenceTransformer):
        self.client = client

    async def embed(self, texts: list[str])-> list[list[float]]:
        # Offloads the blocking CPU operations to a background thread
        vectors = await asyncio.to_thread(self.client.encode, texts)

        #sentence_transformers returns numpy arrays.Convert to native python floats.
        return [vector.list() for vector in vectors]