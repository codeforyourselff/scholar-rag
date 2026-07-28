import uuid
from enum import StrEnum
from typing import Any
from pydantic import BaseModel, Field, ConfigDict, HttpUrl, computed_field, model_validator

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
    
class SourceType(StrEnum):
    PDF = "pdf"
    URL = "url"
    TEXT = "text"
    MARKDOWN = "markdown"

class DocumentMetaData(BaseModel):
    model_config = ConfigDict(frozen=True)
    source_id: str = Field(...)
    source_type:SourceType
    title: str | None = None
    authors: list[str] | None = Field(default_factory=list, description="List of author names.")
    abstract:str = Field(default="", max_length=5000)

class DocumentChunk(BaseModel):
    text: str = Field(...,min_length=1)
    metadata: DocumentMetaData
    chunk_index: int = Field(...,ge=0)

    @computed_field
    def chunk_id(self) -> str:
        """The idempotency key"""
        unique_string=f"{self.metadata.source_id}_{self.chunk_index}_{self.text}"
        return str(uuid.uuid5(uuid.NAMESPACE_OID, unique_string))

class EmbeddedChunk(DocumentChunk):
    """A documentChunk augmented with its own vector representation"""
    vector:list[float] = Field(...)

class RAGResponseModel(BaseModel):
    answer: str
    sources: list[EmbeddedChunk]

# Defined the models for parsing the files
class BlockType(StrEnum):
    heading="heading"
    paragraph="paragraph"
    equation="equation"
    table="table"

class DocumentBlock(BaseModel):
    type: BlockType
    text: str = Field(min_length=1)

class Citation(BaseModel):
    inline_text: str = Field(min_length=1)
    page_number:int | None = Field(default=None,gt=0)
    source_url:HttpUrl | None  = Field(default=None)

class ParsedDocument(BaseModel):
    document_id:str = Field(min_length=1)
    metadata:DocumentMetaData
    document_blocks: list[DocumentBlock] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)

