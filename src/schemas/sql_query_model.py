from pydantic import BaseModel
from typing import Any

class QueryRequest(BaseModel):
    file_uuid: str
    query: str

class QueryCheckResponse(BaseModel):
    ignore: bool
    reason: str

class QueryResponse(BaseModel):
    results: list[list[Any]]