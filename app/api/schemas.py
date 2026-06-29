from app.config import Settings, get_settings
from functools import lru_cache
from typing import Any
from pydantic import Field
from openai import BaseModel

@lru_cache
def get_config() -> Settings:
    return get_settings()

class SearchQuery(BaseModel):
    query: list[float]
    limit: int = Field(default_factory=lambda: get_config().qdrant.search_limit)
    MetaData: dict[str,Any]