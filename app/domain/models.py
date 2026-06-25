from typing import Any
from pydantic import BaseModel, Field
from pydantic import BaseModel, ConfigDict, Field
from app.config import Settings

class MetaData(BaseModel):
    model_config = ConfigDict(frozen=True,strict=True)

    file_name : str
    file_size : float
    file_extension: str
    file_source : str
    timestamp : str = Field(default_factory=str)
    character_encoding : str
    tags: list[str] = Field(default_factory=list)
    match_conditions: dict[str, Any] = Field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.file_name == "" or self.file_name == None:
            raise ValueError(f"File name should not be empty")
        if self.file_source == "" or self.file_source == None:
            raise ValueError(f"File source should not be empty")
        if self.timestamp is None:
            raise ValueError(f"Timestamp should not be empty")

class Point(BaseModel):
    model_config = ConfigDict(frozen=True,strict=True)

    point_id : str = Field(default_factory=str)
    vector : list[float] = Field(default_factory=list[float])
    MetaData : dict

    def __post_init__(self) -> None:
        if self.point_id is None:
            raise ValueError(f"PointId cannot be none")
        if self.vector != int(Settings.embedder.dim):
            raise ValueError(f"The vector size should match with embedder dim size")

class SearchResult(BaseModel):
    model_config = ConfigDict(frozen=True,strict=True)

    search_id : str
    score : float = Field(...)
    MetaData: dict[str, Any]

    def __post_init__(self) -> None:
        if self.search_id == "" or self.search_id == None:
            raise ValueError(f"Search id should not be empty")
        if self.score > 1.0 or self.score < 0.1:
            raise ValueError(f"Score should be between given range")
        

"""Future score for optional payload fileds (equality/ membership)"""
class Filter(BaseModel):
    pass