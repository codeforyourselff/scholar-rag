from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse
from app.domain.exception import DimensionMismatchErrors, PortUnavailibleError
from app.domain.models import EmbeddedChunk

class QdrantAdapter:
    def __init__(self, client: AsyncQdrantClient, collection_name: str="scholar_rag") -> None:
        self.client = client
        self.collection_name = collection_name

    async def upsert(self, chunks:list[EmbeddedChunk])-> None:
        try:
            qdrant_point = [models.PointStruct(
                id=str(chunk.chunk_id),
                vector=chunk.vector,
                payload=None
            ) for chunk in chunks]

            await self.client.upsert(self.collection_name, points=qdrant_point, wait=True)

        except UnexpectedResponse as e:
            if e.status_code == 400 and "dimension" in str(e.content).lower():
                raise DimensionMismatchErrors(f"Qdrant rejected vector shape: {str(e.content)}") from e
            raise PortUnavailibleError(f"Qdrant HTTP Error: {str(e.content)}") from e
        except Exception as e:
            raise PortUnavailibleError(f"Failed to connect to Qdrant: {str(e)}") from e
        
    async def search(self,query: list[float], limit: int, MetaData: None) -> list[EmbeddedChunk]:
        qdrant_filter = None
        
        # if MetaData and MetaData.match_conditions:
        #     must_conditions: list[models.Condition] = [
        #         models.FieldCondition(key=key, match=models.MatchValue(value=val))
        #         for key, val in MetaData.match_conditions.items()
        #     ]
            # qdrant_filter = models.Filter(must=must_conditions)
        try:
            raw_results = await self.client.search(
                collection_name=self.collection_name,
                query_filter=qdrant_filter,
                query_vector=query,
                limit=limit,
            )
            result = [EmbeddedChunk(**chunk.model_dump()) for chunk in raw_results]
            return result
        except Exception as e:
            raise PortUnavailibleError(f"Qdrant search failed: {str(e)}") from e




