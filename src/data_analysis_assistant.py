from numpy import False_
from src.data_handler.sqlite_handler import SQLiteHandler
from src.agents.query_preprocessor_agent import check_if_query_is_related_to_data, preprocess_query
from src.agents.sql_agent import SQLAgent
from src.agents.llm_provider import OpenAILLMProvider
from src.vis.data_formatter import DataFormatter
from src.agents.sql_agent import SQLQueryState

class DataAnalysisAssistant:
    """Agentic data analyst that converts natural language questions into analytics on tabular data."""
    
    def __init__(self, project_uuid: str, upload_dir: str = "uploads", llm_provider: OpenAILLMProvider = None):
        self.project_uuid = project_uuid
        self.sqlite_handler = SQLiteHandler(upload_dir)
        self.llm_provider = llm_provider
        self.conversation_history = []
        self.sql_agent = None
        self.preprocess_query = False
        self.data_formatter = DataFormatter(llm_provider=self.llm_provider)

    def load_data(self, csv_file_paths: list[str], table_names: list[str] = None) -> str:
        """Load multiple CSV files into a single SQLite database."""
        db_path = self.sqlite_handler.convert_multiple_files_to_sqlite(
            project_uuid=self.project_uuid,
            file_paths=csv_file_paths, 
            table_names=table_names
        )
        print(f"Data loaded into database: {db_path}")
        
        # Initialize SQL agent with the database
        self.sql_agent = SQLAgent(db_path, sqlite_handler=self.sqlite_handler, llm_provider=self.llm_provider)
        return db_path
    
    def analyze_query(self, user_query: str, db_path: str) -> SQLQueryState:
        """Process a natural language query and return analysis results."""
        
        # Check if query is related to data analysis
        query_check = check_if_query_is_related_to_data(user_query=user_query, llm_provider=self.llm_provider)
        if query_check.ignore:
            self.sql_agent.sql_query_state.ignore = True
            self.sql_agent.sql_query_state.reason_for_ignoring = query_check.reason
            self.sql_agent.sql_query_state.suggestion_for_fixing = "Please ask a question about the data, such as 'What are the average costs?' or 'Show me a chart of the distribution.'"
            return self.sql_agent.sql_query_state
        
        # Preprocess the query for clarity
        if self.preprocess_query:
            preprocessed_query = preprocess_query(user_query=user_query, llm_provider=self.llm_provider)
        else:
            preprocessed_query = user_query
        
        # Store in conversation history
        self.conversation_history.append({
            "user_query": user_query,
            "preprocessed_query": preprocessed_query
        })
        
        # Use SQL agent to parse the question and identify relevant tables
        if self.sql_agent:
            try:
                # step 1: parse the question
                self.sql_agent.parse_question(question=preprocessed_query)
                # step 2: get the unique nouns
                self.sql_agent.get_unique_nouns()
                # step 3: generate the SQL query
                self.sql_agent.generate_sql()
                # step 4: execute the query
                self.sql_agent.execute_query()
                # step 5: format the results
                self.sql_agent.format_results()
                # step 6: choose the visualization type
                self.sql_agent.choose_visualization_type()

                return self.sql_agent.sql_query_state
            except Exception as e:
                self.sql_agent.sql_query_state.ignore = True
                self.sql_agent.sql_query_state.reason_for_ignoring = "Error in SQL agent"
                self.sql_agent.sql_query_state.suggestion_for_fixing = "Please try again later."
                self.sql_agent.sql_query_state.output_response_to_user = "Sorry, there was an error processing your question. Please try again later."
                return self.sql_agent.sql_query_state
        else:
            self.sql_agent.sql_query_state.ignore = True
            self.sql_agent.sql_query_state.reason_for_ignoring = "SQL agent not initialized. Please load data first."
            self.sql_agent.sql_query_state.suggestion_for_fixing = "Please load data first."
            self.sql_agent.sql_query_state.output_response_to_user = "Sorry, SQL agent not initialized. Please load data first."
            return self.sql_agent.sql_query_state
    
    def get_conversation_history(self) -> list:
        """Get the conversation history."""
        return self.conversation_history