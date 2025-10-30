# db_setup.py
import sys
import os
import sqlite3

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(PROJECT_ROOT)

try:
    from initial_setup.config import TABLES, INSERTS
    from config.config import FULL_DATABASE_FILE_PATH
    from database.db_models import create_connection
    from utils.utils_uuid import derive_uuid
    from utils.utils import get_utc_datetime
except ImportError as e:
    print(f"ERROR: Failed to import required modules: {str(e)}")
    sys.exit(1)

now = get_utc_datetime()

def generate_create_table_sql(table_def):
    """Generate CREATE TABLE SQL from structured table definition."""
    table_name = table_def["name"]
    columns = table_def["columns"]

    col_defs = []
    for col_name, col_config in columns.items():
        parts = [col_name, col_config["data_type"]]

        if col_config["primary_key"]:
            parts.append("PRIMARY KEY")
        if col_config["null_constraint"] == "NOT NULL":
            parts.append("NOT NULL")
        elif col_config["null_constraint"] == "NULL":
            parts.append("NULL")

        if col_config["column_default"] is not None:
            default_val = col_config["column_default"]
            if isinstance(default_val, str):
                default_val = f"'{default_val}'"
            parts.append(f"DEFAULT {default_val}")

        if col_config["is_unique"]:
            parts.append("UNIQUE")

        col_defs.append(" ".join(parts))

    # Add foreign keys
    fk_defs = table_def.get("foreign_keys", [])
    col_defs.extend(fk_defs)

    create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n    {', '.join(col_defs)}\n)"
    # print(f"Create SQL:\n{create_sql}")
    return create_sql

def setup_database():
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
    except sqlite3.Error as e:
        print(f"ERROR: Failed to connect to database: {str(e)}")
        sys.exit(1)

    # Create tables
    for table in TABLES:
        create_sql = generate_create_table_sql(table)
        try:
            c.execute(create_sql)
            conn.commit()
            print(f"INFO: Created table {table['name']} successfully")
        except sqlite3.Error as e:
            print(f"ERROR: Failed to create table {table['name']}: {str(e)}")
            conn.close()
            sys.exit(1)

        # Create indexes
        for index_name, index_sql in table.get("indexes", []):
            try:
                c.execute(index_sql)
                conn.commit()
                print(f"INFO: Created index {index_name} on {table['name']}")
            except sqlite3.Error as e:
                print(f"ERROR: Failed to create index {index_name}: {str(e)}")
                conn.close()
                sys.exit(1)

    # === INSERT SAMPLE DATA ===
    for insert in INSERTS:
        table_name = insert["table"]
        columns = insert["columns"]
        uuid_keys = insert.get("uuid_keys", {})
        lookup_keys = insert.get("lookup_keys", {})

        try:
            c.execute(f"SELECT COUNT(*) FROM {table_name}")
            if c.fetchone()[0] > 0:
                print(f"INFO: {table_name} already has data, skipping insert")
                continue

            # Sort hierarchical data
            data_to_insert = insert["data"]
            if any("hierarchy_level" in row for row in data_to_insert):
                data_to_insert = sorted(data_to_insert, key=lambda x: x.get("hierarchy_level", 0))

            for row in data_to_insert:
                values = []
                for col in columns:
                    if col in ["created_datetime", "updated_datetime"]:
                        values.append(now)
                    elif col == "is_active":
                        values.append(row.get(col, 1))
                    elif col in ["created_by", "updated_by"]:
                        values.append(derive_uuid(row.get(col, "cameron")))
                    elif col.endswith("_uuid") and col in lookup_keys:
                        # Handle lookup (same as before)
                        lookup_config = lookup_keys[col]
                        lookup_table = lookup_config["table"]
                        lookup_cols = lookup_config["lookup_columns"]
                        lookup_data = {}
                        for lc in lookup_cols:
                            key = f"{lc.replace('_uuid', '')}_name" if lc != "organization_uuid" else lc
                            lookup_data[lc] = row.get(key)
                        uuid = lookup_uuid_from_db(conn, lookup_table, lookup_cols, lookup_data)
                        values.append(uuid)
                    elif col.endswith("_uuid") and col in uuid_keys:
                        parts = [str(row.get(k, "")) for k in uuid_keys[col]]
                        values.append(derive_uuid("".join(parts)))
                    else:
                        values.append(row.get(col))

                try:
                    placeholders = ", ".join(["?"] * len(columns))
                    c.execute(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})", values)
                    conn.commit()
                    print(f"INFO: Inserted into {table_name}: {row.get('name', row.get('username', 'record'))}")
                except sqlite3.IntegrityError as e:
                    print(f"ERROR: Integrity error inserting into {table_name}: {str(e)}")
                    conn.close()
                    sys.exit(1)
        except sqlite3.Error as e:
            print(f"ERROR: Unexpected DB error in {table_name}: {str(e)}")
            conn.close()
            sys.exit(1)

    conn.close()
    print("INFO: Database setup completed successfully")

# Reuse your existing lookup function
def lookup_uuid_from_db(conn, table_name, lookup_columns, row_data):
    c = conn.cursor()
    where_parts = [f"{col} = ?" for col in lookup_columns]
    params = [row_data.get(col) for col in lookup_columns]
    uuid_col = f"{table_name[:-1] if table_name.endswith('s') else table_name}_uuid"
    query = f"SELECT {uuid_col} FROM {table_name} WHERE {' AND '.join(where_parts)}"
    try:
        c.execute(query, params)
        result = c.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"ERROR: Lookup failed: {str(e)}")
        return None

if __name__ == "__main__":
    setup_database()