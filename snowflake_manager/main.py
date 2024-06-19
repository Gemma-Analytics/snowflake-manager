import argparse
import logging
import subprocess
from yaml import load, Loader

from typing import FrozenSet, Dict

from rich.console import Console
from rich.logging import RichHandler

from snowflake_manager.constants import OBJECT_TYPES, DDL_ROLE
from snowflake_manager.objects import SnowflakeObject
from snowflake_manager.utils import get_snowflake_cursor, format_params, execute_ddl
from snowflake_manager.inspector import inspect_object_type
from snowflake_manager.parser import parse_object_type


all_ddl_statements = {object_type: None for object_type in OBJECT_TYPES}

drop_template = "USE ROLE {role};DROP {object_type} {name};"
create_template = "USE ROLE {role};CREATE {object_type} {name} {extra_sql};"
alter_template = "USE ROLE {role};ALTER {object_type} {name} SET {parameters};"

objects_to_ignore_in_alter = {"user": ["snowflake"]}
params_to_ignore_in_alter = {
    "user": ["password", "must_change_password"],
    "warehouse": ["initially_suspended", "statement_timeout_in_seconds"],
}


logging.basicConfig(
    level="WARN", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger(__name__)
log.setLevel("INFO")
console = Console()


def resolve_objects(
    existing_objects: FrozenSet[SnowflakeObject],
    ought_objects: FrozenSet[SnowflakeObject],
) -> Dict:
    """Prepare DROP, CREATE and ALTER statements for an object type.

    Args:
        existing_objects: Set of Snowflake objects that currently exist
        ought_objects: Set of Snowflake objects that are expected to exist

    Returns:
        ddl_statements: dict with drop, create and alter keys with lists of DDL statments
                        to be executed for the given object type
    """
    ddl_statements = {
        "drop": [],
        "create": [],
        "alter": [],
    }

    # Infer type from arguments
    object_type = list(existing_objects)[0].type

    # Check which objects to drop/create/keep
    objects_to_drop = existing_objects.difference(ought_objects)
    if object_type == "schema":  # Schemas should not be dropped
        objects_to_drop = frozenset()
    objects_to_create = ought_objects.difference(existing_objects)
    objects_to_keep = ought_objects.intersection(existing_objects)

    # Prepare CREATE/DROP statements
    ddl_statements["create"] = [
        create_template.format(
            role=DDL_ROLE,
            object_type=object_type,
            name=obj.name,
            extra_sql=format_params(obj.params),
        ).strip()
        for obj in objects_to_create
    ]
    ddl_statements["drop"] = [
        drop_template.format(role=DDL_ROLE, object_type=object_type, name=obj.name)
        for obj in objects_to_drop
    ]

    # Prepare ALTER statements
    existing_objects_to_keep = sorted(
        [obj for obj in existing_objects if obj in objects_to_keep]
    )
    ought_objects_to_keep = sorted(
        [obj for obj in ought_objects if obj in objects_to_keep]
    )

    for existing, ought in zip(existing_objects_to_keep, ought_objects_to_keep):
        assert (
            existing == ought
        )  # Leverages custom __eq__ implementation to compare name and type
        if not ought.params:
            continue
        if existing.params == ought.params:
            continue

        for p in params_to_ignore_in_alter.get(object_type, list()):
            ought.params.pop(p, None)

        ought_params_set = set(ought.params.items())
        existing_params_set = set(existing.params.items())
        params_to_alter_set = ought_params_set.difference(existing_params_set)
        if not params_to_alter_set:
            continue
        if ought.name in objects_to_ignore_in_alter.get(object_type, list()):
            continue
        ddl_statements["alter"].append(
            alter_template.format(
                role=DDL_ROLE,
                object_type=object_type,
                name=ought.name,
                parameters=format_params(dict(params_to_alter_set)),
            )
        )

    return ddl_statements


def drop_create(args):
    permifrost_spec = load(open(args.permifrost_spec_path, "r"), Loader=Loader)

    if args.dry:
        console.log(80 * "-")
        console.log("[bold]Running in [yellow]dry run mode[/yellow] (only SHOW statements are executed)[/bold]")
        console.log(80 * "-")

    console.log("START...")
    console.log("Fetching Snowflake metadata and Permifrost specification...")

    for object_type in OBJECT_TYPES:
        all_ddl_statements[object_type] = resolve_objects(
            inspect_object_type(object_type),
            parse_object_type(permifrost_spec, object_type),
        )

    console.log("Statements:\n")

    execute_ddl(get_snowflake_cursor(), all_ddl_statements, args.dry)

    console.log("\nDONE!")


def permifrost(args):
    try:
        # Call the Permifrost CLI
        result = subprocess.run(
            ['permifrost', '-vv', 'run', args.permifrost_spec_path, '--dry'],
            capture_output=True,
            text=True,
            check=True
        )

        # Forward stdout to the logger
        console.log(result.stdout)

        # Forward stderr to the logger
        if result.stderr:
            log.error(result.stderr)

    except subprocess.CalledProcessError as e:
        # Handle errors from the Permifrost CLI
        log.error(f"Permifrost command failed with exit code {e.returncode}")
        log.error(e.stderr)

def main():
    parser = argparse.ArgumentParser(
        description="Snowflake Manager - Drop, create and alter Snowflake objects and set permissions with Permifrost"
    )
    subparsers = parser.add_subparsers()

    # Drop/create functionality
    parser_drop_create = subparsers.add_parser("drop_create")
    parser_drop_create.add_argument("-p", "--permifrost_spec_path", "--filepath", required=True)
    parser_drop_create.add_argument("--dry", action="store_true")
    parser_drop_create.set_defaults(func=drop_create)

    # Permissions functionality
    parser_drop_create = subparsers.add_parser("permifrost")
    parser_drop_create.add_argument("-p", "--permifrost_spec_path", "--filepath", required=True)
    parser_drop_create.add_argument("--dry", action="store_true")
    parser_drop_create.set_defaults(func=permifrost)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
