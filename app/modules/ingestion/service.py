from pathlib import Path
from app.config import Settings
from app.domain.ports.embedder import EmbedderPort
from app.domain.ports.vector_store_port import VectorStorePort
from app.modules.ingestion.chunking import TokenChunker
from app.modules.ingestion.loaders import TextStreamingLoader

class DocumentIngestionService:
    def __init__(self, embedder: EmbedderPort, vector_store: VectorStorePort, chunker: TokenChunker) -> None:
        self.embedder = embedder
        self.vector_store = vector_store
        self.chunker = chunker
        self.batch_size: int = Settings.embedder.batch_size

    async def execute(self,file_path: str | Path)-> int:
        """First we load the file into loader function"""
        __loader = TextStreamingLoader(file_path)

        """get the metadata from the module"""
        __metadata = __loader.get_metadata()
        """Send the request to process the text-stream into our iterator"""
        __text_stream = __loader.stream_text()

        """At these moment we are converting our text-stream"""
        __current_batch: list = []
        __embedded_chunks: list = []
        total_ingested: int = 0
        
        for single_batch in self.chunker.chunk_stream(text_stream=__text_stream,metadata=__metadata):
            __current_batch.append(single_batch)
            if len(__current_batch) == self.batch_size:
                __embedded_chunks = self.embedder.embed_chunks(chunks=__current_batch)
                await self.vector_store.upsert(__embedded_chunks)
                total_ingested = total_ingested + 1
                __current_batch.clear()
                __embedded_chunks.clear()

        if __current_batch:
            __embedded_chunks = self.embedder.embed_chunks(chunks=__current_batch)
            await self.vector_store.upsert(__embedded_chunks)
            total_ingested = total_ingested + 1
        
        return total_ingested


    