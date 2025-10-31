"""Database models – dict-based, DRY, UUID-strategy driven, with console debug."""
import sqlite3
import os
from typing import Any, Dict, List, Tuple, Optional

from config.config import FULL_DATABASE_FILE_PATH
from initial_setup.config import METADATA_FIELDS  # <-- Imported from config
from utils.utils_uuid import derive_uuid, generate_uuid
from utils.utils import get_utc_datetime
from utils.utils_system_specs import get_hostname
from utils.utils_logging import log_database_operation
import streamlit as st


# --------------------------------------------------------------------------- #
# CONNECTION
# --------------------------------------------------------------------------- #
def create_connection():
    conn = sqlite3.connect(FULL_DATABASE_FILE_PATH)
    print(f"[DB] Connected to {FULL_DATABASE_FILE_PATH}")
    return conn


# --------------------------------------------------------------------------- #
# UUID STRATEGY REGISTRY
# --------------------------------------------------------------------------- #
UUID_STRATEGIES = {
    "automation": lambda d: generate_uuid(d["organization_uuid"]),
    "batch": lambda d: generate_uuid(f"{d['organization_uuid']}{d.get('automation_uuid', '')}"),
    "category": lambda d: derive_uuid(f"{d.get('parent_category_uuid', '')}{d['organization_uuid']}{d['name']}"),
    "document": lambda d: derive_uuid(f"{d['organization_uuid']}{d['batch_uuid']}{d['upload_name']}"),
    "document_category": lambda d: derive_uuid(f"{d['organization_uuid']}{d['document_uuid']}"),
    "llm_models": lambda d: derive_uuid(f"{d['system']}{d['name']}"),
    "ocr_models": lambda d: derive_uuid(d["name"]),
    "organization": lambda d: derive_uuid(d["name"]),
    "stamps": lambda d: derive_uuid(f"{d['organization_uuid']}{d['name']}"),
    "user": lambda d: derive_uuid(d["username"]),
    "user_role": lambda d: derive_uuid(d["name"]),
}


# --------------------------------------------------------------------------- #
# HELPERS
# --------------------------------------------------------------------------- #
def _current_user_uuid() -> bytes:
    """Return the logged-in user UUID (BLOB) from Streamlit session_state."""
    if "user_uuid" not in st.session_state:
        raise RuntimeError("User is not logged in – session_state['user_uuid'] missing.")
    return st.session_state["user_uuid"]


# --------------------------------------------------------------------------- #
# TABLE-SPECIFIC BUSINESS FIELDS (required + optional)
# --------------------------------------------------------------------------- #
TABLE_REQUIRED_FIELDS: Dict[str, List[str]] = {
    "organization": ["name"],
    "user_role": ["name"],
    "user": ["username", "user_role_uuid", "pwd"],
    "automation": ["organization_uuid", "input_directory", "output_directory", "review_directory", "schedule"],
    "ocr_models": ["name", "default_language", "default_dpi", "max_pages"],
    "llm_models": ["system", "name", "description", "min_ram_gb", "default_timeout", "gpu_required", "gpu_optional", "min_vram_gb", "is_vision_capable"],
    "category": ["organization_uuid", "name", "hierarchy_level"],
    "stamps": ["organization_uuid", "name"],
    "batch": ["organization_uuid", "system_metadata", "status", "number_of_files", "process_time"],
    "document": ["organization_uuid", "batch_uuid", "upload_name"],
    "document_category": ["organization_uuid", "document_uuid"],
}

TABLE_OPTIONAL_FIELDS: Dict[str, List[str]] = {
    "organization": ["vm_name", "is_automation_on"],
    "user_role": ["description"],
    "user": ["first_name", "last_name", "email", "organization_uuid"],
    "automation": ["created_by", "updated_by"],  # kept only for legacy – will be ignored
    "ocr_models": [],
    "llm_models": [],
    "category": [
        "parent_category_uuid", "use_stamps", "description", "use_keywords", 
        "keywords", "use_llm", "high_min_threshold", "medium_min_threshold", 
        "exclusion_rules", "file_rename_rules", "created_by", "updated_by"
    ],
    "stamps": ["description", "keywords", "created_by", "updated_by"],
    "batch": ["automation_uuid"],
    "document": ["upload_folder", "pdf", "created_by", "updated_by"],
    "document_category": [
        "category_uuid", "stamps_uuid", "category_confidence", "all_category_confidence",
        "ocr_text", "ocr_text_confidence", "override_category_uuid", "override_context",
        "created_by", "updated_by",
    ],
}


# --------------------------------------------------------------------------- #
# SQL BUILDERS – fully generic, metadata always included
# --------------------------------------------------------------------------- #
def _build_insert_sql(table: str, data: Dict[str, Any], uuid_field: str, uuid_val: bytes) -> Tuple[str, List[Any]]:
    now = get_utc_datetime()
    user_uuid = _current_user_uuid()

    fields: List[str] = [uuid_field]
    placeholders: List[str] = ["?"]
    values: List[Any] = [uuid_val]

    # 1. Required business fields
    for f in TABLE_REQUIRED_FIELDS.get(table, []):
        if f not in data:
            raise ValueError(f"Missing required field '{f}' for table '{table}'")
        fields.append(f)
        placeholders.append("?")
        values.append(data[f])

    # 2. Optional business fields
    for f in TABLE_OPTIONAL_FIELDS.get(table, []):
        if f in data:
            fields.append(f)
            placeholders.append("?")
            values.append(data[f])

    # 3. METADATA FIELDS – always added
    fields.append("is_active")
    placeholders.append("?")
    values.append(data.get("is_active", 1))

    fields.extend(["created_datetime", "created_by"])
    placeholders.extend(["?", "?"])
    values.extend([now, user_uuid])

    fields.extend(["updated_datetime", "updated_by"])
    placeholders.extend(["?", "?"])
    values.extend([now, user_uuid])

    # 4. Special: organization.vm_hash
    if table == "organization" and "vm_name" in data:
        fields.append("vm_hash")
        placeholders.append("?")
        values.append(derive_uuid(get_hostname()))

    sql = f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
    return sql, values


def _build_update_sql(table: str, data: Dict[str, Any], uuid_field: str, uuid_val: bytes) -> Tuple[Optional[str], Optional[List[Any]]]:
    now = get_utc_datetime()
    user_uuid = _current_user_uuid()

    updates: List[str] = []
    params: List[Any] = []

    updatable = TABLE_REQUIRED_FIELDS.get(table, []) + TABLE_OPTIONAL_FIELDS.get(table, [])
    for f in updatable:
        if f in data:
            updates.append(f"{f} = ?")
            params.append(data[f])

    if table == "organization" and "vm_name" in data:
        updates.append("vm_hash = ?")
        params.append(derive_uuid(get_hostname()))

    if not updates:
        return None, None

    updates.append("updated_datetime = ?")
    params.append(now)
    updates.append("updated_by = ?")
    params.append(user_uuid)

    sql = f"UPDATE {table} SET {', '.join(updates)} WHERE {uuid_field} = ?"
    params.append(uuid_val)
    return sql, params


# --------------------------------------------------------------------------- #
# BASE MODEL
# --------------------------------------------------------------------------- #
class BaseModel:
    def __init__(self, table: str, uuid_field: str):
        self.table = table
        self.uuid_field = uuid_field

    def insert(self, session_state, page_name: str, data: Dict[str, Any]) -> bytes:
        print(f"\n[DB INSERT] Table: {self.table} | Page: {page_name}")
        print(f"    Data: {data}")

        conn = None  # ← ensure defined
        try:
            strategy = UUID_STRATEGIES.get(self.table)
            if not strategy:
                raise ValueError(f"No UUID strategy for table: {self.table}")
            uuid_val = strategy(data)
            print(f"    UUID: {uuid_val}")

            sql, params = _build_insert_sql(self.table, data, self.uuid_field, uuid_val)
            print(f"    SQL: {sql}")
            print(f"    Params: {params}")

            conn = create_connection()
            c = conn.cursor()
            c.execute("PRAGMA foreign_keys = ON")
            c.execute(sql, params)
            conn.commit()

            print(f"    SUCCESS: Inserted | UUID: {uuid_val}")
            log_database_operation(session_state, page_name, "INSERT", self.table, success=True)
            return uuid_val

        except sqlite3.IntegrityError as e:
            error_msg = str(e)
            print(f"    FAILED (Integrity): {error_msg}")
            log_database_operation(session_state, page_name, "INSERT", self.table, success=False, error_msg=error_msg)
            raise ValueError(f"Integrity error in {self.table}: {error_msg}")
        except Exception as e:
            print(f"    UNEXPECTED ERROR: {e}")
            raise
        finally:
            if conn:
                conn.close()
                print(f"[DB] Connection closed.\n")

    def update(self, session_state, page_name: str, uuid_val: bytes, data: Dict[str, Any]) -> None:
        if not data:
            print(f"[DB UPDATE] No data for {self.table} UUID={uuid_val}. Skipping.")
            return

        print(f"\n[DB UPDATE] Table: {self.table} | UUID: {uuid_val} | Page: {page_name}")
        print(f"    Updating: {list(data.keys())}")

        conn = None
        try:
            sql, params = _build_update_sql(self.table, data, self.uuid_field, uuid_val)
            if not sql:
                print("    No fields to update.")
                return

            print(f"    SQL: {sql}")
            print(f"    Params: {params}")

            conn = create_connection()
            c = conn.cursor()
            c.execute("PRAGMA foreign_keys = ON")
            c.execute(sql, params)
            conn.commit()

            print(f"    SUCCESS: Updated | UUID: {uuid_val}")
            log_database_operation(session_state, page_name, "UPDATE", self.table, success=True)

        except sqlite3.IntegrityError as e:
            error_msg = str(e)
            print(f"    FAILED: {error_msg}")
            log_database_operation(session_state, page_name, "UPDATE", self.table, success=False, error_msg=error_msg)
            raise ValueError(f"Failed to update {self.table}: {error_msg}")
        finally:
            if conn:
                conn.close()
                print(f"[DB] Connection closed.\n")

    def delete(self, session_state, page_name: str, uuid_val: bytes) -> None:
        print(f"\n[DB DELETE] Soft-delete {self.table} | UUID: {uuid_val} | Page: {page_name}")
        self.update(session_state, page_name, uuid_val, {"is_active": 0})


# --------------------------------------------------------------------------- #
# CONCRETE MODELS
# --------------------------------------------------------------------------- #
class Organization(BaseModel):
    def __init__(self):
        super().__init__("organization", "organization_uuid")

class UserRole(BaseModel):
    def __init__(self):
        super().__init__("user_role", "user_role_uuid")

class User(BaseModel):
    def __init__(self):
        super().__init__("user", "user_uuid")

class Automation(BaseModel):
    def __init__(self):
        super().__init__("automation", "automation_uuid")

class OCRModel(BaseModel):
    def __init__(self):
        super().__init__("ocr_models", "ocr_models_uuid")

class LLMModel(BaseModel):
    def __init__(self):
        super().__init__("llm_models", "llm_model_uuid")

class Category(BaseModel):
    def __init__(self):
        super().__init__("category", "category_uuid")

class Stamps(BaseModel):
    def __init__(self):
        super().__init__("stamps", "stamps_uuid")

class Batch(BaseModel):
    def __init__(self):
        super().__init__("batch", "batch_uuid")

    def delete(self, session_state, page_name: str, uuid_val: bytes) -> None:
        print(f"[DB] Batch records cannot be deleted. UUID: {uuid_val}")
        raise NotImplementedError("Batch records cannot be deleted.")

class Document(BaseModel):
    def __init__(self):
        super().__init__("document", "document_uuid")

class DocumentCategory(BaseModel):
    def __init__(self):
        super().__init__("document_category", "document_category_uuid")