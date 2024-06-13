from snowflake_manager.objects import (
    Warehouse,
    Database,
    User,
    Role,
    Schema,
)


OBJECT_TYPE_MAP = {
    "warehouse": Warehouse,
    "database": Database,
    "user": User,
    "role": Role,
    "schema": Schema,
}

OBJECT_TYPES = list(OBJECT_TYPE_MAP.keys())

DDL_ROLE = "PERMIFROST"
