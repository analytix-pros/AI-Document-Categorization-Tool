# database/db_models.py
"""Database models for the AI Document Categorization Tool."""
import sqlite3
import sys
import os

# Ensure project root is in path
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import FULL_DATABASE_FILE_PATH
from utils.utils_uuid import derive_uuid, generate_uuid
from utils.utils import get_utc_datetime
from utils.utils_system_specs import get_hostname


def create_connection():
    """Create and return a connection to the SQLite database."""
    conn = sqlite3.connect(FULL_DATABASE_FILE_PATH)
    return conn


class Organization:
    def __init__(self):
        self.table = "organization"

    def insert(self, name, vm_name, is_active=1, is_automation_on=0):
        """Insert a new organization record."""
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        now = get_utc_datetime()
        org_uuid = generate_uuid()
        vm_hash = derive_uuid(get_hostname())
        try:
            c.execute(
                """
                INSERT INTO organization (organization_uuid, name, vm_name, vm_hash, is_active, is_automation_on, created_datetime, updated_datetime)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (org_uuid, name, vm_name, vm_hash, is_active, is_automation_on, now, now)
            )
            conn.commit()
            return org_uuid
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to insert organization: {str(e)}")
        finally:
            conn.close()

    def update(self, organization_uuid, name=None, vm_name=None, is_active=None, is_automation_on=None):
        """Update an existing organization record."""
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        now = get_utc_datetime()
        updates = []
        params = []
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if vm_name is not None:
            updates.append("vm_name = ?")
            params.append(vm_name)
            vm_hash = derive_uuid(get_hostname())
            updates.append("vm_hash = ?")
            params.append(vm_hash)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(is_active)
        if is_automation_on is not None:
            updates.append("is_automation_on = ?")
            params.append(is_automation_on)
        if not updates:
            conn.close()
            return
        updates.append("updated_datetime = ?")
        params.append(now)
        params.append(organization_uuid)
        try:
            c.execute(
                f"UPDATE organization SET {', '.join(updates)} WHERE organization_uuid = ?",
                params
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to update organization: {str(e)}")
        finally:
            conn.close()

    def delete(self, organization_uuid):
        """Soft delete an organization by setting is_active to 0."""
        self.update(organization_uuid, is_active=0)

class UserRole:
    def __init__(self):
        self.table = "user_role"

    def insert(self, name, description="", is_active=1):
        """Insert a new user_role record."""
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        now = get_utc_datetime()
        role_uuid = generate_uuid()
        try:
            c.execute(
                """
                INSERT INTO user_role (user_role_uuid, name, description, is_active, created_datetime, updated_datetime)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (role_uuid, name, description, is_active, now, now)
            )
            conn.commit()
            return role_uuid
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to insert user_role: {str(e)}")
        finally:
            conn.close()

    def update(self, user_role_uuid, name=None, description=None, is_active=None):
        """Update an existing user_role record."""
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        now = get_utc_datetime()
        updates = []
        params = []
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(is_active)
        if not updates:
            conn.close()
            return
        updates.append("updated_datetime = ?")
        params.append(now)
        params.append(user_role_uuid)
        try:
            c.execute(
                f"UPDATE user_role SET {', '.join(updates)} WHERE user_role_uuid = ?",
                params
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to update user_role: {str(e)}")
        finally:
            conn.close()

    def delete(self, user_role_uuid):
        """Soft delete a user_role by setting is_active to 0."""
        self.update(user_role_uuid, is_active=0)

class User:
    def __init__(self):
        self.table = "user"

    def insert(self, user_role_uuid, username, pwd, first_name="", last_name="", email="", is_active=1, organization_uuid=None):
        """Insert a new user record."""
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        now = get_utc_datetime()
        user_uuid = generate_uuid()
        try:
            c.execute(
                """
                INSERT INTO user (user_uuid, organization_uuid, user_role_uuid, username, pwd, first_name, last_name, email, is_active, created_datetime, updated_datetime)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_uuid, organization_uuid, user_role_uuid, username, pwd, first_name, last_name, email, is_active, now, now)
            )
            conn.commit()
            return user_uuid
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to insert user: {str(e)}")
        finally:
            conn.close()

    def update(self, user_uuid, user_role_uuid=None, username=None, pwd=None, first_name=None, last_name=None, email=None, is_active=None, organization_uuid=None):
        """Update an existing user record."""
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        now = get_utc_datetime()
        updates = []
        params = []
        if user_role_uuid is not None:
            updates.append("user_role_uuid = ?")
            params.append(user_role_uuid)
        if username is not None:
            updates.append("username = ?")
            params.append(username)
        if pwd is not None:
            updates.append("pwd = ?")
            params.append(pwd)
        if first_name is not None:
            updates.append("first_name = ?")
            params.append(first_name)
        if last_name is not None:
            updates.append("last_name = ?")
            params.append(last_name)
        if email is not None:
            updates.append("email = ?")
            params.append(email)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(is_active)
        if organization_uuid is not None:
            updates.append("organization_uuid = ?")
            params.append(organization_uuid)
        if not updates:
            conn.close()
            return
        updates.append("updated_datetime = ?")
        params.append(now)
        params.append(user_uuid)
        try:
            c.execute(
                f"UPDATE user SET {', '.join(updates)} WHERE user_uuid = ?",
                params
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to update user: {str(e)}")
        finally:
            conn.close()

    def delete(self, user_uuid):
        """Soft delete a user by setting is_active to 0."""
        self.update(user_uuid, is_active=0)

class Automation:
    def __init__(self):
        self.table = "automation"

    def insert(self, organization_uuid, input_directory, output_directory, review_directory, schedule, is_active=1, created_by=None, updated_by=None):
        """Insert a new automation record."""
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        now = get_utc_datetime()
        automation_uuid = generate_uuid()
        try:
            c.execute(
                """
                INSERT INTO automation (automation_uuid, organization_uuid, input_directory, output_directory, review_directory, schedule, is_active, created_datetime, created_by, updated_datetime, updated_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (automation_uuid, organization_uuid, input_directory, output_directory, review_directory, schedule, is_active, now, created_by, now, updated_by)
            )
            conn.commit()
            return automation_uuid
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to insert automation: {str(e)}")
        finally:
            conn.close()

    def update(self, automation_uuid, organization_uuid=None, input_directory=None, output_directory=None, review_directory=None, schedule=None, is_active=None, updated_by=None):
        """Update an existing automation record."""
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        now = get_utc_datetime()
        updates = []
        params = []
        if organization_uuid is not None:
            updates.append("organization_uuid = ?")
            params.append(organization_uuid)
        if input_directory is not None:
            updates.append("input_directory = ?")
            params.append(input_directory)
        if output_directory is not None:
            updates.append("output_directory = ?")
            params.append(output_directory)
        if review_directory is not None:
            updates.append("review_directory = ?")
            params.append(review_directory)
        if schedule is not None:
            updates.append("schedule = ?")
            params.append(schedule)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(is_active)
        if updated_by is not None:
            updates.append("updated_by = ?")
            params.append(updated_by)
        if not updates:
            conn.close()
            return
        updates.append("updated_datetime = ?")
        params.append(now)
        params.append(automation_uuid)
        try:
            c.execute(
                f"UPDATE automation SET {', '.join(updates)} WHERE automation_uuid = ?",
                params
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to update automation: {str(e)}")
        finally:
            conn.close()

    def delete(self, automation_uuid):
        """Soft delete an automation by setting is_active to 0."""
        self.update(automation_uuid, is_active=0)

class OCRModel:
    def __init__(self):
        self.table = "ocr_models"

    def insert(self, name, default_language, default_dpi, max_pages, is_active=1):
        """Insert a new ocr_models record."""
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        now = get_utc_datetime()
        ocr_uuid = generate_uuid()
        try:
            c.execute(
                """
                INSERT INTO ocr_models (ocr_models_uuid, name, default_language, default_dpi, max_pages, is_active, created_datetime, updated_datetime)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (ocr_uuid, name, default_language, default_dpi, max_pages, is_active, now, now)
            )
            conn.commit()
            return ocr_uuid
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to insert ocr_model: {str(e)}")
        finally:
            conn.close()

    def update(self, ocr_models_uuid, name=None, default_language=None, default_dpi=None, max_pages=None, is_active=None):
        """Update an existing ocr_models record."""
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        now = get_utc_datetime()
        updates = []
        params = []
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if default_language is not None:
            updates.append("default_language = ?")
            params.append(default_language)
        if default_dpi is not None:
            updates.append("default_dpi = ?")
            params.append(default_dpi)
        if max_pages is not None:
            updates.append("max_pages = ?")
            params.append(max_pages)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(is_active)
        if not updates:
            conn.close()
            return
        updates.append("updated_datetime = ?")
        params.append(now)
        params.append(ocr_models_uuid)
        try:
            c.execute(
                f"UPDATE ocr_models SET {', '.join(updates)} WHERE ocr_models_uuid = ?",
                params
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to update ocr_model: {str(e)}")
        finally:
            conn.close()

    def delete(self, ocr_models_uuid):
        """Soft delete an ocr_model by setting is_active to 0."""
        self.update(ocr_models_uuid, is_active=0)

class LLMModel:
    def __init__(self):
        self.table = "llm_models"

    def insert(self, system, name, description, min_ram_gb, default_timeout, gpu_required, gpu_optional, min_vram_gb, is_active=1):
        """Insert a new llm_models record."""
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        now = get_utc_datetime()
        llm_uuid = generate_uuid()
        try:
            c.execute(
                """
                INSERT INTO llm_models (llm_model_uuid, system, name, description, min_ram_gb, default_timeout, gpu_required, gpu_optional, min_vram_gb, is_active, created_datetime, updated_datetime)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (llm_uuid, system, name, description, min_ram_gb, default_timeout, gpu_required, gpu_optional, min_vram_gb, is_active, now, now)
            )
            conn.commit()
            return llm_uuid
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to insert llm_model: {str(e)}")
        finally:
            conn.close()

    def update(self, llm_model_uuid, system=None, name=None, description=None, min_ram_gb=None, default_timeout=None, gpu_required=None, gpu_optional=None, min_vram_gb=None, is_active=None):
        """Update an existing llm_models record."""
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        now = get_utc_datetime()
        updates = []
        params = []
        if system is not None:
            updates.append("system = ?")
            params.append(system)
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if min_ram_gb is not None:
            updates.append("min_ram_gb = ?")
            params.append(min_ram_gb)
        if default_timeout is not None:
            updates.append("default_timeout = ?")
            params.append(default_timeout)
        if gpu_required is not None:
            updates.append("gpu_required = ?")
            params.append(gpu_required)
        if gpu_optional is not None:
            updates.append("gpu_optional = ?")
            params.append(gpu_optional)
        if min_vram_gb is not None:
            updates.append("min_vram_gb = ?")
            params.append(min_vram_gb)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(is_active)
        if not updates:
            conn.close()
            return
        updates.append("updated_datetime = ?")
        params.append(now)
        params.append(llm_model_uuid)
        try:
            c.execute(
                f"UPDATE llm_models SET {', '.join(updates)} WHERE llm_model_uuid = ?",
                params
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to update llm_model: {str(e)}")
        finally:
            conn.close()

    def delete(self, llm_model_uuid):
        """Soft delete an llm_model by setting is_active to 0."""
        self.update(llm_model_uuid, is_active=0)

class Category:
    def __init__(self):
        self.table = "category"

    def insert(self, organization_uuid, name, hierarchy_level, use_stamps=0, stamps_uuid=None, description="", keywords="", file_rename_rules="", is_active=1, created_by=None, updated_by=None, parent_category_uuid=None):
        """Insert a new category record."""
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        now = get_utc_datetime()
        category_uuid = generate_uuid()
        try:
            c.execute(
                """
                INSERT INTO category (category_uuid, parent_category_uuid, organization_uuid, name, hierarchy_level, use_stamps, stamps_uuid, description, keywords, file_rename_rules, is_active, created_datetime, created_by, updated_datetime, updated_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (category_uuid, parent_category_uuid, organization_uuid, name, hierarchy_level, use_stamps, stamps_uuid, description, keywords, file_rename_rules, is_active, now, created_by, now, updated_by)
            )
            conn.commit()
            return category_uuid
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to insert category: {str(e)}")
        finally:
            conn.close()

    def update(self, category_uuid, organization_uuid=None, name=None, hierarchy_level=None, use_stamps=None, stamps_uuid=None, description=None, keywords=None, file_rename_rules=None, is_active=None, updated_by=None, parent_category_uuid=None):
        """Update an existing category record."""
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        now = get_utc_datetime()
        updates = []
        params = []
        if organization_uuid is not None:
            updates.append("organization_uuid = ?")
            params.append(organization_uuid)
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if hierarchy_level is not None:
            updates.append("hierarchy_level = ?")
            params.append(hierarchy_level)
        if use_stamps is not None:
            updates.append("use_stamps = ?")
            params.append(use_stamps)
        if stamps_uuid is not None:
            updates.append("stamps_uuid = ?")
            params.append(stamps_uuid)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if keywords is not None:
            updates.append("keywords = ?")
            params.append(keywords)
        if file_rename_rules is not None:
            updates.append("file_rename_rules = ?")
            params.append(file_rename_rules)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(is_active)
        if updated_by is not None:
            updates.append("updated_by = ?")
            params.append(updated_by)
        if parent_category_uuid is not None:
            updates.append("parent_category_uuid = ?")
            params.append(parent_category_uuid)
        if not updates:
            conn.close()
            return
        updates.append("updated_datetime = ?")
        params.append(now)
        params.append(category_uuid)
        try:
            c.execute(
                f"UPDATE category SET {', '.join(updates)} WHERE category_uuid = ?",
                params
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to update category: {str(e)}")
        finally:
            conn.close()

    def delete(self, category_uuid):
        """Soft delete a category by setting is_active to 0."""
        self.update(category_uuid, is_active=0)

class Stamps:
    def __init__(self):
        self.table = "stamps"

    def insert(self, organization_uuid, name, description="", keywords="", is_active=1, created_by=None, updated_by=None):
        """Insert a new stamps record."""
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        now = get_utc_datetime()
        stamps_uuid = derive_uuid(f"{get_hostname()}{name}")
        try:
            c.execute(
                """
                INSERT INTO stamps (stamps_uuid, organization_uuid, name, description, keywords, is_active, created_datetime, created_by, updated_datetime, updated_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (stamps_uuid, organization_uuid, name, description, keywords, is_active, now, created_by, now, updated_by)
            )
            conn.commit()
            return stamps_uuid
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to insert stamps: {str(e)}")
        finally:
            conn.close()

    def update(self, stamps_uuid, organization_uuid=None, name=None, description=None, keywords=None, is_active=None, updated_by=None):
        """Update an existing stamps record."""
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        now = get_utc_datetime()
        updates = []
        params = []
        if organization_uuid is not None:
            updates.append("organization_uuid = ?")
            params.append(organization_uuid)
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if keywords is not None:
            updates.append("keywords = ?")
            params.append(keywords)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(is_active)
        if updated_by is not None:
            updates.append("updated_by = ?")
            params.append(updated_by)
        if not updates:
            conn.close()
            return
        updates.append("updated_datetime = ?")
        params.append(now)
        params.append(stamps_uuid)
        try:
            c.execute(
                f"UPDATE stamps SET {', '.join(updates)} WHERE stamps_uuid = ?",
                params
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to update stamps: {str(e)}")
        finally:
            conn.close()

    def delete(self, stamps_uuid):
        """Soft delete a stamps record by setting is_active to 0."""
        self.update(stamps_uuid, is_active=0)

class Logging:
    def __init__(self):
        self.table = "logging"

    def insert(self, organization_uuid, user_uuid, page, message, level):
        """Insert a new logging record."""
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        now = get_utc_datetime()
        logging_uuid = generate_uuid()
        try:
            c.execute(
                """
                INSERT INTO logging (logging_uuid, organization_uuid, user_uuid, page, message, level, created_datetime)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (logging_uuid, organization_uuid, user_uuid, page, message, level, now)
            )
            conn.commit()
            return logging_uuid
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to insert logging: {str(e)}")
        finally:
            conn.close()

class Batch:
    def __init__(self):
        self.table = "batch"

    def insert(self, organization_uuid, automation_uuid, system_metadata, status, process_time, created_by):
        """Insert a new batch record."""
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        now = get_utc_datetime()
        batch_uuid = generate_uuid()
        try:
            c.execute(
                """
                INSERT INTO batch (batch_uuid, organization_uuid, automation_uuid, system_metadata, status, process_time, created_datetime, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (batch_uuid, organization_uuid, automation_uuid, system_metadata, status, process_time, now, created_by)
            )
            conn.commit()
            return batch_uuid
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to insert batch: {str(e)}")
        finally:
            conn.close()

    def update(self, batch_uuid, organization_uuid=None, automation_uuid=None, system_metadata=None, status=None, process_time=None):
        """Update an existing batch record."""
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        now = get_utc_datetime()
        updates = []
        params = []
        if organization_uuid is not None:
            updates.append("organization_uuid = ?")
            params.append(organization_uuid)
        if automation_uuid is not None:
            updates.append("automation_uuid = ?")
            params.append(automation_uuid)
        if system_metadata is not None:
            updates.append("system_metadata = ?")
            params.append(system_metadata)
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if process_time is not None:
            updates.append("process_time = ?")
            params.append(process_time)
        if not updates:
            conn.close()
            return
        params.append(batch_uuid)
        try:
            c.execute(
                f"UPDATE batch SET {', '.join(updates)} WHERE batch_uuid = ?",
                params
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to update batch: {str(e)}")
        finally:
            conn.close()

    def delete(self, batch_uuid):
        """Batch records are not soft-deleted, as they are part of immutable processing logs."""
        raise NotImplementedError("Batch records cannot be deleted.")

class Document:
    def __init__(self):
        self.table = "document"

    def insert(self, organization_uuid, upload_name, upload_folder=None, pdf=None, is_active=1, created_by=None, updated_by=None):
        """Insert a new document record."""
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        now = get_utc_datetime()
        document_uuid = generate_uuid()
        try:
            c.execute(
                """
                INSERT INTO document (document_uuid, organization_uuid, upload_name, upload_folder, pdf, is_active, created_datetime, created_by, updated_datetime, updated_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (document_uuid, organization_uuid, upload_name, upload_folder, pdf, is_active, now, created_by, now, updated_by)
            )
            conn.commit()
            return document_uuid
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to insert document: {str(e)}")
        finally:
            conn.close()

    def update(self, document_uuid, organization_uuid=None, upload_name=None, upload_folder=None, pdf=None, is_active=None, updated_by=None):
        """Update an existing document record."""
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        now = get_utc_datetime()
        updates = []
        params = []
        if organization_uuid is not None:
            updates.append("organization_uuid = ?")
            params.append(organization_uuid)
        if upload_name is not None:
            updates.append("upload_name = ?")
            params.append(upload_name)
        if upload_folder is not None:
            updates.append("upload_folder = ?")
            params.append(upload_folder)
        if pdf is not None:
            updates.append("pdf = ?")
            params.append(pdf)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(is_active)
        if updated_by is not None:
            updates.append("updated_by = ?")
            params.append(updated_by)
        if not updates:
            conn.close()
            return
        updates.append("updated_datetime = ?")
        params.append(now)
        params.append(document_uuid)
        try:
            c.execute(
                f"UPDATE document SET {', '.join(updates)} WHERE document_uuid = ?",
                params
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to update document: {str(e)}")
        finally:
            conn.close()

    def delete(self, document_uuid):
        """Soft delete a document by setting is_active to 0."""
        self.update(document_uuid, is_active=0)

class DocumentCategory:
    def __init__(self):
        self.table = "document_category"

    def insert(self, organization_uuid, document_uuid, category_uuid, stamps_uuid=None, category_confidence=None, all_category_confidence=None, ocr_text=None, ocr_text_confidence=None, override_category_uuid=None, override_context=None, is_active=1, created_by=None, updated_by=None):
        """Insert a new document_category record."""
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        now = get_utc_datetime()
        doc_category_uuid = generate_uuid()
        try:
            c.execute(
                """
                INSERT INTO document_category (document_category_uuid, organization_uuid, document_uuid, category_uuid, stamps_uuid, category_confidence, all_category_confidence, ocr_text, ocr_text_confidence, override_category_uuid, override_context, is_active, created_datetime, created_by, updated_datetime, updated_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (doc_category_uuid, organization_uuid, document_uuid, category_uuid, stamps_uuid, category_confidence, all_category_confidence, ocr_text, ocr_text_confidence, override_category_uuid, override_context, is_active, now, created_by, now, updated_by)
            )
            conn.commit()
            return doc_category_uuid
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to insert document_category: {str(e)}")
        finally:
            conn.close()

    def update(self, document_category_uuid, organization_uuid=None, document_uuid=None, category_uuid=None, stamps_uuid=None, category_confidence=None, all_category_confidence=None, ocr_text=None, ocr_text_confidence=None, override_category_uuid=None, override_context=None, is_active=None, updated_by=None):
        """Update an existing document_category record."""
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        now = get_utc_datetime()
        updates = []
        params = []
        if organization_uuid is not None:
            updates.append("organization_uuid = ?")
            params.append(organization_uuid)
        if document_uuid is not None:
            updates.append("document_uuid = ?")
            params.append(document_uuid)
        if category_uuid is not None:
            updates.append("category_uuid = ?")
            params.append(category_uuid)
        if stamps_uuid is not None:
            updates.append("stamps_uuid = ?")
            params.append(stamps_uuid)
        if category_confidence is not None:
            updates.append("category_confidence = ?")
            params.append(category_confidence)
        if all_category_confidence is not None:
            updates.append("all_category_confidence = ?")
            params.append(all_category_confidence)
        if ocr_text is not None:
            updates.append("ocr_text = ?")
            params.append(ocr_text)
        if ocr_text_confidence is not None:
            updates.append("ocr_text_confidence = ?")
            params.append(ocr_text_confidence)
        if override_category_uuid is not None:
            updates.append("override_category_uuid = ?")
            params.append(override_category_uuid)
        if override_context is not None:
            updates.append("override_context = ?")
            params.append(override_context)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(is_active)
        if updated_by is not None:
            updates.append("updated_by = ?")
            params.append(updated_by)
        if not updates:
            conn.close()
            return
        updates.append("updated_datetime = ?")
        params.append(now)
        params.append(document_category_uuid)
        try:
            c.execute(
                f"UPDATE document_category SET {', '.join(updates)} WHERE document_category_uuid = ?",
                params
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to update document_category: {str(e)}")
        finally:
            conn.close()

    def delete(self, document_category_uuid):
        """Soft delete a document_category by setting is_active to 0."""
        self.update(document_category_uuid, is_active=0)


if __name__ == "__main__":
    # Example usage
    org = Organization()
    # org_uuid = org.insert("Test Org", "Test-VM.local")
    # role = UserRole()
    # role_uuid = role.insert("test_role", "Test role description")
    # user = User()
    # user_uuid = user.insert(role_uuid, "testuser", "password123")
    # stamps = Stamps()
    # stamps_uuid = stamps.insert(org_uuid, "TEST_STAMP", keywords="['test']", created_by=user_uuid, updated_by=user_uuid)