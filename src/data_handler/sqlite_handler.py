import pandas as pd
import os
import sqlite3
import uuid
from typing import List, Optional, Dict, Any
from pathlib import Path

from src.schemas.sql_query_model import QueryRequest, QueryResponse
from src.data_handler.utils import table_exists

UPLOAD_DIR = "uploads"


class SQLiteHandler:
    """A class to handle SQLite database operations for CSV file conversion."""
    
    def __init__(self, upload_dir: str = UPLOAD_DIR):
        """Initialize the SQLite handler with upload directory."""
        self.upload_dir = upload_dir
        self._ensure_upload_dir()
    
    def _ensure_upload_dir(self) -> None:
        """Create upload directory if it doesn't exist."""
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def _validate_file_format(self, file_path: str) -> str:
        """Validate file format and return the extension."""
        allowed_formats = ["csv", "xls", "xlsx"]
        file_extension = os.path.splitext(file_path)[1][1:].lower()
        
        if file_extension not in allowed_formats:
            raise ValueError(f"Invalid file format. Allowed formats are: {', '.join(allowed_formats)}")
        
        return file_extension
    
    def _read_csv_file(self, file_path: str) -> pd.DataFrame:
        """Read CSV file with appropriate parameters."""
        try:
            # Try with semicolon delimiter first (as seen in the sample files)
            df = pd.read_csv(file_path, delimiter=';', quoting=1, on_bad_lines='skip')
            if len(df.columns) == 1:
                # If only one column, try comma delimiter
                df = pd.read_csv(file_path, delimiter=',', on_bad_lines='skip')
            return df
        except Exception as e:
            raise RuntimeError(f"Error reading CSV file {file_path}: {str(e)}")
    
    def _read_excel_file(self, file_path: str) -> pd.DataFrame:
        """Read Excel file."""
        try:
            return pd.read_excel(file_path)
        except Exception as e:
            raise RuntimeError(f"Error reading Excel file {file_path}: {str(e)}")
    
    def _read_file(self, file_path: str) -> pd.DataFrame:
        """Read file based on its extension."""
        file_extension = self._validate_file_format(file_path)
        
        if file_extension == "csv":
            return self._read_csv_file(file_path)
        elif file_extension in ["xls", "xlsx"]:
            return self._read_excel_file(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    def _sanitize_table_name(self, name: str) -> str:
        """Sanitize table name to be SQLite compatible."""
        # Remove or replace invalid characters
        sanitized = "".join(c if c.isalnum() or c == '_' else '_' for c in name)
        # Ensure it starts with a letter or underscore
        if sanitized and not (sanitized[0].isalpha() or sanitized[0] == '_'):
            sanitized = f"table_{sanitized}"
        return sanitized or "unnamed_table"
    
    def convert_single_file_to_sqlite(self, file_path: str, table_name: Optional[str] = None) -> str:
        """Convert a single file to SQLite database."""
        # Generate UUID for the database file
        file_uuid = str(uuid.uuid4())
        db_path = os.path.join(self.upload_dir, f"{file_uuid}.sqlite")
        
        # Read the file
        df = self._read_file(file_path)
        
        # Generate table name if not provided
        if table_name is None:
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            table_name = self._sanitize_table_name(base_name)
        else:
            table_name = self._sanitize_table_name(table_name)
        
        # Convert to SQLite
        try:
            with sqlite3.connect(db_path) as conn:
                df.to_sql(table_name, conn, if_exists="replace", index=False)
            return db_path
        except Exception as e:
            raise RuntimeError(f"Error converting file to SQLite: {str(e)}")
    
    def convert_multiple_files_to_sqlite(self, file_paths: List[str], 
                                       output_db_path: Optional[str] = None,
                                       table_names: Optional[List[str]] = None) -> str:
        """Convert multiple files to a single SQLite database with separate tables."""
        if not file_paths:
            raise ValueError("No file paths provided")
        
        # Generate output database path if not provided
        if output_db_path is None:
            project_uuid = str(uuid.uuid4())
            output_db_path = os.path.join(self.upload_dir, f"{project_uuid}.sqlite")
        
        # Remove existing database if it exists
        if os.path.exists(output_db_path):
            os.remove(output_db_path)
        
        try:
            with sqlite3.connect(output_db_path) as conn:
                for i, file_path in enumerate(file_paths):
                    # Read the file
                    df = self._read_file(file_path)
                    
                    # Generate table name
                    if table_names and i < len(table_names):
                        table_name = self._sanitize_table_name(table_names[i])
                    else:
                        base_name = os.path.splitext(os.path.basename(file_path))[0]
                        table_name = self._sanitize_table_name(f"{base_name}_{i+1}")
                    
                    # Convert to SQLite table
                    df.to_sql(table_name, conn, if_exists="replace", index=False)
                    print(f"Created table '{table_name}' from file '{file_path}'")
            
            return output_db_path
            
        except Exception as e:
            raise RuntimeError(f"Error converting multiple files to SQLite: {str(e)}")
    
    def execute_query(self, db_path: str, query: str) -> List[List[Any]]:
        """Execute a SQL query on the database and return results."""
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                results = cursor.fetchall()
                return [list(row) for row in results]
        except sqlite3.Error as e:
            raise RuntimeError(f"SQL error: {e}")
    
    def get_table_info(self, db_path: str) -> Dict[str, List[str]]:
        """Get information about all tables in the database."""
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Get all table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                
                table_info = {}
                for table in tables:
                    # Get column information
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [row[1] for row in cursor.fetchall()]
                    table_info[table] = columns
                
                return table_info
        except sqlite3.Error as e:
            raise RuntimeError(f"Error getting table info: {e}")
    
    def cleanup_old_files(self, max_age_days: int = 7) -> None:
        """Clean up old database files."""
        # This is a placeholder for cleanup functionality
        # In a production environment, you might want to implement this
        pass


# Convenience functions for backward compatibility
def convert_csv_to_sqlite(file_path: str) -> str:
    """Convert a single CSV file to SQLite database."""
    handler = SQLiteHandler()
    return handler.convert_single_file_to_sqlite(file_path)


def convert_multiple_csvs_to_sqlite(file_paths: List[str], 
                                   output_db_path: Optional[str] = None,
                                   table_names: Optional[List[str]] = None) -> str:
    """Convert multiple CSV files to a single SQLite database."""
    handler = SQLiteHandler()
    return handler.convert_multiple_files_to_sqlite(file_paths, output_db_path, table_names)


async def execute_query(request: QueryRequest):
    """Execute a query on a database file."""
    handler = SQLiteHandler()
    db_path = os.path.join(UPLOAD_DIR, f"{request.file_uuid}.sqlite")
    results = handler.execute_query(db_path, request.query)
    return {"results": results}

def get_schema(db_path: str) -> str:
    """Get the schema of the database with sample data."""
    
    # Check if the database file exists
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Get the table schema from sqlite_master
            cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            schema_parts = []

            # Process each table and fetch its schema and example rows
            for table_name, create_statement in tables:
                schema_parts.append(f"Table: {table_name}")
                schema_parts.append(f"CREATE statement: {create_statement}")
                
                # Get column information
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns_info = cursor.fetchall()
                column_names = [col[1] for col in columns_info]
                schema_parts.append(f"Columns: {', '.join(column_names)}")
                schema_parts.append("")

                # Fetch sample rows from the table
                cursor.execute(f"SELECT * FROM '{table_name}' LIMIT 5;")
                rows = cursor.fetchall()
                if rows:
                    schema_parts.append("Sample data:")
                    # Add column headers
                    schema_parts.append(f"Row: {', '.join(column_names)}")
                    for i, row in enumerate(rows, 1):
                        schema_parts.append(f"Row {i}: {', '.join(str(cell) for cell in row)}")
                schema_parts.append("")  # Blank line between tables

            return "\n".join(schema_parts)
            
    except sqlite3.Error as e:
        raise RuntimeError(f"Error getting database schema: {e}")