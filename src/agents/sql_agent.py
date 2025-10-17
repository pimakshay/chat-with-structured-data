import os
from src.agents.llm_provider import OpenAILLMProvider
from langchain_core.prompts import ChatPromptTemplate
from src.data_handler.sqlite_handler import get_schema, SQLiteHandler
from src.schemas.sql_query_model import QueryParseResponse, VisualizationTypeResponse
from src.schemas.sql_agent_state import SQLQueryState

from src.vis.data_formatter import DataFormatter

class SQLAgent:
    def __init__(self, db_path: str, sqlite_handler: SQLiteHandler = None, llm_provider: OpenAILLMProvider = None):
        self.sqlite_handler = sqlite_handler
        self.llm_provider = llm_provider
        self.db_path = db_path
        self.sql_query_state = SQLQueryState()
        self.data_formatter = DataFormatter(llm_provider=self.llm_provider)


    def parse_question(self, question: str) -> QueryParseResponse:
        """Parse user question and identify relevant tables and columns."""
        
        self.sql_query_state.user_query = question

        # Get the database schema
        schema = get_schema(self.db_path)

        prompt = ChatPromptTemplate.from_messages([
            ("system", '''You are a data analyst that can help summarize SQL tables and parse user questions about a database. 
        Given the question and database schema, identify the relevant tables and columns. 
        If the question is not relevant to the database or if there is not enough information to answer the question, set is_relevant to false and return an empty "relevant_tables" array.

        Your response should always be in the following JSON format:
        {{
            "is_relevant": boolean,
            "relevant_tables": [
                {{
                    "table_name": string,
                    "columns": [string],
                    "noun_columns": [string]
                }}
            ]
        }}

        If no relevant tables are found, return "is_relevant": false and an empty "relevant_tables" array.

        The "noun_columns" field should contain only the columns that are relevant to the question and contain nouns or names. For example, the column "brand_name" contains nouns relevant to the question "What are the top selling brands?", but the column "assessment_number" is not relevant because it does not contain a noun. Do not include columns that contain only numbers.
        '''),
            ("human", "===Database schema:\n{schema}\n\n===User question:\n{question}\n\nIdentify relevant tables and columns:")
        ])

        # Format the prompt with the schema and question
        formatted_prompt = prompt.format(schema=schema, question=question)
        
        # Get structured output
        response = self.llm_provider.with_structured_output(QueryParseResponse)
        result = response.invoke(formatted_prompt)
        self.sql_query_state.query_parse_response = result
        return result

    def get_unique_nouns(self) -> dict:
        """Find unique nouns in relevant tables and columns."""

        if not self.sql_query_state.query_parse_response.is_relevant:
            return {"unique_nouns": []}

        unique_nouns = set()
        for table_info in self.sql_query_state.query_parse_response.relevant_tables:
            table_name = table_info.table_name
            noun_columns = table_info.noun_columns
            
            if noun_columns:
                column_names = ', '.join(f"`{col}`" for col in noun_columns)
                query = f"SELECT DISTINCT {column_names} FROM `{table_name}`"
                results = self.sqlite_handler.execute_query(self.db_path, query)
                for row in results:
                    unique_nouns.update(str(value) for value in row if value)

        return {"unique_nouns": list(unique_nouns)}

    def generate_sql(self) -> dict:
        """Generate SQL query based on parsed question and unique nouns."""

        question = self.sql_query_state.user_query
        parsed_question = self.sql_query_state.query_parse_response
        unique_nouns = self.sql_query_state.unique_nouns
        schema = get_schema(self.db_path)

        prompt = ChatPromptTemplate.from_messages([
            ("system", '''
You are an AI assistant that generates SQL queries based on user questions, database schema, and unique nouns found in the relevant tables. Generate a valid SQL query to answer the user's question.

If there is not enough information to write a SQL query, respond with "NOT_ENOUGH_INFO".

Here are some examples:

1. What are the average yearly therapy costs in Non-small cell lung cancer?
Answer: SELECT yearly_price_avg_today_apu, COUNT(*) as count FROM treatment_costs WHERE yearly_price_avg_today_apu IS NOT NULL AND yearly_price_avg_today_apu != "" AND yearly_price_avg_today_apu != "N/A" GROUP BY yearly_price_avg_today_apu ORDER BY count DESC LIMIT 1

2. Which active substances were also part of the appropriate comparative therapies?
Answer: SELECT \`active_substance\`, COUNT(*) as count FROM germany_sample WHERE \`active_substance\` IS NOT NULL AND \`active_substance\` != "" AND \`active_substance\` != "N/A" GROUP BY \`active_substance\`  ORDER BY count DESC LIMIT 1

3. Show me the range of yearly therapy costs by additional benefit rating.
Answer: SELECT \`additional_benefit_rating\`, MIN(yearly_price_avg_today_apu) as min_cost, MAX(yearly_price_avg_today_apu) as max_cost FROM treatment_costs WHERE \`additional_benefit_rating\` IS NOT NULL AND \`additional_benefit_rating\` != "" AND \`additional_benefit_rating\` != "N/A" GROUP BY \`additional_benefit_rating\`  ORDER BY min_cost DESC LIMIT 1

4. Give me a distribution of additional benefit ratings as a pie chart.
Answer: SELECT \`additional_benefit_rating\`, COUNT(*) as count FROM treatment_costs WHERE \`additional_benefit_rating\` IS NOT NULL AND \`additional_benefit_rating\` != "" AND \`additional_benefit_rating\` != "N/A" GROUP BY \`additional_benefit_rating\`  ORDER BY count DESC LIMIT 1

THE RESULTS SHOULD ONLY BE IN THE FOLLOWING FORMAT, SO MAKE SURE TO ONLY GIVE TWO OR THREE COLUMNS:
[[x, y]]
or 
[[label, x, y]]
             
For questions like "plot a distribution of the additional benefit ratings for each disease area", 
count the frequency of each additional benefit rating per disease area. 
The x-axis should represent the category (e.g., additional_benefit), and the y-axis should represent the count.

SKIP ALL ROWS WHERE ANY COLUMN IS NULL or "N/A" or "".
Just give the query string. Do not format it. Make sure to use the correct spellings of nouns as provided in the unique nouns list. All the table and column names should be enclosed in backticks.
'''),
            ("human", '''===Database schema:
{schema}

===User question:
{question}

===Relevant tables and columns:
{parsed_question}

===Unique nouns in relevant tables:
{unique_nouns}

Generate SQL query string'''),
        ])

        formatted_prompt = prompt.format(schema=schema, question=question, parsed_question=parsed_question, unique_nouns=unique_nouns)
        response = self.llm_provider.invoke(formatted_prompt)
        
        if response.strip() == "NOT_ENOUGH_INFO":
            self.sql_query_state.ignore = True
            self.sql_query_state.reason_for_ignoring = "There is not enough information to write a SQL query"
            self.sql_query_state.suggestion_for_fixing = "Please provide more information to generate a SQL query."
            self.sql_query_state.generated_sql_query = "NOT_RELEVANT"
            return self.sql_query_state
        else:
            self.sql_query_state.ignore = False
            self.sql_query_state.generated_sql_query = response
            return self.sql_query_state


    def validate_and_format_sql(self, sql_query: str) -> str:
        """Validate and format the SQL query."""
        pass

    def execute_query(self) -> list:
        """Execute a SQL query on the database."""
        query = self.sql_query_state.generated_sql_query
        if query == "NOT_RELEVANT":
            self.sql_query_state.ignore = True
            self.sql_query_state.reason_for_ignoring = "There is not enough information to write a SQL query"
            self.sql_query_state.suggestion_for_fixing = "Please provide more information to generate a SQL query."
            self.sql_query_state.generated_sql_query = "NOT_RELEVANT"
            self.sql_query_state.results = "NOT_RELEVANT"
            return self.sql_query_state
        else:
            self.sql_query_state.ignore = False
            self.sql_query_state.results = self.sqlite_handler.execute_query(self.db_path, query)
            return self.sql_query_state

    def format_results(self) -> dict:
        """Format query results into a human-readable response."""
        question = self.sql_query_state.user_query
        results = self.sql_query_state.results
        if results == "NOT_RELEVANT":
            self.sql_query_state.ignore = True
            self.sql_query_state.reason_for_ignoring = "There is not enough information to answer the question"
            self.sql_query_state.suggestion_for_fixing = "Please provide more information to answer the question."
            self.sql_query_state.output_response_to_user = "Sorry, not enough information to answer the question."
            return self.sql_query_state

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an AI assistant that formats database query results into a human-readable response. Give a conclusion to the user's question based on the query results. Do not give the answer in markdown format. Only give the answer in one line."),
            ("human", "User question: {question}\n\nQuery results: {results}\n\nFormatted response:"),
        ])

        formatted_prompt = prompt.format(question=question, results=results)
        response = self.llm_provider.invoke(formatted_prompt)
        self.sql_query_state.output_response_to_user = response
        return self.sql_query_state

    def choose_visualization_type(self) -> dict:
        """Choose the visualization type based on the user's question and query results."""
        question = self.sql_query_state.user_query
        results = self.sql_query_state.results
        sql_query = self.sql_query_state.generated_sql_query
        if results == "NOT_RELEVANT":
            return {"visualization": "none", "visualization_reasoning": "No visualization needed for irrelevant questions."}

        prompt = ChatPromptTemplate.from_messages([
            ("system", '''
You are an AI assistant that recommends appropriate data visualizations. Based on the user's question, SQL query, and query results, suggest the most suitable type of graph or chart to visualize the data. If no visualization is appropriate, indicate that.

Available chart types and their use cases:
- Bar Graphs: Best for comparing categorical data or showing changes over time when categories are discrete and the number of categories is more than 2. Use for questions like "What are the sales figures for each product?" or "How does the population of cities compare? or "What percentage of each city is male?"
- Horizontal Bar Graphs: Best for comparing categorical data or showing changes over time when the number of categories is small or the disparity between categories is large. Use for questions like "Show the revenue of A and B?" or "How does the population of 2 cities compare?" or "How many men and women got promoted?" or "What percentage of men and what percentage of women got promoted?" when the disparity between categories is large.
- Scatter Plots: Useful for identifying relationships or correlations between two numerical variables or plotting distributions of data. Best used when both x axis and y axis are continuous. Use for questions like "Plot a distribution of the fares (where the x axis is the fare and the y axis is the count of people who paid that fare)" or "Is there a relationship between advertising spend and sales?" or "How do height and weight correlate in the dataset? Do not use it for questions that do not have a continuous x axis."
- Pie Charts: Ideal for showing proportions or percentages within a whole. Use for questions like "What is the market share distribution among different companies?" or "What percentage of the total revenue comes from each product?"
- Line Graphs: Best for showing trends and distributionsover time. Best used when both x axis and y axis are continuous. Used for questions like "How have website visits changed over the year?" or "What is the trend in temperature over the past decade?". Do not use it for questions that do not have a continuous x axis or a time based x axis.

Consider these types of questions when recommending a visualization:
1. Aggregations and Summarizations (e.g., "What is the average yearly therapy costs in Non-small cell lung cancer?" - Bar Graph)
2. Comparisons (e.g., "Which active substances were also part of the appropriate comparative therapies?" - Bar Graph)
3. Plotting Distributions (e.g., "Show me the range of yearly therapy costs by additional benefit rating." - Bar Graph)
4. Trends Over Time (e.g., "Give me a distribution of additional benefit ratings as a pie chart." - Pie Chart)

Provide your response in the following format:
Recommended Visualization: [Chart type or "None"]. ONLY use the following names: bar, horizontal_bar, line, pie, scatter, none
'''),
            ("human", '''
User question: {question}
SQL query: {sql_query}
Query results: {results}

Recommend a visualization:'''),
        ])

        formatted_prompt = prompt.format(question=question, sql_query=sql_query, results=results)
        response = self.llm_provider.with_structured_output(VisualizationTypeResponse)
        result = response.invoke(formatted_prompt)
        self.sql_query_state.visualizationType = result
        if result.visualization == "none":
            return self.sql_query_state
        else:
            self.sql_query_state.formatted_data_for_visualization = self.format_data_for_visualization()
            return self.sql_query_state


    def format_data_for_visualization(self) -> dict:
        """Format the data for visualization."""
        question = self.sql_query_state.user_query
        results = self.sql_query_state.results
        sql_query = self.sql_query_state.generated_sql_query
        visualization = self.sql_query_state.visualizationType
        return self.data_formatter.format_data_for_visualization(question=question, results=results, sql_query=sql_query, visualization=visualization)