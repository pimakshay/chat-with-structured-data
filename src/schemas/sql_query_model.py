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


class RelevantTable(BaseModel):
    table_name: str
    columns: list[str]
    noun_columns: list[str]

class QueryParseResponse(BaseModel):
    is_relevant: bool
    relevant_tables: list[RelevantTable]

class VisualizationTypeResponse(BaseModel):
    visualization: str
    visualization_reasoning: str