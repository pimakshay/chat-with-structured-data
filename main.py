import os
from src.data_handler.sqlite_handler import SQLiteHandler, convert_multiple_csvs_to_sqlite
from src.agents.query_preprocessor_agent import check_if_query_is_related_to_data, preprocess_query
from src.agents.sql_agent import SQLAgent
from src.data_analysis_assistant import DataAnalysisAssistant
from src.agents.llm_provider import OpenAILLMProvider

from dotenv import load_dotenv
load_dotenv()


def main():
    """Main function demonstrating the data analysis assistant."""
    
    # Initialize the LLM provider
    llm_provider = OpenAILLMProvider(api_key=os.getenv("OPENAI_API_KEY"),
                                     model_name="gpt-4o",
                                     temperature=0.0,
                                     verbose=True)

    # Initialize the assistant
    assistant = DataAnalysisAssistant(llm_provider=llm_provider)
    
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
        # "Which active substances were also part of the appropriate comparative therapies?",
        # "Show me the range of yearly therapy costs by additional benefit rating",
        # "Give me a distribution of additional benefit ratings as a pie chart",
        # "Are there any products that received a higher benefit rating in a reassessment in the same disease area"
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
