import os
from src.agents.llm_provider import OpenAILLMProvider
from src.schemas.sql_query_model import QueryCheckResponse

llm_provider = OpenAILLMProvider(api_key=os.getenv("OPENAI_API_KEY"), model_name="gpt-4o-mini")

def check_if_query_is_related_to_data(user_query: str) -> QueryCheckResponse:
    prompt = f"""You are a data analysis assistant. Check if the user's query is about data analysis, statistics, or insights from CSV data.

Accept queries about:
- Data analysis, statistics, trends, patterns
- Charts, graphs, visualizations
- Data filtering, grouping, aggregations
- Comparisons, correlations, distributions
- Export formats (CSV, Excel, PDF, DOCX)
- Follow-up questions referencing previous analysis

Reject queries about:
- General conversation, weather, personal topics
- Non-data related questions
- Technical support unrelated to data

User query: {user_query}"""
    
    response = llm_provider.with_structured_output(QueryCheckResponse)
    response = response.invoke(prompt)
    return response


def preprocess_query(user_query: str) -> str:
    prompt = f"""You are a data analysis assistant. Preprocess the user's query to be clear and actionable for data analysis.

Tasks:
- Clarify ambiguous data analysis requests
- Extract specific metrics, filters, or comparisons needed
- Identify the type of analysis (statistical, visual, export)
- Preserve context from previous questions if referenced

User query: {user_query}

Return a clear, specific query ready for data analysis:"""
    
    response = llm_provider.invoke(prompt)
    return response