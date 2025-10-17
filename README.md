# Chat with Structured Data

An agentic data analyst that converts natural language questions into SQL queries and automatically generates visualizations from tabular data.

## Overview

This system provides a local-first solution for interactive data analysis through natural language. It processes CSV files, converts them to SQLite databases, and uses LLM-powered agents to generate SQL queries, execute them, and create appropriate visualizations.

## Approach

### Text-to-SQL Agentic Workflow

We chose a simplified agentic workflow over a hierarchical multi-agent system for ease of implementation and maintenance:

**Current Implementation:**
```
User Query → Query Validation → SQL Generation → Execution → Visualization
```

**Alternative: Hierarchical Multi-Agent System (Future Enhancement)**
- Planner Agent: Orchestrates analysis tasks
- Supervisor Agent: Coordinates between agents
- SQL Agent: Handles query generation and execution
- Data Formatter Agent: Prepares visualization data
- Visualizer Agent: Creates charts and plots

### Tradeoffs

| Approach | Pros | Cons |
|----------|------|------|
| **Text-to-SQL** | Scalable, well-established, cloud-ready | Requires SQL knowledge, depends on agent accuracy |
| Text-to-Embedding | Semantic understanding | Loses data exactness |
| Text-to-Pandas | Direct manipulation | Poor multi-user scaling, memory intensive |

## Architecture

```
src/
├── agents/              # LLM-based agents
│   ├── llm_provider.py
│   ├── query_preprocessor_agent.py
│   └── sql_agent.py
├── data_handler/        # SQLite operations
│   ├── sqlite_handler.py
│   └── utils.py
├── vis/                 # Visualization
│   ├── plotter.py
│   ├── data_formatter.py
│   └── graph_instructions.py
└── schemas/             # Data models
```

## Key Components

- **DataAnalysisAssistant**: Main orchestrator that coordinates the analysis pipeline
- **SQLAgent**: Handles query parsing, SQL generation, and execution
- **SimplePlotter**: Automatically generates charts based on data characteristics
- **SQLiteHandler**: Converts CSV files to SQLite databases with proper schema handling

## Installation

```bash
# Clone and setup
uv sync

# Activate environment
source .venv/bin/activate

# Set up environment variables
cp .env.example .env
# Add your OPENAI_API_KEY to .env
```

## Usage

### CLI Mode
```bash
python main.py
```

### API Mode (Recommended)
```bash
python main_routes.py
```

**Available Endpoints:**
- `POST /create-user-session` - Create new analysis session
- `POST /chat-with-data` - Process natural language queries
- `GET /get-conversation-history` - Retrieve session history

### Example Queries

**Sample Data:** `case_study_germany_sample.csv`
- "Which active substances were also part of the appropriate comparative therapies?"
- "Show me the distribution of additional benefit ratings as a pie chart"

**Sample Data:** `case_study_germany_treatment_costs_sample.csv`
- "What are the average yearly therapy costs in Non-small cell lung cancer?"

### Example Response

```json
{
  "ignore": false,
  "user_query": "Which active substances were also part of the appropriate comparative therapies?",
  "query_parse_response": {
    "is_relevant": true,
    "relevant_tables": [
      {
        "table_name": "case_study_germany_sample",
        "columns": ["active_substance", "appropriate_comparative_therapy"],
        "noun_columns": ["active_substance"]
      }
    ]
  },
  "generated_sql_query": "SELECT `active_substance`, COUNT(*) as count FROM case_study_germany_sample WHERE `active_substance` IS NOT NULL AND `active_substance` != \"\" AND `active_substance` != \"N/A\" GROUP BY `active_substance` ORDER BY count DESC LIMIT 1",
  "results": [["pembrolizumab", 8]],
  "visualizationType": {
    "visualization": "bar",
    "visualization_reasoning": "Bar graph suitable for comparing categorical data frequency"
  },
  "formatted_data_for_visualization": {
    "formatted_data_for_visualization": {
      "labels": ["pembrolizumab"],
      "values": [{"data": [8], "label": "Occurrences in Comparative Therapies"}]
    }
  },
  "output_response_to_user": "The active substance pembrolizumab was also part of the appropriate comparative therapies."
}
```

## Output

- **JSON Responses**: Complete analysis results with SQL queries, data, and visualization metadata
- **Auto-generated Plots**: Saved to `output/{project_uuid}/` directory
- **Supported Charts**: Bar, pie, line, and scatter plots with professional styling

## Scalability Considerations

- **Database Migration**: SQLite → PostgreSQL/BigQuery for production scaling
- **Multi-user Support**: Project UUIDs enable concurrent user sessions
- **Stateless Design**: API endpoints support horizontal scaling
- **Caching**: Query results can be cached for improved performance

## Next Steps

- **SQL Query Validation**: Implement syntax checking and retry logic
- **User Sessions**: Project reloading and session persistence
- **Export Functionality**: PDF/DOCX report generation
- **Chat History**: Context-aware conversations with memory
- **Enhanced Error Handling**: Better error messages and recovery
- **Hierarchical Multi-Agent System**: Advanced orchestration for complex analyses