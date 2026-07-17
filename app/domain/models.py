import hashlib
from typing import Any
from pydantic import BaseModel, Field, computed_field, model_validator
from pydantic import BaseModel, ConfigDict, Field

class SearchParams(BaseModel):
    model_config = ConfigDict(frozen=True)
    query: list[float]
    limit: int
    MetaData: dict[str,Any]

class SearchResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    search_id : str = Field(...)
    score : float = Field(...)
    MetaData: dict[str, Any]

    @model_validator(mode="after")
    def validate_search_result(self):
        if self.search_id == "" or self.search_id == None:
            raise ValueError(f"Search id should not be empty")
        if self.score > 1.0 or self.score < 0.1:
            raise ValueError(f"Score should be between given range")
        return self

class DocumentMetaData(BaseModel):
    model_config = ConfigDict(frozen=True)
    source_id: str = Field(...)
    title: str | None = None
    author: str | None = None

class DocumentChunk(BaseModel):
    text: str = Field(...,min_length=1)
    metadata: DocumentMetaData
    chunk_index: int = Field(...,ge=0)

    @computed_field
    def chunk_id(self) -> str:
        """The idempotency key"""
        unique_string=f"{self.metadata.source_id}_{self.chunk_index}_{self.text}"
        return hashlib.sha256(unique_string.encode("utf-8")).hexdigest()

class EmbeddedChunk(DocumentChunk):
    """A documentChunk augmented with its own vector representation"""
    vector:list[float] = Field(...)

class RAGResponseModel(BaseModel):
    answer: str
    used_chunks: list[EmbeddedChunk] = Field(default_factory=list)