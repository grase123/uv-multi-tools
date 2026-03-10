"""Shared UI helpers for all CLI tools in the package.

The UI class provides a single point of control for all console output
across every tool. Both greeter and orchestrator import and use it,
ensuring consistent styling, color palette, and error formatting.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class UI:
    """Unified output interface shared across all tools.

    Usage in any tool module::

        from mytools.tools import UI

        ui = UI(app_name="greeter")
        ui.panel("Hello!", title="Greeting")
        ui.success("All done")
        ui.error("Something broke")
    """

    BORDER_STYLE = "cyan"
    TITLE_STYLE = "bold green"
    ERROR_STYLE = "bold red"
    SUCCESS_STYLE = "green"
    INFO_STYLE = "bold blue"

    def __init__(self, *, app_name: str = "mytools") -> None:
        self.app_name = app_name
        self.console = Console()

    # --- Atomic outputs -------------------------------------------------- #

    def panel(self, text: str, *, title: str = "") -> None:
        """Print *text* inside a styled Rich panel."""
        self.console.print(
            Panel(
                text,
                title=f"[{self.TITLE_STYLE}]{title}[/]" if title else None,
                border_style=self.BORDER_STYLE,
            )
        )

    def success(self, text: str) -> None:
        """Print a success message in green."""
        self.console.print(f"[{self.SUCCESS_STYLE}]{text}[/]")

    def error(self, text: str) -> None:
        """Print an error message with app name prefix in red."""
        self.console.print(f"[{self.ERROR_STYLE}]{self.app_name}: error:[/] {text}")

    def info(self, text: str) -> None:
        """Print an informational message in blue."""
        self.console.print(f"[{self.INFO_STYLE}]{self.app_name}:[/] {text}")

    # --- Table builder --------------------------------------------------- #

    def table(self, *, title: str, columns: list[tuple[str, str]]) -> Table:
        """Create a pre-styled Rich Table.

        *columns* is a list of ``(header, style)`` tuples.
        Returns the Table so the caller can add rows.
        """
        tbl = Table(title=title, show_lines=True)
        for header, style in columns:
            tbl.add_column(header, style=style)
        return tbl

    def print(self, renderable: object) -> None:
        """Proxy to ``Console.print`` for any Rich renderable."""
        self.console.print(renderable)
