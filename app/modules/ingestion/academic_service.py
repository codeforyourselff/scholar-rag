from app.domain.models import DocumentBlock, EmbeddedChunk, ParsedDocument
from app.domain.ports.embedder_port import EmbedderPort
from app.domain.ports.parser_port import DocumentParserPort
from app.domain.ports.vector_store_port import VectorStorePort

class AcademicIngestionUseCase:
    def __init__(self, parser: DocumentParserPort, embedder: EmbedderPort, vector_store: VectorStorePort) -> None:
        self.parser = parser
        self.embedder = embedder
        self.vector_store = vector_store

    def _format_semantic_block(self, block: DocumentBlock) -> str:
        # Enforce exact string representation of the BlockType enum value
        type_prefix = str(block.type.value).upper()
        return f"Type: {type_prefix}\nContent: {block.text}"

    async def process_file(self, file_path: str) -> int:
        parsed_doc:ParsedDocument = await self.parser.parse(file_path=file_path)

        if not parsed_doc.document_blocks:
            return 0

        formatted_texts: list[str] = [
            self._format_semantic_block(block) 
            for block in parsed_doc.document_blocks
        ]

        # 3. Batch generate dense vector embeddings across boundary interfaces
        vectors: list[list[float]] = await self.embedder.embed(user_query=formatted_texts)

        if len(vectors) != len(parsed_doc.document_blocks):
            raise ValueError(f"Embedder payload length mismatch. Expected {len(parsed_doc.document_blocks)} "f"vectors, but received {len(vectors)}.")

        chunks_to_ingest: list[EmbeddedChunk] = []
        for index, block in enumerate(parsed_doc.document_blocks):
            chunk = EmbeddedChunk(
                chunk_index=index,
                text=formatted_texts[index],
                vector=vectors[index],
                metadata=parsed_doc.metadata
            )
            chunks_to_ingest.append(chunk)

        await self.vector_store.upsert(chunks=chunks_to_ingest)
        return len(chunks_to_ingest)