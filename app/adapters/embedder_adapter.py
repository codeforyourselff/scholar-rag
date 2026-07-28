import asyncio
from sentence_transformers import SentenceTransformer

class EmbedderAdapter:
    def __init__(self, client: SentenceTransformer):
        self.client = client

    async def embed(self, user_query: list[str])-> list[list[float]]:
        # Offloads the blocking CPU operations to a background thread
        vectors = await asyncio.to_thread(self.client.encode, user_query)

        #sentence_transformers returns numpy arrays.Convert to native python floats.
        return [vector.tolist() for vector in vectors]