from pydantic import BaseModel
from src.schemas.sql_agent_state import SQLQueryState

class UserSession(BaseModel):
    project_uuid: str = None
    query: str = None