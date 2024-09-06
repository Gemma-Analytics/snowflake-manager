import logging
import os
import re
import subprocess
import textwrap
from typing import Dict

from rich.console import Console
from rich.logging import RichHandler
from snowflake.connector import connect


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


def run_command(command):
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    # Continuously read and print output
    while True:
        output = process.stdout.readline()
        if output == "" and process.poll() is not None:
            break
        if output:
            console.log(output.strip())

    # Check for errors
    output, errs = process.communicate()
    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, command, errs)
    return output, errs


def log_dry_run_info():
    console.log(20 * "-")
    console.log("[bold]Executing in [yellow]dry run mode[/yellow][/bold]")
    console.log(20 * "-")
