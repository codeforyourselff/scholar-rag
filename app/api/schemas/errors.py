# Exception and Error models to identify as pydantic
from pydantic import BaseModel

class ValidationErrorDetail(BaseModel):
    loc: list[str | int]
    msg: str
    type: str

class ErrorResponseModel(BaseModel):
    status_code: int
    error_code: str
    details: list[ValidationErrorDetail] | None = None