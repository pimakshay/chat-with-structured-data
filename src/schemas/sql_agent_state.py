from pydantic import BaseModel
from src.schemas.sql_query_model import QueryParseResponse, VisualizationTypeResponse

class SQLQueryState(BaseModel):
    ignore: bool = False
    reason_for_ignoring: str = ""
    suggestion_for_fixing: str = ""
    user_query: str = ""
    preprocessed_query: str = ""
    query_parse_response: QueryParseResponse = None
    unique_nouns: list = []
    generated_sql_query: str = ""
    results: list = []
    visualizationType: VisualizationTypeResponse = None
    formatted_data_for_visualization: dict = None
    output_response_to_user: str = None
