from fastapi import FastAPI
import uuid
from fastapi.middleware.cors import CORSMiddleware
from src.schemas.sql_agent_state import SQLQueryState
from src.schemas.user_session_model import UserSession
from src.agents.llm_provider import OpenAILLMProvider
from src.data_analysis_assistant import DataAnalysisAssistant
import os
from dotenv import load_dotenv
load_dotenv()

def create_app():
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize the LLM provider
    llm_provider = OpenAILLMProvider(api_key=os.getenv("OPENAI_API_KEY"),
                                     model_name="gpt-4o",
                                     temperature=0.0,
                                     verbose=True)
    
    # Default sample data files
    default_csv_files = [
        "data/case_study_germany_sample.csv",
        "data/case_study_germany_treatment_costs_sample.csv"
    ]
    
    # Default table names
    default_table_names = [file.split("/")[-1].split(".")[0] for file in default_csv_files]

    @app.post("/create-user-session")
    async def create_user_session(username: str = "default", csv_files: list[str] = None):
        """Create a new user session with a unique project UUID."""
        project_uuid = str(uuid.uuid4())
        
        # Use provided csv_files or default ones
        files_to_load = csv_files if csv_files else default_csv_files
        table_names = [file.split("/")[-1].split(".")[0] for file in files_to_load]
        
        # Create assistant and load data
        assistant = DataAnalysisAssistant(project_uuid=project_uuid, llm_provider=llm_provider)
        db_path = assistant.load_data(files_to_load, table_names)
        
        return {
            "project_uuid": project_uuid,
            "db_path": db_path,
            "message": f"User session created for {username}"
        }

    @app.post("/chat-with-data")
    async def chat_with_data(request: UserSession):
        """Process a chat query with the data analysis assistant."""
        project_uuid = request.project_uuid
        
        # If no project UUID provided, create a new session
        if not project_uuid or project_uuid == "":
            print(f"Creating new user session for default user")
            session_response = await create_user_session(username="default")
            project_uuid = session_response["project_uuid"]
            print(f"Project UUID: {project_uuid}")
        
        # Create assistant instance for this project
        assistant = DataAnalysisAssistant(project_uuid=project_uuid, llm_provider=llm_provider)
        
        # Load data and ensure SQL agent is initialized
        try:
            # Construct the expected database path
            db_path = os.path.join(assistant.sqlite_handler.upload_dir, f"{project_uuid}.sqlite")
            if not os.path.exists(db_path):
                print(f"Loading default data for project {project_uuid}")
                db_path = assistant.load_data(default_csv_files, default_table_names)
            else:
                # Database exists but SQL agent might not be initialized
                print(f"Database exists for project {project_uuid}, initializing SQL agent")
                # Initialize SQL agent with existing database
                from src.agents.sql_agent import SQLAgent
                assistant.sql_agent = SQLAgent(db_path, sqlite_handler=assistant.sqlite_handler, llm_provider=llm_provider)
        except Exception as e:
            print(f"Error with database, loading default data: {e}")
            db_path = assistant.load_data(default_csv_files, default_table_names)
        
        # Process the query
        response = assistant.analyze_query(request.query, db_path)
        return response

    @app.get("/get-conversation-history")
    async def get_conversation_history(project_uuid: str):
        """Get conversation history for a specific project."""
        assistant = DataAnalysisAssistant(project_uuid=project_uuid, llm_provider=llm_provider)
        return assistant.get_conversation_history()

    return app

# Create the app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)