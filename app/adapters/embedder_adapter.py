from sentence_transformers import SentenceTransformer

class EmbedderAdapter:
    def __init__(self, client: SentenceTransformer):
        self.client = client

    async def embeded(self,chunks: list[str])-> list[list[float]]:
        return [[0.1, 0.2, 0.3]]