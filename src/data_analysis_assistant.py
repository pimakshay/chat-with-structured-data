from numpy import False_
from src.data_handler.sqlite_handler import SQLiteHandler, convert_multiple_csvs_to_sqlite
from src.agents.query_preprocessor_agent import check_if_query_is_related_to_data, preprocess_query
from src.agents.sql_agent import SQLAgent
from src.agents.llm_provider import OpenAILLMProvider
from src.vis.data_formatter import DataFormatter

class DataAnalysisAssistant:
    """Agentic data analyst that converts natural language questions into analytics on tabular data."""
    
    def __init__(self, upload_dir: str = "uploads", llm_provider: OpenAILLMProvider = None):
        self.sqlite_handler = SQLiteHandler(upload_dir)
        self.llm_provider = llm_provider
        self.conversation_history = []
        self.sql_agent = None
        self.preprocess_query = False
        self.data_formatter = DataFormatter(llm_provider=self.llm_provider)

    def load_data(self, csv_file_paths: list[str], table_names: list[str] = None) -> str:
        """Load multiple CSV files into a single SQLite database."""
        db_path = self.sqlite_handler.convert_multiple_files_to_sqlite(
            file_paths=csv_file_paths, 
            table_names=table_names
        )
        print(f"Data loaded into database: {db_path}")
        
        # Initialize SQL agent with the database
        self.sql_agent = SQLAgent(db_path, sqlite_handler=self.sqlite_handler, llm_provider=self.llm_provider)
        return db_path
    
    def analyze_query(self, user_query: str, db_path: str) -> dict:
        """Process a natural language query and return analysis results."""
        
        # Check if query is related to data analysis
        query_check = check_if_query_is_related_to_data(user_query=user_query, llm_provider=self.llm_provider)
        if query_check.ignore:
            return {
                "ignore": True, 
                "reason": query_check.reason,
                "suggestion": "Please ask a question about the data, such as 'What are the average costs?' or 'Show me a chart of the distribution.'"
            }
        
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
                parse_result = self.sql_agent.parse_question(question=preprocessed_query)
                unique_nouns = self.sql_agent.get_unique_nouns(parsed_question=parse_result)
                sql_query = self.sql_agent.generate_sql(question=preprocessed_query, parsed_question=parse_result, unique_nouns=unique_nouns)
                executed_query = self.sql_agent.execute_query(query=sql_query['sql_query'])
                output_response = self.sql_agent.format_results(question=preprocessed_query, results=executed_query)
                visualization_type = self.sql_agent.choose_visualization_type(question=preprocessed_query, results=executed_query, sql_query=sql_query['sql_query'])
                
                # formatted_data_for_visualization = self.data_formatter.format_data_for_visualization(question=preprocessed_query, results=executed_query, sql_query=sql_query['sql_query'], visualization=visualization_type['visualization'])
                
                
                return {
                    "query": preprocessed_query,
                    "status": "processed",
                    "is_relevant": parse_result.is_relevant,
                    "relevant_tables": [table.table_name for table in parse_result.relevant_tables] if parse_result.relevant_tables else [],
                    "noun_columns": [col for table in parse_result.relevant_tables for col in table.noun_columns] if parse_result.relevant_tables else [],
                    "sql_query": sql_query['sql_query'],
                    "executed_query": executed_query,
                    "conversation_length": len(self.conversation_history),
                    "output_response": output_response,
                    "visualization_type": visualization_type,
                    # "formatted_data_for_visualization": formatted_data_for_visualization
                }
            except Exception as e:
                return {
                    "query": preprocessed_query,
                    "status": "error",
                    "error": str(e),
                    "conversation_length": len(self.conversation_history)
                }
        else:
            return {
                "query": preprocessed_query,
                "status": "no_sql_agent",
                "message": "SQL agent not initialized. Please load data first.",
                "conversation_length": len(self.conversation_history)
            }
    
    def get_conversation_history(self) -> list:
        """Get the conversation history."""
        return self.conversation_history