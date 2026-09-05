import re
import tiktoken
from typing import List, Iterator
from app.domain.models import DocumentBlock, DocumentChunk
from typing import Iterator

class SemanticMarkdownChunker:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", max_tokens: int = 250, overlap_tokens: int = 50) -> None:
        self.encoder = tiktoken.encoding_for_model(model_name)
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens

    def chunk_document(self,document_id: str, blocks: List[DocumentBlock]) -> List[DocumentChunk]:

        master_string = ""
        start = 0
        chunks = []

        for block in blocks:
            master_string = block.markdown + "\n\n"
            end = start + len(master_string)
            


        

        


