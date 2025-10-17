import os
from src.data_handler.sqlite_handler import SQLiteHandler, convert_multiple_csvs_to_sqlite
from src.agents.query_preprocessor_agent import check_if_query_is_related_to_data, preprocess_query

class DataAnalysisAssistant:
    """Agentic data analyst that converts natural language questions into analytics on tabular data."""
    
    def __init__(self, upload_dir: str = "uploads"):
        self.sqlite_handler = SQLiteHandler(upload_dir)
        self.conversation_history = []
    
    def load_data(self, csv_file_paths: list[str], table_names: list[str] = None) -> str:
        """Load multiple CSV files into a single SQLite database."""
        db_path = convert_multiple_csvs_to_sqlite(
            csv_file_paths, 
            table_names=table_names
        )
        print(f"✅ Data loaded into database: {db_path}")
        return db_path
    
    def analyze_query(self, user_query: str, db_path: str) -> dict:
        """Process a natural language query and return analysis results."""
        
        # Check if query is related to data analysis
        query_check = check_if_query_is_related_to_data(user_query)
        if query_check.ignore:
            return {
                "ignore": True, 
                "reason": query_check.reason,
                "suggestion": "Please ask a question about the data, such as 'What are the average costs?' or 'Show me a chart of the distribution.'"
            }
        
        # Preprocess the query for clarity
        preprocessed_query = preprocess_query(user_query)
        
        # Store in conversation history
        self.conversation_history.append({
            "user_query": user_query,
            "preprocessed_query": preprocessed_query
        })
        
        # For now, return a placeholder response
        # TODO: Implement actual query processing and code generation
        return {
            "query": preprocessed_query,
            "status": "processed",
            "message": "Query processed successfully. Analysis implementation coming soon.",
            "conversation_length": len(self.conversation_history)
        }
    
    def get_conversation_history(self) -> list:
        """Get the conversation history."""
        return self.conversation_history

def main():
    """Main function demonstrating the data analysis assistant."""
    
    # Initialize the assistant
    assistant = DataAnalysisAssistant()
    
    # Load the sample data
    csv_files = [
        "data/case_study_germany_sample.csv",
        "data/case_study_germany_treatment_costs_sample.csv"
    ]
    
    table_names = ["germany_sample", "treatment_costs"]
    db_path = assistant.load_data(csv_files, table_names)
    
    # Example queries from the problem statement
    example_queries = [
        "What are the average yearly therapy costs in Non-small cell lung cancer?",
        "Which active substances were also part of the appropriate comparative therapies?",
        "Show me the range of yearly therapy costs by additional benefit rating",
        "Give me a distribution of additional benefit ratings as a pie chart",
        "Are there any products that received a higher benefit rating in a reassessment in the same disease area"
    ]
    
    print("\n" + "="*60)
    print("Data Analysis Assistant - Example Queries")
    print("="*60)
    
    for i, query in enumerate(example_queries, 1):
        print(f"\n{i}. Query: {query}")
        result = assistant.analyze_query(query, db_path)
        print(f"   Result: {result}")
    
    print(f"\n📊 Conversation history: {len(assistant.get_conversation_history())} queries processed")

if __name__ == "__main__":
    main()
