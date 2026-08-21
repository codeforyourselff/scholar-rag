import logging
from app.domain.models import EmbeddedChunk, ParsedDocument
from app.domain.ports.embedder_port import EmbedderPort
from app.domain.ports.parser_port import DocumentParserPort
from app.domain.ports.vector_store_port import VectorStorePort
from app.modules.ingestion.semantic_markdown_chunker import SemanticMarkdownChunker

logger = logging.getLogger(__name__)

class AcademicIngestionUseCase:
    def __init__(self, parser: DocumentParserPort, embedder: EmbedderPort, vector_store: VectorStorePort, chunker: SemanticMarkdownChunker) -> None:
        self.parser = parser
        self.embedder = embedder
        self.vector_store = vector_store
        self.chunker = chunker

    async def process_file(self, file_path: str, tenant_id: str) -> dict:
        if not file_path:
            return {"message": "File_path not found..."}
        
        parsed_doc: ParsedDocument = await self.parser.parse_file(file_path=file_path)

        if parsed_doc.status == "FAILED":
            logger.info("parser has been crashed due to unexpected error...")
            return {"status": "FAILED", "reason": "Parser crashed...."}

        # 2. Chunk the Markdown structurally
        chunks = self.chunker.chunk_document(parsed_doc)

        # 3. Batch generate dense vector embeddings across boundary interfaces
        vectors: list[list[float]] = await self.embedder.embed(user_query=chunks)

        if len(vectors) != len(parsed_doc.document_blocks):
            raise ValueError(f"Embedder payload length mismatch. Expected {len(parsed_doc.document_blocks)} "f"vectors, but received {len(vectors)}.")

        chunks_to_ingest: list[EmbeddedChunk] = []
        for index, block in enumerate(parsed_doc.document_blocks):
            chunk = EmbeddedChunk(
                chunk_index=index,
                text=chunks[index].content,
                vector=vectors[index],
                metadata=parsed_doc.metadata
            )
            chunks_to_ingest.append(chunk)

        await self.vector_store.upsert(chunks=chunks_to_ingest)
        return {"status": "SUCCESS", "chunks_ingested": len(chunks_to_ingest), "message":"Parsing and chunking complete.."}