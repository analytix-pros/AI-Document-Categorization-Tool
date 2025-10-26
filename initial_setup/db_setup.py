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


# Insert sample data
now = get_utc_datetime()


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
        try:
            c.execute(f"SELECT COUNT(*) FROM {table_name}")
            if c.fetchone()[0] == 0:
                for row in insert["data"]:
                    values = []
                    for col in columns:
                        if col == "created_datetime" or col == "updated_datetime":
                            values.append(now)
                        elif col == "is_active":
                            values.append(1)
                        elif col.endswith("_uuid") and col in uuid_keys:
                            # Generate UUID using specified keys
                            uuid_input = "".join(
                                str(row.get(key, "")) if key != "vm_name" else row.get("vm_name", "")
                                for key in uuid_keys[col]
                            )
                            values.append(derive_uuid(uuid_input))
                        elif col in ["created_by", "updated_by"]:
                            values.append(derive_uuid("cameron"))
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