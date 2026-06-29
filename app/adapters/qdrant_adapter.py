from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse
from app.domain.exception import DimensionMismatchErrors, PortUnavailibleError
from app.domain.models import MetaData, Point, SearchParams, SearchResult

class QdrantAdapter:
    def __init__(self, client: AsyncQdrantClient, collection_name: str="scholar_rag") -> None:
        self.client = client
        self.collection_name = collection_name

    async def upsert(self, point:Point):
        try:
            qdrant_point = models.PointStruct(
                id=str(point.point_id),
                vector=point.vector,
                payload=point.MetaData
            )

            await self.client.upsert(self.collection_name,points=[qdrant_point],wait=True)

        except UnexpectedResponse as e:
            if e.status_code == 400 and "dimension" in str(e.content).lower():
                raise DimensionMismatchErrors(f"Qdrant rejected vector shape: {str(e.content)}") from e
            raise PortUnavailibleError(f"Qdrant HTTP Error: {str(e.content)}") from e
        except Exception as e:
            raise PortUnavailibleError(f"Failed to connect to Qdrant: {str(e)}") from e
        
    async def search(self, searchParams: SearchParams) -> list[SearchResult]:
        qdrant_filter = None
        query = searchParams.query
        limit = searchParams.limit
        filters = searchParams.MetaData
        
        if filters and isinstance(filters, MetaData) and filters.match_conditions:
            must_conditions: list[models.Condition] = [
                models.FieldCondition(key=key, match=models.MatchValue(value=val))
                for key, val in filters.match_conditions.items()
            ]
            qdrant_filter = models.Filter(must=must_conditions)
        try:
            raw_results = await self.client.search(
                collection_name=self.collection_name,
                query_filter=qdrant_filter,
                query_vector=query,
                limit=limit,
            )
            return [SearchResult(search_id=str(hit.id), score=hit.score, MetaData=hit.payload or {}) for hit in raw_results]
        except Exception as e:
            raise PortUnavailibleError(f"Qdrant search failed: {str(e)}") from e




