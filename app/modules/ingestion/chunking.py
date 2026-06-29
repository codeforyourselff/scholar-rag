from typing import Iterator
from app.domain.models import DocumentChunk, DocumentMetaData

class TokenChunker:
    def __init__(self, chunk_size: int = 500, chunk_overlap:int = 50, model_name: str = "cl100k_base")-> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("The chunk_size is smaller than the chunk_overlap")
        
        self.chunk_size= chunk_size
        self.chunk_overlap= chunk_overlap
        self.encoder= model_name

    def chunk_stream(self, text_stream: Iterator[str], metadata: DocumentMetaData)-> Iterator[DocumentChunk]:
        __buffer_tokens: list[int] = []
        __chunk_index: int = 0

        for text_block in text_stream: 
            tokens = self.encoder.encode(text_block) 

            """Add the new tokens into the buffer"""
            __buffer_tokens.extend(tokens) 

            while len(__buffer_tokens) >= self.chunk_size: 
                __chunk_tokens = __buffer_tokens[:self.chunk_size] 
                __chunk_text = self.encoder.decode(__chunk_tokens)

                yield DocumentChunk(
                    text=__chunk_text,
                    metadata=metadata,
                    chunk_index=__chunk_index
                )
                __chunk_index = __chunk_index + 1
                
                __buffer_tokens = __buffer_tokens[self.chunk_size-self.chunk_overlap:]

        if __buffer_tokens:
            __chunk_text = self.encoder.decode(__buffer_tokens)
            if __chunk_text.strip():
                yield DocumentChunk(
                    text= __chunk_text,
                    metadata= metadata,
                    chunk_index= __chunk_index
                    )



