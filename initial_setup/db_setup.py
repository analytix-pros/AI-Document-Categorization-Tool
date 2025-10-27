"""Database setup script."""
import sys
import os
import sqlite3

# Set project root and change working directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(PROJECT_ROOT)

# Local imports
try:
    from initial_setup.config import *
    from config.config import FULL_DATABASE_FILE_PATH
    from database.db_models import create_connection
    from utils.utils_system_specs import get_hostname
    from utils.utils_uuid import derive_uuid
    from utils.utils import get_utc_datetime
except ImportError as e:
    print(f"ERROR: Failed to import required modules: {str(e)}")
    print("Ensure config.py, database/db_models.py, utils/utils.py, utils/utils_system_specs.py, and utils/utils_uuid.py exist.")
    sys.exit(1)

now = get_utc_datetime()


def lookup_uuid_from_db(conn, table_name, lookup_columns, row_data):
    """
    Look up a UUID from the database based on specified columns.
    
    Args:
        conn: Database connection
        table_name: Table to search in
        lookup_columns: List of column names to match
        row_data: Dictionary containing the data for lookup
        
    Returns:
        str: UUID if found, None otherwise
    """
    c = conn.cursor()
    
    # Build WHERE clause dynamically
    where_conditions = []
    params = []
    
    for col in lookup_columns:
        where_conditions.append(f"{col} = ?")
        params.append(row_data.get(col))
    
    where_clause = " AND ".join(where_conditions)
    uuid_column = f"{table_name[:-1] if table_name.endswith('s') else table_name}_uuid"
    
    query = f"SELECT {uuid_column} FROM {table_name} WHERE {where_clause}"
    
    try:
        c.execute(query, params)
        result = c.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"ERROR: Failed to lookup UUID from {table_name}: {str(e)}")
        return None


def setup_database():
    """Set up the SQLite database with tables and sample data."""
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
    except sqlite3.Error as e:
        print(f"ERROR: Failed to connect to database: {str(e)}")
        sys.exit(1)

    # Create tables and indexes
    for table in TABLES:
        try:
            c.execute(table["create"])
            conn.commit()
            print(f"INFO: Created table {table['name']} successfully")
        except sqlite3.OperationalError as e:
            print(f"ERROR: Failed to create table {table['name']}: {str(e)}")
            conn.close()
            sys.exit(1)
        except sqlite3.Error as e:
            print(f"ERROR: Unexpected error creating table {table['name']}: {str(e)}")
            conn.close()
            sys.exit(1)

        for index_name, index_sql in table["indexes"]:
            try:
                c.execute(index_sql)
                conn.commit()
                print(f"INFO: Created index {index_name} on {table['name']} successfully")
            except sqlite3.OperationalError as e:
                print(f"ERROR: Failed to create index {index_name} on {table['name']}: {str(e)}")
                conn.close()
                sys.exit(1)
            except sqlite3.Error as e:
                print(f"ERROR: Unexpected error creating index {index_name} on {table['name']}: {str(e)}")
                conn.close()
                sys.exit(1)

    # Process inserts from config.py
    for insert in INSERTS:
        table_name = insert["table"]
        columns = insert["columns"]
        uuid_keys = insert.get("uuid_keys", {})
        lookup_keys = insert.get("lookup_keys", {})
        
        try:
            c.execute(f"SELECT COUNT(*) FROM {table_name}")
            if c.fetchone()[0] == 0:
                # Sort data by hierarchy_level if it exists (for hierarchical tables)
                data_to_insert = insert["data"]
                if "hierarchy_level" in columns:
                    data_to_insert = sorted(data_to_insert, key=lambda x: x.get("hierarchy_level", 0))
                
                for row in data_to_insert:
                    values = []
                    
                    for col in columns:
                        if col == "created_datetime" or col == "updated_datetime":
                            values.append(now)
                        elif col == "is_active":
                            values.append(1)
                        elif col in ["created_by", "updated_by"]:
                            values.append(derive_uuid("cameron"))
                        elif col.endswith("_uuid") and col in lookup_keys:
                            # Lookup UUID from database
                            lookup_config = lookup_keys[col]
                            lookup_table = lookup_config["table"]
                            lookup_cols = lookup_config["lookup_columns"]
                            
                            # Build lookup data from special name columns
                            lookup_data = {}
                            for lookup_col in lookup_cols:
                                if lookup_col == "organization_uuid":
                                    lookup_data[lookup_col] = row.get("organization_uuid")
                                elif lookup_col == "name":
                                    # Use special name field (e.g., parent_category_name, stamps_name)
                                    name_key = f"{col.replace('_uuid', '')}_name"
                                    if col == "stamps_uuid":
                                        name_key = "stamps_name"
                                    lookup_data[lookup_col] = row.get(name_key)
                            
                            # Skip lookup if name is None
                            if lookup_data.get("name") is None:
                                values.append(None)
                            else:
                                looked_up_uuid = lookup_uuid_from_db(conn, lookup_table, lookup_cols, lookup_data)
                                values.append(looked_up_uuid)
                        elif col.endswith("_uuid") and col in uuid_keys:
                            # Generate UUID using specified keys
                            uuid_input_parts = []
                            for key in uuid_keys[col]:
                                if key == "vm_name":
                                    uuid_input_parts.append(row.get("vm_name", ""))
                                else:
                                    uuid_input_parts.append(str(row.get(key, "")))
                            uuid_input = "".join(uuid_input_parts)
                            values.append(derive_uuid(uuid_input))
                        else:
                            values.append(row.get(col, None if col.endswith("_uuid") else ""))
                    
                    try:
                        c.execute(
                            f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['?' for _ in columns])})",
                            values
                        )
                        conn.commit()
                        print(f"INFO: Inserted {table_name} {row.get('name', row.get('username', ''))}")
                    except sqlite3.IntegrityError as e:
                        print(f"ERROR: Failed to insert {table_name} {row.get('name', row.get('username', ''))}: {str(e)}")
                        conn.close()
                        sys.exit(1)
                    except sqlite3.Error as e:
                        print(f"ERROR: Unexpected error inserting {table_name} {row.get('name', row.get('username', ''))}: {str(e)}")
                        conn.close()
                        sys.exit(1)
            else:
                print(f"INFO: {table_name} table already contains data, skipping insert")
        except sqlite3.Error as e:
            print(f"ERROR: Unexpected error checking {table_name} table: {str(e)}")
            conn.close()
            sys.exit(1)

    try:
        conn.close()
        print("INFO: Database setup completed successfully")
    except sqlite3.Error as e:
        print(f"ERROR: Failed to close database connection: {str(e)}")
        sys.exit(1)