# db_setup.py
import sys
import os
import time
import sqlite3

# ─────────────────────────────────────────────────────────────────────────────
# Set project root and change working directory
# ─────────────────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(PROJECT_ROOT)

try:
    from initial_setup.config import TABLES, INSERTS, METADATA_FIELDS
    from config.config import FULL_DATABASE_FILE_PATH
    from database.db_models import create_connection
    from utils.utils_uuid import derive_uuid
    from utils.utils import get_utc_datetime
except ImportError as e:
    print(f"ERROR: Failed to import required modules: {str(e)}")
    sys.exit(1)

now = get_utc_datetime()


# ─────────────────────────────────────────────────────────────────────────────
# 1. Generate CREATE TABLE SQL (single-line, no \n in f-string)
# ─────────────────────────────────────────────────────────────────────────────
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

        if col_config["column_default"] is not None:
            default_val = col_config["column_default"]
            if isinstance(default_val, str):
                default_val = f"'{default_val}'"
            elif isinstance(default_val, bool):
                default_val = int(default_val)
            parts.append(f"DEFAULT {default_val}")

        if col_config["is_unique"]:
            parts.append("UNIQUE")

        col_defs.append(" ".join(parts))

    fk_defs = table_def.get("foreign_keys", [])
    col_defs.extend(fk_defs)

    column_sql = ", ".join(col_defs)
    create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({column_sql});"
    return create_sql


# ─────────────────────────────────────────────────────────────────────────────
# 2. Generic lookup: SELECT uuid_col FROM table WHERE col1=? AND col2=?
# ─────────────────────────────────────────────────────────────────────────────
def lookup_uuid_from_db(conn, table_name, uuid_column, match_columns, match_values):
    """
    Perform a lookup to resolve a foreign key UUID.
    Example:
        SELECT category_uuid FROM category WHERE organization_uuid=? AND name=?
    """
    c = conn.cursor()
    where = " AND ".join(f"{col} = ?" for col in match_columns)
    query = f"SELECT {uuid_column} FROM {table_name} WHERE {where}"
    try:
        c.execute(query, match_values)
        row = c.fetchone()
        if row:
            return row[0]
        else:
            print(f"WARNING: No match in {table_name} for {dict(zip(match_columns, match_values))}")
            return None
    except sqlite3.Error as e:
        print(f"ERROR: Lookup failed → {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 3. Main setup function
# ─────────────────────────────────────────────────────────────────────────────
def setup_database():
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
    except sqlite3.Error as e:
        print(f"ERROR: Failed to connect to database: {str(e)}")
        sys.exit(1)

    # ─────────────────────────────────────────────────────────────────────────
    # CREATE TABLES
    # ─────────────────────────────────────────────────────────────────────────
    for table in TABLES:
        create_sql = generate_create_table_sql(table)
        try:
            c.execute(create_sql)
            conn.commit()
            print(f"INFO: Created table {table['name']}")
        except sqlite3.Error as e:
            print(f"ERROR: Failed to create table {table['name']}: {str(e)}")
            conn.close()
            sys.exit(1)

        # Create indexes
        for index_name, index_sql in table.get("indexes", []):
            try:
                c.execute(index_sql)
                conn.commit()
                print(f"INFO: Created index {index_name}")
            except sqlite3.Error as e:
                print(f"ERROR: Failed to create index {index_name}: {str(e)}")
                conn.close()
                sys.exit(1)

    # ─────────────────────────────────────────────────────────────────────────
    # INSERT SAMPLE DATA
    # ─────────────────────────────────────────────────────────────────────────
    for insert in INSERTS:
        table_name   = insert["table"]
        columns      = insert["columns"]
        uuid_keys    = insert.get("uuid_keys", {})
        lookup_keys  = insert.get("lookup_keys", {})

        # Skip if table already has data
        try:
            c.execute(f"SELECT COUNT(*) FROM {table_name}")
            if c.fetchone()[0] > 0:
                print(f"INFO: {table_name} already has data – skipping inserts")
                continue
        except sqlite3.Error as e:
            print(f"ERROR: count check {table_name}: {e}")
            continue

        # Sort hierarchical data
        data_to_insert = insert["data"]
        if any("hierarchy_level" in row for row in data_to_insert):
            data_to_insert = sorted(
                data_to_insert,
                key=lambda r: r.get("hierarchy_level", 0)
            )

        # ─────────────────────────────────────────────────────────────────────
        # Process each row
        # ─────────────────────────────────────────────────────────────────────
        for row in data_to_insert:
            values       = []
            lookup_cache = {}

            # ─────────────────────────────────────────────────────────────────
            # 1. Resolve ALL lookup_keys FIRST
            # ─────────────────────────────────────────────────────────────────
            for col, cfg in lookup_keys.items():
                src_table   = cfg["source_table"]
                src_uuid    = cfg["source_derived_uuid"]
                match_cols  = cfg["source_matched_columns"]
                data_keys   = cfg["lookup_column_in_data"]   # ← LIST

                # If ANY data_key is None → NULL lookup
                params = []
                for src_col, data_key in zip(match_cols, data_keys):
                    val = row.get(data_key)
                    if val is None:
                        params = None
                        break
                    params.append(val)

                if params is None:
                    lookup_cache[col] = None
                    continue

                uuid = lookup_uuid_from_db(conn, src_table, src_uuid, match_cols, params)
                if uuid is None:
                    print(f"ERROR: lookup failed for {col} → {cfg} | row: {row}")
                    conn.close()
                    sys.exit(1)
                lookup_cache[col] = uuid

            # ─────────────────────────────────────────────────────────────────
            # 2. Build INSERT values
            # ─────────────────────────────────────────────────────────────────
            for col in columns:
                # ---- METADATA ------------------------------------------------
                if col in METADATA_FIELDS:
                    if col == "is_active":
                        values.append(row.get(col, METADATA_FIELDS[col]["column_default"]))
                    elif col in ("created_datetime", "updated_datetime"):
                        values.append(now)
                    elif col in ("created_by", "updated_by"):
                        user_ref = row.get(col)
                        if user_ref is None:
                            admin_uuid = lookup_uuid_from_db(conn, "user", "user_uuid", ["username"], ["cameron"])
                            values.append(admin_uuid or derive_uuid("cameron"))
                        else:
                            if isinstance(user_ref, str) and len(user_ref) == 36 and "-" in user_ref:
                                values.append(user_ref)
                            else:
                                uuid = lookup_uuid_from_db(conn, "user", "user_uuid", ["username"], [user_ref])
                                values.append(uuid or derive_uuid(user_ref))
                    else:
                        values.append(row.get(col))
                    continue

                # ---- RESOLVED LOOKUP -----------------------------------------
                if col in lookup_cache:
                    values.append(lookup_cache[col])
                    continue

                # ---- OWN UUID (primary key) ---------------------------------
                if col.endswith("_uuid") and col in uuid_keys:
                    parts = []
                    for k in uuid_keys[col]:
                        val = row.get(k)
                        if val is None:
                            val = lookup_cache.get(k)
                        if val is None:
                            val = ""  # ← REPLACES None WITH BLANK
                        parts.append(str(val))
                    values.append(derive_uuid("".join(parts)))
                    continue

                # ---- PLAIN VALUE --------------------------------------------
                val = row.get(col)
                if isinstance(val, str) and val.startswith("[") and val.endswith("]"):
                    values.append(val)
                else:
                    values.append(val)

            # ─────────────────────────────────────────────────────────────────
            # 3. BUILD + PRINT SQL + VALUES → THEN EXECUTE
            # ─────────────────────────────────────────────────────────────────
            placeholders = ", ".join(["?"] * len(values))
            sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

            print("\n" + "="*80)
            print(f"DEBUG: INSERT INTO {table_name}")
            print(f"SQL:   {sql}")
            print(f"VALUES: {values}")
            print("="*80 + "\n")

            try:
                c.execute(sql, values)
                conn.commit()
                time.sleep(.1) # wait a little after comitting
                identifier = row.get("name") or row.get("username") or "record"
                print(f"INFO: Inserted into {table_name}: {identifier}\n")
            except sqlite3.IntegrityError as e:
                print(f"ERROR: integrity error in {table_name}: {e}\n   row → {row}\n")
                conn.close()
                sys.exit(1)
            except Exception as e:
                print(f"ERROR: unexpected error in {table_name}: {e}\n   row → {row}\n")
                conn.close()
                sys.exit(1)

    conn.close()
    print("INFO: Database setup completed successfully")


# ─────────────────────────────────────────────────────────────────────────────
# Run
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    setup_database()