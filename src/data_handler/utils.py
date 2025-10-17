

def table_exists(conn, table_name_prefix):
    cursor = conn.cursor()
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    has_cleaned_table = False
    for table in tables:
        table_name, create_statement = table
        if table_name_prefix in table_name:
            has_cleaned_table = True

    if has_cleaned_table is False:
        raise RuntimeError(f"Cleaned Table does not exist in the database")
    
    return True