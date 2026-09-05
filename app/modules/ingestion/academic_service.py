import os
import logging
from app.domain.models import ParsedDocument
from app.domain.ports.parser_port import DocumentParserPort

logger = logging.getLogger(__name__)

class AcademicIngestionUseCase:
    def __init__(self,parser:DocumentParserPort) -> None:
        self.parser = parser

    def process_file(self, file_path: str, document_id: str) -> dict:
        logger.info(f"Starting ingestion orchestration for document {document_id}")

        # Pre-flight check if the file exists at the given file_path. If not, raise a FileNotFoundError.
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"Cannot find pdf file at {file_path}")

        try:
            # 1. Parse the document using the provided parser
            parsed_doc: ParsedDocument = self.parser.parse_file(file_path=file_path, document_id=document_id)

            logger.info(f"Successfully parsed document {document_id}. Total blocks extracted: {len(parsed_doc.blocks)}")
            logger.info(f"Document {parsed_doc}")

            if parsed_doc.is_partial:
                logger.warning(f"Partial parsing detected for document {document_id}. Some pages may not have been processed correctly.")

            # Here we will call the semantic chunker
            # 2. Chunk the parsed document into smaller blocks for semantic processing
            # 3. Store the chunks in the vector store for semantic search and retrieval
            # chunks = self.semantic_chunker.chunk(parsed_doc)

            # chunk_count = len(chunks)
            # logger.info(f"Successfully processed document {document_id}. Total chunks created: {chunk_count}")


        finally:
            # Cleanup: Remove the file after processing to free up space
            try:
                os.remove(file_path)
                logger.info(f"Successfully removed the file {file_path} after processing.")
            except Exception as e:
                logger.error(f"Failed to remove the file {file_path}. Error: {e}")
        return {"document_id": document_id, "status": "processed", "is_partial": parsed_doc.is_partial, "total_blocks": len(parsed_doc.blocks)}