
TABLES = [
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
        },
        "foreign_key": [
            ("organization_uuid": "FOREIGN KEY (organization_uuid) REFERENCES organization (organization_uuid)"),
            ("user_role_uuid": "FOREIGN KEY (user_role_uuid) REFERENCES user_role (user_role_uuid)")
        ],
        "indexes": [
            ("user_organization_uuid", "CREATE INDEX IF NOT EXISTS user_organization_uuid ON user (organization_uuid)"),
            ("user_role_uuid", "CREATE INDEX IF NOT EXISTS user_role_uuid ON user (user_role_uuid)")
        ]
    }
]