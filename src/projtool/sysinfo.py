"""System information CLI tool.

Displays environment details: Python version, OS, platform, key paths,
and selected environment variables. Useful for debugging and support.

Uses the shared UI class from mytools.tools for consistent output styling.
"""

import os
import platform
import sys

import typer

from mytools.tools import UI

app = typer.Typer(help="Display system and environment information.")
ui = UI(app_name="sysinfo")


@app.command()
def show(
    env: bool = typer.Option(False, "--env", help="Include environment variables"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show extended details"),
) -> None:
    """Show current system and Python environment information."""
    table = ui.table(
        title="System Information",
        columns=[
            ("Property", "cyan bold"),
            ("Value", "green"),
        ],
    )

    table.add_row("Python version", sys.version.split()[0])
    table.add_row("Python executable", sys.executable)
    table.add_row("Platform", platform.platform())
    table.add_row("Architecture", platform.machine())
    table.add_row("OS", platform.system())

    if verbose:
        table.add_row("Python full version", sys.version)
        table.add_row("Prefix", sys.prefix)
        table.add_row("Base prefix", sys.base_prefix)
        venv = "Yes" if sys.prefix != sys.base_prefix else "No"
        table.add_row("In virtualenv", venv)
        table.add_row("Working directory", os.getcwd())

    ui.print(table)

    if env:
        ui.print("")
        env_table = ui.table(
            title="Environment Variables",
            columns=[
                ("Variable", "cyan bold"),
                ("Value", "green"),
            ],
        )
        interesting = ["PATH", "VIRTUAL_ENV", "HOME", "USER", "SHELL", "LANG", "EDITOR"]
        for var in interesting:
            val = os.environ.get(var)
            if val is not None:
                env_table.add_row(var, val)
        ui.print(env_table)


@app.command()
def check() -> None:
    """Quick health check — confirms the tool is working."""
    ui.success(f"sysinfo is operational (Python {sys.version.split()[0]})")
    ui.info(f"platform: {platform.platform()}")


if __name__ == "__main__":
    app()
