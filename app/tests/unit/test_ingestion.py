from app.adapters.in_memory.fake_embedder import FakeEmbedder
from app.modules.ingestion.chunking import TokenChunker
from app.modules.ingestion.service import DocumentIngestionService
from app.tests.unit.fake_vector_store import FakeVectorStore


def test_idempotent_ingestion(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("This is a test sentence that we will repeat to fill up tokens." * 1000)  # Create a large enough document
    vector_store = FakeVectorStore()
    embedder = FakeEmbedder()
    chunker = TokenChunker()

    use_case = DocumentIngestionService(embedder=embedder, vector_store=vector_store, chunker=chunker)

    total_ingested = use_case.execute(file_path=test_file)

    assert total_ingested == 1  # Assuming the document is chunked into one batch
    #Write the assertion that proves the database actually stored them.
    # How do you count the number of keys in our FakeVectorStore's dictionary?

    assert len(vector_store.db) == 1  # Assuming the document is chunked into one batch

    # 4. IDEMPOTENCY CHECK: The real test.
    # We run the EXACT same file through the pipeline a second time.

    total_ingested_again = use_case.execute(file_path=test_file)  # Ingest the same file again

    assert total_ingested_again == 0  # Assuming the document is already in the database, no new chunks should be ingested
    assert len(vector_store.db) == 1  # The number of keys in the store should remain the same
