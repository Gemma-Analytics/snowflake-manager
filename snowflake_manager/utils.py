import logging
import os
from typing import Dict

from rich.console import Console
from rich.logging import RichHandler
from snowflake.connector import connect

from snowflake_manager.constants import OBJECT_TYPES


logging.basicConfig(
    level="WARN", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger(__name__)
log.setLevel("INFO")
console = Console()


def get_snowflake_cursor():
    return connect(
        user=os.getenv("PERMISSION_BOT_USER"),
        password=os.getenv("PERMISSION_BOT_PASSWORD"),
        account=os.getenv("PERMISSION_BOT_ACCOUNT"),
        warehouse=os.getenv("PERMISSION_BOT_WAREHOUSE"),
        database=os.getenv("PERMISSION_BOT_DATABASE"),
    ).cursor()


def execute_ddl(cursor, statements: dict, is_dry_run: bool) -> None:
    """Execute drop, create and alter statements in sequence for each object type.

    Args:
        cursor: Snowflake API cursor object
        statements: dict with the list of statements of each type (e.g. create, drop)
                    it assumes statements come as pairs  like "USE ROLE...; CREATE/DROP ..."
        is_dry_run: when true, skips any create or drop statement (only prints it)
    """
    for object_type in OBJECT_TYPES:
        for operation in ["drop", "create", "alter"]:
            for statement_pair in statements[object_type][operation]:
                for s in statement_pair.split(";"):
                    if s:  # Ignore empty strings
                        console.log(s)
                        if not is_dry_run:
                            cursor.execute(s)
                            console.log("Executed successfully\n")


def plural(name: str) -> str:
    return f"{name}s"


def treat_metadata_value(value):
    if isinstance(value, str):
        if value == "true":
            return True
        if value == "false":
            return False
        return value.lower()
    return value


def format_params(params: Dict) -> str:
    """Returns formated list of parameters to use as arguments in DDL statements"""

    def get_param_value_type(value: str) -> type(type):
        if not isinstance(value, str):
            value = str(value)
        if value.isdigit():
            return int
        if value.upper() in ["TRUE", "FALSE"]:
            return bool
        return str

    params_formatted = []
    templates = {
        int: "{name} = {value}",
        bool: "{name} = {value}",
        str: "{name} = '{value}'",
    }
    for name, value in params.items():
        value_type = get_param_value_type(value)
        params_formatted.append(templates[value_type].format(name=name, value=value))
    return ", ".join(params_formatted)
