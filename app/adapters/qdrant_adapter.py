from typing import Any
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse
from app.domain.exception import DimensionMismatchErrors, PortUnavailableError
from app.domain.models import DocumentMetaData, EmbeddedChunk

class QdrantAdapter:
    def __init__(self, client: AsyncQdrantClient, collection_name: str="scholar_rag") -> None:
        self.client = client
        self.collection_name = collection_name

    async def upsert(self, chunks:list[EmbeddedChunk])-> None:
        if not self.collection_name:
            raise ValueError(f"Collection name is not defined.{self.collection_name}")

        if not await self.client.collection_exists(collection_name=self.collection_name):
            raise ValueError(f"Collection {self.collection_name} does not exists.")
        try:
            qdrant_point = [models.PointStruct(
                id=chunk.chunk_id,
                vector=chunk.vector,
                payload={
                    "text":chunk.text,
                    "chunk_index":chunk.chunk_index,
                    "metadata":chunk.metadata.model_dump()
                }
            ) for chunk in chunks]

            await self.client.upsert(self.collection_name, points=qdrant_point, wait=True)

        except UnexpectedResponse as e:
            if e.status_code == 400 and "dimension" in str(e.content).lower():
                raise DimensionMismatchErrors(f"Qdrant rejected vector shape: {str(e.content)}") from e
            raise PortUnavailableError(f"Qdrant HTTP Error: {str(e.content)}") from e
        except Exception as e:
            raise PortUnavailableError(f"Failed to connect to Qdrant: {str(e)}") from e
        
    async def search(self,query: list[float], limit: int, meta_data: dict[str,Any] | None = None) -> list[EmbeddedChunk]:
        try:
            raw_results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=query,
                limit=limit,
                with_payload=True,
                with_vectors=True
            )

            # Manually reconstruct the Domain Model from the Qdrant responses
            results = []
            for point in raw_results:
                if point.payload is None or point.vector is None:
                    continue # Skip corrupted records
                    
                meta_obj = DocumentMetaData(**point.payload["metadata"])

            results.append(
                EmbeddedChunk(
                text=point.payload["text"],
                chunk_index=point.payload["chunk_index"],
                meta_data=meta_obj,
                vector=point.vector
                ))
            return results
        except Exception as e:
            raise PortUnavailableError(f"Qdrant search failed: {str(e)}") from e




