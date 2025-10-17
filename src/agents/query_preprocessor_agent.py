import os
from src.agents.llm_provider import OpenAILLMProvider
from src.schemas.sql_query_model import QueryCheckResponse

def check_if_query_is_related_to_data(user_query: str, llm_provider: OpenAILLMProvider) -> QueryCheckResponse:
    prompt = f"""You are a data analysis assistant. Check if the user's query is about data analysis, statistics, or insights from CSV data.

ACCEPT queries about:
- Data analysis, statistics, trends, patterns, averages, ranges, distributions
- Charts, graphs, visualizations, pie charts, bar charts, scatter plots
- Data filtering, grouping, aggregations, comparisons, correlations
- Medical/pharmaceutical data analysis (drugs, treatments, costs, benefits, assessments)
- Therapy costs, treatment costs, yearly costs, pricing analysis
- Active substances, brand names, disease areas, therapeutic areas
- Additional benefits, benefit ratings, comparative therapies
- Product assessments, reassessments, evaluations
- Export formats (CSV, Excel, PDF, DOCX)
- Follow-up questions referencing previous analysis
- Any question that asks for insights from tabular data

REJECT queries about:
- General conversation, weather, personal topics
- Non-data related questions
- Technical support unrelated to data
- Questions that don't involve analyzing data

IMPORTANT: All questions about medical data, therapy costs, drug analysis, benefit ratings, and pharmaceutical information should be ACCEPTED as they are data analysis queries.

User query: {user_query}"""
    
    response = llm_provider.with_structured_output(QueryCheckResponse)
    response = response.invoke(prompt)
    return response


def preprocess_query(user_query: str, llm_provider: OpenAILLMProvider) -> str:
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