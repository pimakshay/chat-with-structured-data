import os
from src.data_analysis_assistant import DataAnalysisAssistant
from src.agents.llm_provider import OpenAILLMProvider
import uuid
from dotenv import load_dotenv
load_dotenv()


def main():
    """Main function demonstrating the data analysis assistant."""
    
    # Initialize the LLM provider
    llm_provider = OpenAILLMProvider(api_key=os.getenv("OPENAI_API_KEY"),
                                     model_name="gpt-4o",
                                     temperature=0.0,
                                     verbose=True)

    # generate project uuid
    project_uuid = "d3c4b61c-e7be-4d19-9e7a-d31810041b45"#str(uuid.uuid4())
    print(f"Project UUID: {project_uuid}")

    # Initialize the assistant
    assistant = DataAnalysisAssistant(project_uuid=project_uuid, llm_provider=llm_provider)
    
    # Load the sample data
    csv_files = [
        "data/case_study_germany_sample.csv",
        "data/case_study_germany_treatment_costs_sample.csv"
    ]
    
    # generate table names from the csv files
    table_names = [file.split("/")[-1].split(".")[0] for file in csv_files]
    db_path = assistant.load_data(csv_files, table_names)
    
    # Example queries from the problem statement
    example_queries = [
        "How are you doing?",
        # "What are the average yearly therapy costs in Non-small cell lung cancer?",
        "Which active substances were also part of the appropriate comparative therapies?",
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
        if result.ignore:
            print(f"   Reason: {result.reason_for_ignoring}")
            print(f"   Suggestion: {result.suggestion_for_fixing}")
            continue
        print(f"   Result: {result}")

        print(f"================================================")
        print(f"Query: {result.user_query}")
        print(f"Output Response: {result.output_response_to_user}")
        print(f"Visualization Type: {result.visualizationType.visualization}")
        print(f"================================================")
    
    print(f"\n Conversation history: {len(assistant.get_conversation_history())} queries processed")

if __name__ == "__main__":
    main()
