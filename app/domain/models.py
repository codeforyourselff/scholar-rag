import uuid
from enum import StrEnum
from typing import Any, Dict, List
from pydantic import BaseModel, Field, ConfigDict, computed_field, model_validator

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

# class DocumentMetaData(BaseModel):
#     model_config = ConfigDict(frozen=True)
#     source_id: str = Field(...)
#     source_type:SourceType
#     title: str | None = None
#     authors: list[str] | None = Field(default_factory=list, description="List of author names.")
#     abstract:str = Field(default="", max_length=5000)

"""This model represents a chunk of a document, which is a smaller segment of the original document."""
class DocumentChunk(BaseModel):
    chunk_id: str = Field(...,min_length=1)
    content: str = Field(...,min_length=1)
    metadata: Dict[str,Any] = Field(default_factory=dict)

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
    page="page"

class DocumentBlock(BaseModel):
    page_number: int
    markdown: str
    metadata: dict = Field(default_factory=dict)

class Citation(BaseModel):
    inline_marker: str = Field(description="e.g., [1] or (Smith, 2022)")
    raw_reference: str = Field(description="The full bibliography text entry")
    page_number: int | None = Field(default=None, gt=0)

class DocumentMetaData(BaseModel):
    confidence_score: float = Field(ge=0.0, le=1.0)
    pages_recovered: int = Field(ge=0)
    parser_exit_code: int

class ParsedDocument(BaseModel):
    document_id: str = Field(min_length=1)
    blocks: List[DocumentBlock]
    is_partial: bool = False

class Chunk(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    token_count: int
    page_range: list[int]