"""Orchestrator CLI tool.

Demonstrates calling another tool (greeter) from the same package
via subprocess. Both tools are visible only inside the venv.

Uses the shared UI class for all console output.
"""

import json
import shutil
import subprocess
import sys

import typer

from mytools.tools import UI

app = typer.Typer(help="Orchestrate calls to the greeter tool.")
ui = UI(app_name="orchestrator")


def _find_greeter() -> str:
    """Locate the greeter executable inside the current venv."""
    path = shutil.which("greeter")
    if path is None:
        ui.error("'greeter' not found in PATH. Is the package installed?")
        raise typer.Exit(code=1)
    return path


def _call_greeter(greeter: str, name: str, style: str) -> dict:
    """Run greeter as a subprocess and parse its JSON output."""
    result = subprocess.run(
        [greeter, name, "--style", style, "--json"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        ui.error(f"greeter failed: {result.stderr.strip()}")
        raise typer.Exit(code=1)
    return json.loads(result.stdout)


@app.command()
def greet_all(
    names: list[str] = typer.Argument(..., help="One or more names to greet"),
    style: str = typer.Option("casual", help="Greeting style (formal / casual / pirate)"),
) -> None:
    """Call the greeter tool for each NAME and display a summary table."""
    greeter = _find_greeter()

    table = ui.table(
        title="Orchestrator Results",
        columns=[
            ("#", "dim"),
            ("Name", "cyan bold"),
            ("Style", "magenta"),
            ("Message", "green"),
        ],
    )

    for idx, name in enumerate(names, start=1):
        data = _call_greeter(greeter, name, style)
        table.add_row(str(idx), data["name"], data["style"], data["message"])

    ui.print("")
    ui.print(table)


@app.command()
def check() -> None:
    """Verify that the greeter tool is reachable inside the venv."""
    greeter = _find_greeter()
    ui.success(f"greeter found at: {greeter}")
    ui.info(f"python: {sys.executable}")


if __name__ == "__main__":
    app()
