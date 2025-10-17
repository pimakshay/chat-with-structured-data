Create a local-first Python script that, an agentic data analyst, that turns natural‑language questions into analytics on tabular data, generates runnable Python code to produce charts/tables, conduct data analyses and can transform outputs (e.g., convert PDF → DOCX or translate a report) without re‑parsing the original CSV. It can also simply chat with the user and consider the chat history.

Data handling
1. clean csv data and store it in sqlite format
2. implement options to retrieve data through sql, 

Query Transformation and handling
1. Handle irrelevant queries like `How are you?`, `What's the weather etc`? 
2. preprocess query --> frame the query properly to extract correct features

Data extraction from csv
1. Identify relevant tables and corresponding columns
2. formulate sql query
3. execture sql query

Summarization and output
1. Produce response for the user query
2. Produce plottable data
2. Decide if output data should be plottable; charts, tables, etc
3. Produce visualizations 

User sessions and reloading
1. Save it in sessions so that user can reload the session
2. User should be able to export the sessions as pdf or docx


## Fixes required:
1. Validate the generated sql query. Correct it if syntax error. Once fixed, retry it. Otherwise ignore.
  Result: {'ignore': False, 'query': 'Show me the range of yearly therapy costs by additional benefit rating', 'status': 'error', 'error': 'SQL error: near "NOT_RELEVANT": syntax error', 'conversation_length': 1}