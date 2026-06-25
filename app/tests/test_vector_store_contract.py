import uuid
import pytest
from qdrant_client import AsyncQdrantClient
from app.domain.exception import DimensionMismatchErrors
from app.domain.models import Point

pytestmask = pytest.mark.asyncio

@pytest.fixture(params=["qdrant"])
def vector_store(request):
    if request.param == "fake":
        from app.adapters.test_in_memory_adapter import InMemoryVectorStore
        return InMemoryVectorStore(dimension=3)
    
    if request.param == "qdrant":
        from app.adapters.qdrant_adapter import QdrantAdapter
        # instantiate AsyncQdrantClient (not pass the class) to satisfy type
        client = AsyncQdrantClient(host="localhost",port=6333)
        return QdrantAdapter(client, "scholar_rag")
    
async def test_upsert_and_search_retrieves_point(vector_store):
    demo_id : uuid.UUID = uuid.uuid4()
    point = Point(point_id=str(demo_id),vector=[0.1, 0.2, 0.3],MetaData={"author": "John"})

    await vector_store.upsert(point)

    results = await vector_store.search(query=[0.1, 0.2, 0.3],limit=1)
    print(results)

    assert len(results) == 1
    assert results[0].search_id == str(demo_id)
    assert results[0].MetaData["author"] == "John"


async def test_upsert_is_idempotent(vector_store):
    demo_id : uuid.UUID = uuid.uuid4()
    point = Point(point_id=str(demo_id), vector=[0.9, 0.8, 0.7], MetaData={})

    await vector_store.upsert(point)
    await vector_store.upsert(point)

    results = await vector_store.search(query=[0.9, 0.8, 0.7], limit=5)

    retrived_ids = [res.search_id for res in results]
    assert retrived_ids.count(str(demo_id)) == 1


async def test_upsert_enforces_dimension_mismatch(vector_store):
    demo_id : uuid.UUID = uuid.uuid4()
    bad_point = Point(point_id=str(demo_id),vector=[0.8, 0.7],MetaData={})

    with pytest.raises(DimensionMismatchErrors):
        await vector_store.upsert(bad_point)
