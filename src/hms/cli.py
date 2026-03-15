"""HackMySkills CLI entry point."""
from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from hms import __version__

app = typer.Typer(
    name="hms",
    help="HackMySkills — spaced-repetition CLI for DevOps engineers",
    no_args_is_help=False,
)

console = Console()


def _show_dashboard() -> None:
    """Display the status dashboard."""
    from hms.init import ensure_initialized
    from hms.config import HMS_HOME
    ensure_initialized()
    content = (
        f"[bold cyan]HackMySkills v{__version__}[/bold cyan]\n\n"
        f"[dim]Data home:[/dim] {HMS_HOME}\n\n"
        "Run [bold]hms quiz[/bold] to get started."
    )
    console.print(
        Panel(
            content,
            title="[bold]HackMySkills[/bold]",
            subtitle="[dim]spaced-repetition for DevOps engineers[/dim]",
            border_style="blue",
        )
    )


@app.callback(invoke_without_command=True)
def default(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        help="Show the version and exit.",
        is_eager=True,
    ),
) -> None:
    """HackMySkills — show status dashboard when no subcommand is given."""
    if version:
        console.print(f"hms version {__version__}")
        raise typer.Exit(0)
    if ctx.invoked_subcommand is None:
        _show_dashboard()


@app.command()
def quiz(
    topic: Optional[str] = typer.Option(None, "--topic", "-t", help="Filter by topic"),
) -> None:
    """Start a focused quiz session."""
    from hms.init import ensure_initialized
    from hms import quiz as quiz_module
    ensure_initialized()
    quiz_module.run_session(topic=topic)


@app.command()
def stats() -> None:
    """Show performance statistics."""
    console.print("[yellow]Not yet implemented.[/yellow]")
    raise typer.Exit(0)


@app.command()
def generate() -> None:
    """Generate new questions via AI."""
    console.print("[yellow]Not yet implemented.[/yellow]")
    raise typer.Exit(0)


@app.command()
def daemon() -> None:
    """Manage the background interrupt daemon."""
    console.print("[yellow]Not yet implemented.[/yellow]")
    raise typer.Exit(0)


if __name__ == "__main__":
    app()
