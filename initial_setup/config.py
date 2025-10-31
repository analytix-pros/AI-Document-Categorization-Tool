# initial_setup/config.py
import sys
import os

# Set project root and change working directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(PROJECT_ROOT)

# Local imports
try:
    from utils.utils_system_specs import get_hostname
    from utils.utils_uuid import derive_uuid
    from utils.utils import get_utc_datetime
except ImportError as e:
    print(f"ERROR: Failed to import required modules: {str(e)}")
    print("Ensure utils/utils.py, utils/utils_system_specs.py, and utils/utils_uuid.py exist.")
    sys.exit(1)



# === SHARED METADATA FIELDS ===
METADATA_FIELDS = {
    "is_active": {
        "primary_key": False,
        "data_type": "INTEGER",
        "null_constraint": "NOT NULL",
        "column_default": 1,
        "is_unique": False
    },
    "created_datetime": {
        "primary_key": False,
        "data_type": "TEXT",
        "null_constraint": "NULL",
        "column_default": None,
        "is_unique": False
    },
    "created_by": {
        "primary_key": False,
        "data_type": "BLOB",
        "null_constraint": "NULL",
        "column_default": None,
        "is_unique": False
    },
    "updated_datetime": {
        "primary_key": False,
        "data_type": "TEXT",
        "null_constraint": "NULL",
        "column_default": None,
        "is_unique": False
    },
    "updated_by": {
        "primary_key": False,
        "data_type": "BLOB",
        "null_constraint": "NULL",
        "column_default": None,
        "is_unique": False
    }
}


# === TABLES WITH STRUCTURED SCHEMA ===
TABLES = [
    {
        "name": "logging",
        "columns": {
            "logging_uuid": {
                "primary_key": True,
                "data_type": "BLOB",
                "null_constraint": "NOT NULL",
                "column_default": None,
                "is_unique": True
            },
            "organization_uuid": {
                "primary_key": False,
                "data_type": "BLOB",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "user_uuid": {
                "primary_key": False,
                "data_type": "BLOB",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "page": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "message": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "level": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            **METADATA_FIELDS
        },
        "foreign_keys": [],
        "indexes": [
            ("logging_organization_uuid", "CREATE INDEX IF NOT EXISTS logging_organization_uuid ON logging (organization_uuid)"),
            ("logging_user_uuid", "CREATE INDEX IF NOT EXISTS logging_user_uuid ON logging (user_uuid)"),
            ("logging_page", "CREATE INDEX IF NOT EXISTS logging_page ON logging (page)"),
            ("logging_level", "CREATE INDEX IF NOT EXISTS logging_level ON logging (level)")
        ]
    },
    {
        "name": "organization",
        "columns": {
            "organization_uuid": {
                "primary_key": True,
                "data_type": "BLOB",
                "null_constraint": "NOT NULL",
                "column_default": None,
                "is_unique": True
            },
            "name": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "vm_name": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "vm_hash": {
                "primary_key": False,
                "data_type": "BLOB",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": True
            },
            "is_automation_on": {
                "primary_key": False,
                "data_type": "INTEGER",
                "null_constraint": "NOT NULL",
                "column_default": 0,
                "is_unique": False
            },
            **METADATA_FIELDS
        },
        "foreign_keys": [],
        "indexes": [
            ("organization_vm_hash", "CREATE INDEX IF NOT EXISTS organization_vm_hash ON organization (vm_hash)")
        ]
    },
    {
        "name": "user_role",
        "columns": {
            "user_role_uuid": {
                "primary_key": True,
                "data_type": "BLOB",
                "null_constraint": "NOT NULL",
                "column_default": None,
                "is_unique": True
            },
            "name": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NOT NULL",
                "column_default": None,
                "is_unique": True
            },
            "description": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            **METADATA_FIELDS
        },
        "foreign_keys": [],
        "indexes": []
    },
    {
        "name": "user",
        "columns": {
            "user_uuid": {
                "primary_key": True,
                "data_type": "BLOB",
                "null_constraint": "NOT NULL",
                "column_default": None,
                "is_unique": True
            },
            "organization_uuid": {
                "primary_key": False,
                "data_type": "BLOB",
                "null_constraint": "NOT NULL",
                "column_default": None,
                "is_unique": False
            },
            "user_role_uuid": {
                "primary_key": False,
                "data_type": "BLOB",
                "null_constraint": "NOT NULL",
                "column_default": None,
                "is_unique": False
            },
            "username": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NOT NULL",
                "column_default": None,
                "is_unique": True
            },
            "pwd": {
                "primary_key": False,
                "data_type": "BLOB",
                "null_constraint": "NOT NULL",
                "column_default": None,
                "is_unique": False
            },
            "first_name": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "last_name": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "email": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            **METADATA_FIELDS
        },
        "foreign_keys": [
            "FOREIGN KEY (organization_uuid) REFERENCES organization (organization_uuid)",
            "FOREIGN KEY (user_role_uuid) REFERENCES user_role (user_role_uuid)"
        ],
        "indexes": [
            ("user_organization_uuid", "CREATE INDEX IF NOT EXISTS user_organization_uuid ON user (organization_uuid)"),
            ("user_role_uuid", "CREATE INDEX IF NOT EXISTS user_role_uuid ON user (user_role_uuid)")
        ]
    },
    {
        "name": "automation",
        "columns": {
            "automation_uuid": {
                "primary_key": True,
                "data_type": "BLOB",
                "null_constraint": "NOT NULL",
                "column_default": None,
                "is_unique": True
            },
            "organization_uuid": {
                "primary_key": False,
                "data_type": "BLOB",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "input_directory": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "output_directory": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "review_directory": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "schedule": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            **METADATA_FIELDS
        },
        "foreign_keys": [
            "FOREIGN KEY (organization_uuid) REFERENCES organization (organization_uuid)",
            "FOREIGN KEY (created_by) REFERENCES user (user_uuid)",
            "FOREIGN KEY (updated_by) REFERENCES user (user_uuid)"
        ],
        "indexes": [
            ("automation_organization_uuid", "CREATE INDEX IF NOT EXISTS automation_organization_uuid ON automation (organization_uuid)")
        ]
    },
    {
        "name": "ocr_models",
        "columns": {
            "ocr_models_uuid": {
                "primary_key": True,
                "data_type": "BLOB",
                "null_constraint": "NOT NULL",
                "column_default": None,
                "is_unique": True
            },
            "name": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "description": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "min_storage_gb": {
                "primary_key": False,
                "data_type": "REAL",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "min_ram_gb": {
                "primary_key": False,
                "data_type": "INTEGER",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "gpu_required": {
                "primary_key": False,
                "data_type": "INTEGER",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "gpu_optional": {
                "primary_key": False,
                "data_type": "INTEGER",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "min_vram_gb": {
                "primary_key": False,
                "data_type": "INTEGER",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "default_language": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "default_dpi": {
                "primary_key": False,
                "data_type": "INTEGER",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "max_pages": {
                "primary_key": False,
                "data_type": "INTEGER",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            **METADATA_FIELDS
        },
        "foreign_keys": [],
        "indexes": []
    },
    {
        "name": "llm_models",
        "columns": {
            "llm_model_uuid": {
                "primary_key": True,
                "data_type": "BLOB",
                "null_constraint": "NOT NULL",
                "column_default": None,
                "is_unique": True
            },
            "system": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "name": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "description": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "min_ram_gb": {
                "primary_key": False,
                "data_type": "INTEGER",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "default_timeout": {
                "primary_key": False,
                "data_type": "INTEGER",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "gpu_required": {
                "primary_key": False,
                "data_type": "INTEGER",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "gpu_optional": {
                "primary_key": False,
                "data_type": "INTEGER",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "min_vram_gb": {
                "primary_key": False,
                "data_type": "INTEGER",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "is_vision_capable": {
                "primary_key": False,
                "data_type": "INTEGER",
                "null_constraint": "NULL",
                "column_default": 0,
                "is_unique": False
            },
            **METADATA_FIELDS
        },
        "foreign_keys": [],
        "indexes": []
    },
    {
        "name": "stamps",
        "columns": {
            "stamps_uuid": {
                "primary_key": True,
                "data_type": "BLOB",
                "null_constraint": "NOT NULL",
                "column_default": None,
                "is_unique": True
            },
            "organization_uuid": {
                "primary_key": False,
                "data_type": "BLOB",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "name": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "description": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "keywords": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            **METADATA_FIELDS
        },
        "foreign_keys": [
            "FOREIGN KEY (organization_uuid) REFERENCES organization (organization_uuid)",
            "FOREIGN KEY (created_by) REFERENCES user (user_uuid)",
            "FOREIGN KEY (updated_by) REFERENCES user (user_uuid)"
        ],
        "indexes": [
            ("stamps_organization_uuid", "CREATE INDEX IF NOT EXISTS stamps_organization_uuid ON stamps (organization_uuid)")
        ]
    },
    {
        "name": "category",
        "columns": {
            "category_uuid": {
                "primary_key": True,
                "data_type": "BLOB",
                "null_constraint": "NOT NULL",
                "column_default": None,
                "is_unique": True
            },
            "parent_category_uuid": {
                "primary_key": False,
                "data_type": "BLOB",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "organization_uuid": {
                "primary_key": False,
                "data_type": "BLOB",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "name": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "hierarchy_level": {
                "primary_key": False,
                "data_type": "INTEGER",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "use_stamps": {
                "primary_key": False,
                "data_type": "INTEGER",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "description": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "use_keywords": {
                "primary_key": False,
                "data_type": "INTEGER",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "keywords": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "use_llm": {
                "primary_key": False,
                "data_type": "INTEGER",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "high_min_threshold": {
                "primary_key": False,
                "data_type": "REAL",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "medium_min_threshold": {
                "primary_key": False,
                "data_type": "REAL",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "exclusion_rules": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "file_rename_rules": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            **METADATA_FIELDS
        },
        "foreign_keys": [
            "FOREIGN KEY (parent_category_uuid) REFERENCES category (category_uuid)",
            "FOREIGN KEY (organization_uuid) REFERENCES organization (organization_uuid)",
            "FOREIGN KEY (created_by) REFERENCES user (user_uuid)",
            "FOREIGN KEY (updated_by) REFERENCES user (user_uuid)"
        ],
        "indexes": [
            ("category_parent_category_uuid", "CREATE INDEX IF NOT EXISTS category_parent_category_uuid ON category (parent_category_uuid)"),
            ("category_organization_uuid", "CREATE INDEX IF NOT EXISTS category_organization_uuid ON category (organization_uuid)")
        ]
    },
    {
        "name": "batch",
        "columns": {
            "batch_uuid": {
                "primary_key": True,
                "data_type": "BLOB",
                "null_constraint": "NOT NULL",
                "column_default": None,
                "is_unique": True
            },
            "organization_uuid": {
                "primary_key": False,
                "data_type": "BLOB",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "automation_uuid": {
                "primary_key": False,
                "data_type": "BLOB",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "system_metadata": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "status": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "number_of_files": {
                "primary_key": False,
                "data_type": "INTEGER",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "process_time": {
                "primary_key": False,
                "data_type": "INTEGER",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            **METADATA_FIELDS
        },
        "foreign_keys": [
            "FOREIGN KEY (organization_uuid) REFERENCES organization (organization_uuid)",
            "FOREIGN KEY (automation_uuid) REFERENCES automation (automation_uuid)",
            "FOREIGN KEY (created_by) REFERENCES user (user_uuid)"
        ],
        "indexes": [
            ("batch_organization_uuid", "CREATE INDEX IF NOT EXISTS batch_organization_uuid ON batch (organization_uuid)"),
            ("batch_automation_uuid", "CREATE INDEX IF NOT EXISTS batch_automation_uuid ON batch (automation_uuid)")
        ]
    },
    {
        "name": "document",
        "columns": {
            "document_uuid": {
                "primary_key": True,
                "data_type": "BLOB",
                "null_constraint": "NOT NULL",
                "column_default": None,
                "is_unique": True
            },
            "organization_uuid": {
                "primary_key": False,
                "data_type": "BLOB",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "batch_uuid": {
                "primary_key": False,
                "data_type": "BLOB",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "upload_name": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "upload_folder": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "pdf": {
                "primary_key": False,
                "data_type": "BLOB",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "image_of_pdf": {
                "primary_key": False,
                "data_type": "BLOB",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            **METADATA_FIELDS
        },
        "foreign_keys": [
            "FOREIGN KEY (organization_uuid) REFERENCES organization (organization_uuid)",
            "FOREIGN KEY (batch_uuid) REFERENCES batch (batch_uuid)",
            "FOREIGN KEY (created_by) REFERENCES user (user_uuid)",
            "FOREIGN KEY (updated_by) REFERENCES user (user_uuid)"
        ],
        "indexes": [
            ("document_organization_uuid", "CREATE INDEX IF NOT EXISTS document_organization_uuid ON document (organization_uuid)"),
            ("document_batch_uuid", "CREATE INDEX IF NOT EXISTS document_batch_uuid ON document (batch_uuid)")
        ]
    },
    {
        "name": "document_category",
        "columns": {
            "document_category_uuid": {
                "primary_key": True,
                "data_type": "BLOB",
                "null_constraint": "NOT NULL",
                "column_default": None,
                "is_unique": True
            },
            "organization_uuid": {
                "primary_key": False,
                "data_type": "BLOB",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "document_uuid": {
                "primary_key": False,
                "data_type": "BLOB",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "category_uuid": {
                "primary_key": False,
                "data_type": "BLOB",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "stamps_uuid": {
                "primary_key": False,
                "data_type": "BLOB",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "category_confidence": {
                "primary_key": False,
                "data_type": "REAL",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "all_category_confidence": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "ocr_text": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "ocr_text_confidence": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "override_category_uuid": {
                "primary_key": False,
                "data_type": "BLOB",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            "override_context": {
                "primary_key": False,
                "data_type": "TEXT",
                "null_constraint": "NULL",
                "column_default": None,
                "is_unique": False
            },
            **METADATA_FIELDS
        },
        "foreign_keys": [
            "FOREIGN KEY (organization_uuid) REFERENCES organization (organization_uuid)",
            "FOREIGN KEY (document_uuid) REFERENCES document (document_uuid)",
            "FOREIGN KEY (category_uuid) REFERENCES category (category_uuid)",
            "FOREIGN KEY (stamps_uuid) REFERENCES stamps (stamps_uuid)",
            "FOREIGN KEY (override_category_uuid) REFERENCES category (category_uuid)",
            "FOREIGN KEY (created_by) REFERENCES user (user_uuid)",
            "FOREIGN KEY (updated_by) REFERENCES user (user_uuid)"
        ],
        "indexes": [
            ("document_category_organization_uuid", "CREATE INDEX IF NOT EXISTS document_category_organization_uuid ON document_category (organization_uuid)"),
            ("document_category_document_uuid", "CREATE INDEX IF NOT EXISTS document_category_document_uuid ON document_category (document_uuid)"),
            ("document_category_category_uuid", "CREATE INDEX IF NOT EXISTS document_category_category_uuid ON document_category (category_uuid)"),
            ("document_category_stamps_uuid", "CREATE INDEX IF NOT EXISTS document_category_stamps_uuid ON document_category (stamps_uuid)"),
            ("document_category_override_category_uuid", "CREATE INDEX IF NOT EXISTS document_category_override_category_uuid ON document_category (override_category_uuid)")
        ]
    }
]


TABLES_METADATA = {table["name"]: list(table["columns"].keys()) for table in TABLES}


# Define sample data inserts with UUID keys
INSERTS = [
    {
        "table": "organization",
        "columns": [
            "organization_uuid", "name", "vm_name", "vm_hash", "is_active",
            "is_automation_on", "created_datetime", "updated_datetime"
        ],
        "uuid_keys": {"organization_uuid": ["name"]},
        "data": [
            {
                "name": "Local Testing - CS",
                "vm_name": 'Camerons-MacBook-Pro.local',
                "vm_hash": derive_uuid('Camerons-MacBook-Pro.local'),
                "is_automation_on": 0
            },
            {
                "name": "Local Testing - JumpBox01",
                "vm_name": "JumpBox01",
                "vm_hash": derive_uuid('JumpBox01'),
                "is_automation_on": 0
            }
        ]
    },
    {
        "table": "user_role",
        "columns": [
            "user_role_uuid", "name", "description", "is_active",
            "created_datetime", "updated_datetime"
        ],
        "uuid_keys": {"user_role_uuid": ["name"]},
        "data": [
            {
                "name": "admin",
                "description": "Access to everything and all organizations' data/settings"
            },
            {
                "name": "editor",
                "description": "Configure automation and override categorizations within their organization"
            },
            {
                "name": "analyst",
                "description": "Read-only access to analyze document metadata and categorization within their organization"
            }
        ]
    },
    {
        "table": "user",
        "columns": [
            "user_uuid", "organization_uuid", "user_role_uuid", "username", "pwd",
            "first_name", "last_name", "email", "is_active", "created_datetime", "updated_datetime"
        ],
        "uuid_keys": {"user_uuid": ["username"]},
        "data": [
            {
                "organization_uuid": "48c049db-166d-5e42-ba31-67468cf144ae",
                "user_role_uuid": "bace0701-15e3-5144-97c5-47487d543032",
                "username": "cameron",
                "pwd": "da3ba40c-1af9-5704-8dfb-9b1571aa6ae4",
                "first_name": "Cameron",
                "last_name": "Stroup",
                "email": "cameronstroup@analytix-pros.com",
                "role_name": "admin"
            },
            {
                "organization_uuid": "48c049db-166d-5e42-ba31-67468cf144ae",
                "user_role_uuid": "bace0701-15e3-5144-97c5-47487d543032",
                "username": "bryan",
                "pwd": "9eeb22a2-420f-5945-a4de-d0a382f0eb4e",
                "first_name": "Bryan",
                "last_name": "Camaglia",
                "email": "bcamaglia@cmaanalytics.com",
                "role_name": "editor"
            }
        ]
    },
    {
        "table": "ocr_models",
        "columns": [
            "ocr_models_uuid", "name", "description", "min_storage_gb", "min_ram_gb",
            "gpu_required", "gpu_optional", "min_vram_gb", "default_language",
            "default_dpi", "max_pages", "is_active", "created_datetime", "updated_datetime"
        ],
        "uuid_keys": {"ocr_models_uuid": ["name"]},
        "data": [
            {
                "name": "Tesseract",
                "description": "Tesseract is a robust, engine-based OCR tool developed by Google, excelling at extracting text from clean, printed or typewritten documents like scanned PDFs, books, and forms. It's ideal for batch processing of high-quality scans where accuracy on structured text is key, but it struggles with handwriting, low-quality images, or complex layouts (e.g., tables). Best for archival digitization or simple text extraction without deep learning overhead.",
                "min_storage_gb": 0.5,
                "min_ram_gb": 1,
                "gpu_required": 0,
                "gpu_optional": 0,
                "min_vram_gb": 0,
                "default_language": "English",
                "default_dpi": 400,
                "max_pages": 30
            },
            {
                "name": "EasyOCR",
                "description": "EasyOCR is a ready-to-use Python library for detecting and reading text in images, supporting 80+ languages. It uses deep learning (CNN-RNN) for scene text recognition, making it suitable for real-world photos, handwritten notes, or multilingual documents like signs and receipts. GPU acceleration significantly speeds up inference (e.g., for video or large batches), but CPU mode is viable for lightweight tasks. Use for mobile apps, document automation, or noisy image processing.",
                "min_storage_gb": 1,
                "min_ram_gb": 8,
                "gpu_required": 0,
                "gpu_optional": 1,
                "min_vram_gb": 4,
                "default_language": "English",
                "default_dpi": 500,
                "max_pages": 30
            },
            {
                "name": "PaddleOCR",
                "description": "PaddleOCR is a comprehensive toolkit from Baidu for multilingual document analysis, including text detection, recognition, and layout parsing (e.g., tables, invoices). It's optimized for production-scale tasks like digitizing forms or extracting from low-resolution scans. CPU mode works for small workloads but is slow; GPU (via PaddlePaddle framework) is essential for efficiency in high-volume scenarios. Ideal for enterprise document processing, receipt automation, or embedded systems with hardware constraints.",
                "min_storage_gb": 2,
                "min_ram_gb": 4,
                "gpu_required": 0,
                "gpu_optional": 1,
                "min_vram_gb": 4,
                "default_language": "English",
                "default_dpi": 550,
                "max_pages": 30
            }
        ]
    },
    {
        "table": "llm_models",
        "columns": [
            "llm_model_uuid", "system", "name", "description", "min_ram_gb",
            "default_timeout", "gpu_required", "gpu_optional", "min_vram_gb",
            "is_vision_capable", "is_active", "created_datetime", "updated_datetime"
        ],
        "uuid_keys": {"llm_model_uuid": ["system", "name"]},
        "data": [
            {
                "name": "granite3.2-vision:latest",
                "system": "Ollama",
                "description": "Best for scanned legal PDFs with tables/forms. Extracts text and categorizes (e.g., invoice, notice) with high accuracy. Ideal for low-resource machines (4-8GB VRAM).",
                "min_ram_gb": 8,
                "default_timeout": 300,
                "gpu_required": 0,
                "gpu_optional": 1,
                "min_vram_gb": 4,
                "is_vision_capable": 1
            },
            {
                "name": "llava:7b:latest",
                "system": "Ollama",
                "description": "Excels at text recognition from scans, including handwritten mail. Classifies complex documents (e.g., disputes, proofs) with reasoning. Needs 8-16GB VRAM. 7 billion parameters",
                "min_ram_gb": 0,
                "default_timeout": 60,
                "gpu_required": 1,
                "gpu_optional": 0,
                "min_vram_gb": 8,
                "is_vision_capable": 1
            },
            {
                "name": "llava:13b:latest",
                "system": "Ollama",
                "description": "Excels at text recognition from scans, including handwritten mail. Classifies complex documents (e.g., disputes, proofs) with reasoning. Needs 8-16GB VRAM. 13 billion parameters",
                "min_ram_gb": 0,
                "default_timeout": 60,
                "gpu_required": 1,
                "gpu_optional": 0,
                "min_vram_gb": 16,
                "is_vision_capable": 1
            },
            {
                "name": "qwen2-vl:7b:latest",
                "system": "Ollama",
                "description": "Strong for multi-page forms and multilingual mail. Fast categorization of legal documents (e.g., demands, filings). Requires 8-12GB VRAM.",
                "min_ram_gb": 0,
                "default_timeout": 60,
                "gpu_required": 1,
                "gpu_optional": 0,
                "min_vram_gb": 8,
                "is_vision_capable": 1
            },
            {
                "name": "mistral:latest",
                "system": "Ollama",
                "description": "Efficient for text-based classification after OCR extraction. Ideal for clean, structured legal text (e.g., summons, notices). Runs on 4-8GB RAM.",
                "min_ram_gb": 4,
                "default_timeout": 60,
                "gpu_required": 0,
                "gpu_optional": 0,
                "min_vram_gb": 0,
                "is_vision_capable": 0
            }
        ]
    },
    {
        "table": "stamps",
        "columns": [
            "stamps_uuid", "organization_uuid", "name", "description", "keywords",
            "is_active", "created_datetime", "created_by", "updated_datetime", "updated_by"
        ],
        "uuid_keys": {"stamps_uuid": ["organization_uuid", "name"]},
        "data": [
            {"organization_uuid": "48c049db-166d-5e42-ba31-67468cf144ae", "name": "FILED", "keywords": "['filed', 'file stamped']", "description": ""},
            {"organization_uuid": "48c049db-166d-5e42-ba31-67468cf144ae", "name": "CERTIFIED", "keywords": "['certified', 'certified copy', 'certification']", "description": ""},
            {"organization_uuid": "48c049db-166d-5e42-ba31-67468cf144ae", "name": "RECORDED", "keywords": "['recorded', 'recording']", "description": ""},
            {"organization_uuid": "48c049db-166d-5e42-ba31-67468cf144ae", "name": "EXEMPLIFIED", "keywords": "['exemplified']", "description": ""},
            {"organization_uuid": "48c049db-166d-5e42-ba31-67468cf144ae", "name": "SERVED", "keywords": "['served', 'proof of service']", "description": ""},
            {"organization_uuid": "48c049db-166d-5e42-ba31-67468cf144ae", "name": "ISSUED", "keywords": "['issued', 'date of issue']", "description": ""},
            {"organization_uuid": "4f4cef4a-899e-50b9-a049-d5fbfbbcc04a", "name": "FILED", "keywords": "['filed', 'file stamped']", "description": ""},
            {"organization_uuid": "4f4cef4a-899e-50b9-a049-d5fbfbbcc04a", "name": "CERTIFIED", "keywords": "['certified', 'certified copy', 'certification']", "description": ""},
            {"organization_uuid": "4f4cef4a-899e-50b9-a049-d5fbfbbcc04a", "name": "RECORDED", "keywords": "['recorded', 'recording']", "description": ""},
            {"organization_uuid": "4f4cef4a-899e-50b9-a049-d5fbfbbcc04a", "name": "EXEMPLIFIED", "keywords": "['exemplified']", "description": ""},
            {"organization_uuid": "4f4cef4a-899e-50b9-a049-d5fbfbbcc04a", "name": "SERVED", "keywords": "['served', 'proof of service']", "description": ""},
            {"organization_uuid": "4f4cef4a-899e-50b9-a049-d5fbfbbcc04a", "name": "ISSUED", "keywords": "['issued', 'date of issue']", "description": ""}
        ]
    },
    {
        "table": "category",
        "columns": [
            "category_uuid", "parent_category_uuid", "organization_uuid", "name", "hierarchy_level",
            "use_stamps", "description", "use_keywords", "keywords", "use_llm", "high_min_threshold", "medium_min_threshold",
            "exclusion_rules", "file_rename_rules", "is_active", "created_datetime", "created_by", "updated_datetime", "updated_by"
        ],
        "uuid_keys": {"category_uuid": ["parent_category_uuid", "organization_uuid", "name"]},
        "lookup_keys": {
            "parent_category_uuid": {
                "source_table": "category",
                "source_derived_uuid": "category_uuid",
                "source_matched_columns": ["organization_uuid", "name"],
                "lookup_column_in_data": ["organization_uuid", "parent_category_name"]
            }
        },
        "data": [
            {
                "parent_category_name": None,
                "organization_uuid": "48c049db-166d-5e42-ba31-67468cf144ae",
                "name": "Garnishments",
                "hierarchy_level": 1,
                "use_stamps": 0,
                "description": "Documents related to wage or bank garnishments",
                "use_keywords": 1,
                "keywords": "['garnishment', 'garnish', 'wage', 'bank account', 'earnings']",
                "use_llm": 1,
                "high_min_threshold": 0.75,
                "medium_min_threshold": 0.50
            },
            {
                "parent_category_name": None,
                "organization_uuid": "48c049db-166d-5e42-ba31-67468cf144ae",
                "name": "Transcript of Judgments",
                "hierarchy_level": 1,
                "use_stamps": 0,
                "description": "Court transcripts of judgments",
                "use_keywords": 1,
                "keywords": "['transcript', 'judgment', 'TOJ', 'court', 'clerk']",
                "use_llm": 1,
                "high_min_threshold": 0.75,
                "medium_min_threshold": 0.50
            },
            {
                "parent_category_name": None,
                "organization_uuid": "48c049db-166d-5e42-ba31-67468cf144ae",
                "name": "Service",
                "hierarchy_level": 1,
                "use_stamps": 0,
                "description": "Service of process documents",
                "use_keywords": 1,
                "keywords": "['service', 'served', 'process server', 'certified mail', 'summons']",
                "use_llm": 1,
                "high_min_threshold": 0.75,
                "medium_min_threshold": 0.50
            },
            {
                "parent_category_name": "Garnishments",
                "organization_uuid": "48c049db-166d-5e42-ba31-67468cf144ae",
                "name": "Wage Garn",
                "hierarchy_level": 2,
                "use_stamps": 0,
                "description": "Wage garnishment documents",
                "use_keywords": 1,
                "keywords": "['wage', 'employer', 'earnings', 'payroll', 'salary']",
                "use_llm": 1,
                "high_min_threshold": 0.75,
                "medium_min_threshold": 0.50
            },
            {
                "parent_category_name": "Garnishments",
                "organization_uuid": "48c049db-166d-5e42-ba31-67468cf144ae",
                "name": "Bank Garn",
                "hierarchy_level": 2,
                "use_stamps": 0,
                "description": "Bank garnishment documents",
                "use_keywords": 1,
                "keywords": "['bank', 'account', 'financial institution', 'deposit', 'checking', 'savings']",
                "use_llm": 1,
                "high_min_threshold": 0.75,
                "medium_min_threshold": 0.50
            },
            {
                "parent_category_name": "Transcript of Judgments",
                "organization_uuid": "48c049db-166d-5e42-ba31-67468cf144ae",
                "name": "Accepted TOJ",
                "hierarchy_level": 2,
                "use_stamps": 1,
                "description": "Accepted transcript of judgment",
                "use_keywords": 1,
                "keywords": "['accepted', 'approved', 'filed', 'recorded', 'issued']",
                "use_llm": 1,
                "high_min_threshold": 0.75,
                "medium_min_threshold": 0.50
            },
            {
                "parent_category_name": "Transcript of Judgments",
                "organization_uuid": "48c049db-166d-5e42-ba31-67468cf144ae",
                "name": "Rejected TOJ",
                "hierarchy_level": 2,
                "use_stamps": 1,
                "description": "Rejected transcript of judgment",
                "use_keywords": 1,
                "keywords": "['rejected', 'denied', 'insufficient', 'incomplete']",
                "use_llm": 1,
                "high_min_threshold": 0.75,
                "medium_min_threshold": 0.50
            },
            {
                "parent_category_name": "Service",
                "organization_uuid": "48c049db-166d-5e42-ba31-67468cf144ae",
                "name": "Served",
                "hierarchy_level": 2,
                "use_stamps": 0,
                "description": "Successfully served documents",
                "use_keywords": 1,
                "keywords": "['served', 'delivered', 'receipt', 'signed', 'accepted']",
                "use_llm": 1,
                "high_min_threshold": 0.75,
                "medium_min_threshold": 0.50
            },
            {
                "parent_category_name": "Service",
                "organization_uuid": "48c049db-166d-5e42-ba31-67468cf144ae",
                "name": "Non-Served",
                "hierarchy_level": 2,
                "use_stamps": 0,
                "description": "Documents that were not successfully served",
                "use_keywords": 1,
                "keywords": "['undelivered', 'refused', 'unable to serve', 'not served', 'returned']",
                "use_llm": 1,
                "high_min_threshold": 0.75,
                "medium_min_threshold": 0.50
            }
        ]
    }
]