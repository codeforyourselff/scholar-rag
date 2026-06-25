
import math

from app.domain.exception import DimensionMismatchErrors
from app.domain.models import MetaData, Point, SearchResult


def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """A pure Python implementation of Cosine Similarity. No external libraries."""
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_v1 = math.sqrt(sum(a * a for a in v1))
    norm_v2 = math.sqrt(sum(b * b for b in v2))
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)


class InMemoryVectorStore:

    def __init__(self,dimension:int) -> None:
        self.dimension = dimension
        self.store:dict[str,Point] = {}

    async def upsert(self, point:Point) -> None:
        if len(point.vector) != self.dimension:
            raise DimensionMismatchErrors(
                f"Store dimension is {self.dimension}, but point vector is {len(point.vector)}."
            )
        self.store[str(point.point_id)] = point

    async def search(self, query: list[float], limit: int, filters: MetaData | None = None) -> list[SearchResult]:
        results: list[SearchResult] = []

        for point in self.store.values():
            if filters:
                match = True
                for key,val in filters:
                    if point.MetaData.get(key) != val:
                        match = False
                        break
                if not match:
                    continue

            score = _cosine_similarity(query,point.vector)
            results.append(SearchResult(search_id=str(point.point_id),score=score,MetaData=point.MetaData))

        results.sort(key=lambda x: x.score,reverse=True)
        return results[:limit]