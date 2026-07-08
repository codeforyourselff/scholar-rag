from pydantic import BaseModel, Field
from app.config import Settings, get_settings
from functools import lru_cache
from typing import Any

@lru_cache
def get_config() -> Settings:
    return get_settings()

class SearchQuery(BaseModel):
    query: str = Field(default_factory=str)
    limit: int = Field(default_factory=lambda: get_config().qdrant.search_limit)
    MetaData: dict[str,Any]

class IngestedDocument(BaseModel):
    file_name: str
    file_size: float
    file_extension: str
    file_source: str
    timestamp: str = Field(default_factory=str)
    character_encoding: str
    tags: list[str] = Field(default_factory=list)
    match_conditions: dict[str, Any] = Field(default_factory=dict)