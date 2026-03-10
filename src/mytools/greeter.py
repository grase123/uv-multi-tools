"""Greeter CLI tool.

Generates greeting messages. Can be used standalone
or called by other tools within the same virtual environment.

Uses the shared UI class for all console output.
"""

import json
from datetime import datetime
from enum import Enum

import typer

from mytools.tools import UI

app = typer.Typer(help="Generate greeting messages.")
ui = UI(app_name="greeter")


class Style(str, Enum):
    formal = "formal"
    casual = "casual"
    pirate = "pirate"


TEMPLATES: dict[Style, str] = {
    Style.formal: "Good day, {name}. It is {time} and we are pleased to greet you.",
    Style.casual: "Hey {name}! It's {time}, what's up?",
    Style.pirate: "Ahoy, {name}! The clock strikes {time}, ye scallywag!",
}


@app.command()
def hello(
    name: str = typer.Argument("World", help="Name to greet"),
    style: Style = typer.Option(Style.casual, help="Greeting style"),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON for machine consumption"),
) -> None:
    """Generate a greeting for NAME in the chosen style."""
    now = datetime.now().strftime("%H:%M")
    message = TEMPLATES[style].format(name=name, time=now)

    if as_json:
        # Machine-readable output for inter-tool communication
        typer.echo(json.dumps({"name": name, "style": style.value, "message": message}))
    else:
        # Human-readable rich output via shared UI
        ui.panel(message, title=f"Greeting ({style.value})")


if __name__ == "__main__":
    app()
