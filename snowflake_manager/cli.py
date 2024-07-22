import argparse
import logging
import subprocess

from rich.console import Console
from rich.logging import RichHandler

from snowflake_manager.core import drop_create_objects
from snowflake_manager.utils import (
    run_command,
    log_dry_run_info,
    log_error_due_to_missing_object_in_snowflake,
)


logging.basicConfig(
    level="WARN", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger(__name__)
log.setLevel("INFO")
console = Console()


def drop_create(args):
    console.log("[bold][purple]Drop/create Snowflake objects[/purple] started[/bold]")
    if args.dry:
        log_dry_run_info()
    drop_create_objects(args.permifrost_spec_path, args.dry)
    console.log(
        "[bold][purple]\nDrop/create Snowflake objects[/purple] completed successfully[/bold]\n"
    )


def permifrost(args):
    console.log("[bold][purple]Permifrost[/purple] started[/bold]")
    cmd = ["permifrost", "run", args.permifrost_spec_path]

    if args.dry:
        cmd.append("--dry")
        log_dry_run_info()

    try:
        run_command(cmd)
        console.log("[bold][purple]Permifrost[/purple] completed successfully[bold]\n")
    except subprocess.CalledProcessError as exp:
        error_msg = exp.output
        if "Object does not exist" in error_msg:
            log_error_due_to_missing_object_in_snowflake(error_msg)
            raise exp
        else:
            log.error(error_msg)
            raise exp


def run(args):
    drop_create(args)
    permifrost(args)


def main():
    parser = argparse.ArgumentParser(
        description="Snowflake Manager - Drop, create and alter Snowflake objects and set permissions with Permifrost"
    )
    subparsers = parser.add_subparsers()

    # Drop/create functionality
    parser_drop_create = subparsers.add_parser("drop_create")
    parser_drop_create.add_argument(
        "-p", "--permifrost_spec_path", "--filepath", required=True
    )
    parser_drop_create.add_argument("--dry", action="store_true")
    parser_drop_create.set_defaults(func=drop_create)

    # Permifrost functionality
    parser_drop_create = subparsers.add_parser("permifrost")
    parser_drop_create.add_argument(
        "-p", "--permifrost_spec_path", "--filepath", required=True
    )
    parser_drop_create.add_argument("--dry", action="store_true")
    parser_drop_create.set_defaults(func=permifrost)

    # Run both
    parser_drop_create = subparsers.add_parser("run")
    parser_drop_create.add_argument(
        "-p", "--permifrost_spec_path", "--filepath", required=True
    )
    parser_drop_create.add_argument("--dry", action="store_true")
    parser_drop_create.set_defaults(func=run)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
