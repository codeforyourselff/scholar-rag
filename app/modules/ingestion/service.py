from typing import Iterator
from app.domain.models import DocumentChunk, DocumentMetaData, EmbeddedChunk
from app.domain.ports.embedder_port import EmbedderPort
from app.domain.ports.vector_store_port import VectorStorePort
from app.modules.ingestion.chunking import TokenChunker

class DocumentIngestionService:
    def __init__(self, embedder: EmbedderPort, vector_store: VectorStorePort, chunker: TokenChunker, batch_size: int) -> None:
        self.embedder: EmbedderPort = embedder
        self.vector_store:VectorStorePort = vector_store
        self.chunker:TokenChunker = chunker
        self.batch_size:int = batch_size

    async def process_and_upsert_batch(self, batch: list[DocumentChunk])-> int:
        """Helper to embed and upsert a single batch, returning the count."""
        if not batch:
            return 0

        __texts = [single_chunk.text for single_chunk in batch]
        __vectors = await self.embedder.embeded(chunks=__texts)
        __embedder_chunks = [EmbeddedChunk(**chunk.model_dump(),vector=vector) for chunk,vector in zip(batch,__vectors)]
        await self.vector_store.upsert(__embedder_chunks)
        return len(batch)
    
    async def execute(self,text_stream: Iterator[str],metadata:DocumentMetaData)-> int:
        """At these moment we are converting our text-stream"""
        __current_batch: list[DocumentChunk] = []
        __total_ingested: int = 0
        
        for single_batch in self.chunker.chunk_stream(text_stream=text_stream,metadata=metadata):
            __current_batch.append(single_batch)
            if len(__current_batch) == self.batch_size:
                __total_ingested += await self.process_and_upsert_batch(__current_batch)
                __current_batch.clear()

        if __current_batch:
            __total_ingested += await self.process_and_upsert_batch(__current_batch)
            __current_batch.clear()

        return __total_ingested
    