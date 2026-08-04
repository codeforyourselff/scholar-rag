import tiktoken
from app.domain.models import Chunk, ParsedDocument

class SemanticMarkdownChunker:
    def __init__(self, chunk_size: int = 250, chunk_overlap:int = 50, model_name: str = "all-MiniLM-L6-v2") -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("The chunk_size is smaller than the chunk_overlap")
        
        self.chunk_size= chunk_size
        self.chunk_overlap= chunk_overlap
        self.encoder= tiktoken.get_encoding(model_name)

    def chunk_document(self, parsed_document: list[ParsedDocument ]) -> list[Chunk]:
        buffer_tokens = []
        chunk_index = 0 

        for text_block in parsed_document.document_blocks:
            tokens = self.encoder.encode(text_block.content, add_special_tokens=False)
            buffer_tokens.extend(tokens)

            while len(buffer_tokens) >= self.chunk_size:
                chunk_tokens = buffer_tokens[:self.chunk_size]
                chunk_text = self.encoder.decode(chunk_tokens)

                yield Chunk(chunk_id=f"{parsed_document.document_id}_{chunk_index}", document_id=parsed_document.document_id, content=chunk_text, token_count=len(chunk_tokens), page_range=[text_block.metadata.get("page_number", 0)])
                chunk_index += 1

                # Retain the last `chunk_overlap` tokens for the next chunk
                buffer_tokens = buffer_tokens[self.chunk_size - self.chunk_overlap:]