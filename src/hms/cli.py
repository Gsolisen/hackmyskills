"""HackMySkills CLI entry point."""
from __future__ import annotations

from pathlib import Path
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
    ensure_initialized()

    from datetime import datetime, timezone
    from hms.gamification import compute_streak_with_freeze, get_level_info, get_total_xp
    from hms.models import Card

    streak, freeze_count = compute_streak_with_freeze()
    total_xp = get_total_xp()
    level_info = get_level_info(total_xp)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    due_count = Card.select().where(Card.due.is_null(False) & (Card.due <= now)).count()

    if streak == 0 and total_xp == 0:
        content = (
            f"[bold cyan]HackMySkills v{__version__}[/bold cyan]\n\n"
            "Welcome! Run [bold]hms quiz[/bold] to begin your streak."
        )
    else:
        streak_part = f"\U0001f525 {streak} day streak" if streak > 0 else "No streak yet"
        level_part = f"Level {level_info['level']} \u00b7 {level_info['name']}"
        due_part = f"{due_count} cards due"
        headline = f"{streak_part}  \u00b7  {level_part}  \u00b7  {due_part}"
        if freeze_count > 0:
            headline += f"  (Freezes: {freeze_count})"
        content = f"{headline}\n\nRun [bold]hms quiz[/bold] to start"

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
    from hms.init import ensure_initialized
    ensure_initialized()
    _render_stats_panel()


def _render_stats_panel() -> None:
    """Build and print the HackMySkills Stats panel."""
    from datetime import datetime, timezone
    from rich.table import Table
    from hms.gamification import (
        compute_streak_with_freeze,
        format_xp_bar,
        get_level_info,
        get_total_xp,
        get_unlocked_tiers_per_topic,
    )
    from hms.models import Card

    streak, freeze_count = compute_streak_with_freeze()
    total_xp = get_total_xp()
    level_info = get_level_info(total_xp)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    due_today = Card.select().where(Card.due.is_null(False) & (Card.due <= now)).count()

    # --- Top summary lines ---
    streak_line = f"\U0001f525 {streak} days" if streak > 0 else "0 day streak"
    if freeze_count > 0:
        streak_line += f"  \u00b7  Freezes: {freeze_count}"
    level_line = f"Level {level_info['level']} \u00b7 {level_info['name']}"
    if level_info["is_max"]:
        xp_line = "Max Level \u2014 you've hacked the skills."
    else:
        bar = format_xp_bar(level_info["xp_in_level"], level_info["xp_for_level"])
        xp_line = (
            f"XP: {level_info['xp_in_level']} / {level_info['xp_for_level']}  {bar}"
        )
    due_line = f"{due_today} cards due today"

    summary = "\n".join([streak_line, level_line, xp_line, due_line])

    # --- Per-topic table ---
    unlocked = get_unlocked_tiers_per_topic()
    topics = sorted(unlocked.keys())

    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
    table.add_column("Topic")
    table.add_column("Due", justify="right")
    table.add_column("Mastery%", justify="right")
    table.add_column("Tier")

    topic_rows: list[tuple[int, str, int, str]] = []
    for topic in topics:
        topic_due = Card.select().where(
            Card.topic == topic,
            Card.due.is_null(False),
            Card.due <= now,
        ).count()
        total_cards = Card.select().where(Card.topic == topic).count()
        mastered = Card.select().where(
            Card.topic == topic, Card.state == "Review"
        ).count()
        mastery_pct = round(100 * mastered / total_cards) if total_cards > 0 else 0
        highest_tier = unlocked[topic][-1] if unlocked[topic] else "L1"
        topic_rows.append((topic_due, topic, mastery_pct, highest_tier))

    # Sort by due DESC
    topic_rows.sort(key=lambda r: r[0], reverse=True)
    for topic_due, topic, mastery_pct, highest_tier in topic_rows:
        table.add_row(topic, str(topic_due), f"{mastery_pct}%", highest_tier)

    # --- Render panel ---
    console.print(Panel(
        summary,
        title="[bold]HackMySkills Stats[/bold]",
        border_style="blue",
    ))
    if topics:
        console.print(table)


@app.command()
def interrupt() -> None:
    """Run a single-question interrupt session."""
    from hms.init import ensure_initialized
    from hms import quiz as quiz_module
    ensure_initialized()
    quiz_module.run_session(max_cards=1)


@app.command("validate-content")
def validate_content() -> None:
    """Validate all content YAML files: schema checks and duplicate detection."""
    from hms.validation import validate_content_dir

    result = validate_content_dir()

    if result.errors:
        console.print(f"\n[bold red]Schema Errors ({len(result.errors)}):[/bold red]")
        for err in result.errors:
            console.print(f"  [red]X[/red] {err.file} :: {err.question_id} -- {err.message}")

    if result.duplicates:
        console.print(f"\n[bold yellow]Duplicates ({len(result.duplicates)}):[/bold yellow]")
        for dup in result.duplicates:
            if dup.reason == "exact_id":
                console.print(f"  [yellow]![/yellow] ID '{dup.id_a}' appears in {dup.file_a} and {dup.file_b}")
            else:
                console.print(
                    f"  [yellow]![/yellow] {dup.id_a} <-> {dup.id_b}: {dup.similarity:.0%} overlap"
                    f" ({dup.file_a}, {dup.file_b})"
                )

    console.print(
        f"\n[dim]Checked {result.questions_checked} questions in {result.files_checked} files.[/dim]"
    )

    if not result.ok:
        raise typer.Exit(1)
    console.print("[green]OK[/green] All content valid.")


@app.command()
def topics() -> None:
    """List available topics with card counts and unlock status."""
    from hms.init import ensure_initialized
    ensure_initialized()

    from rich.table import Table
    from hms.gamification import get_unlocked_tiers_per_topic
    from hms.models import Card

    unlocked = get_unlocked_tiers_per_topic()
    topics_list = sorted(unlocked.keys())

    if not topics_list:
        console.print("[dim]No topics found. Add YAML files to your content directory.[/dim]")
        return

    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
    table.add_column("Topic")
    table.add_column("Cards", justify="right")
    table.add_column("Unlocked")

    for topic in topics_list:
        card_count = Card.select().where(Card.topic == topic).count()
        highest_tier = unlocked[topic][-1] if unlocked[topic] else "L1"
        table.add_row(topic, str(card_count), f"{highest_tier} unlocked")

    console.print(table)


@app.command("import")
def import_file(
    file: Path = typer.Argument(..., help="Path to a YAML question file"),
) -> None:
    """Validate and import a question file into the active bank."""
    from hms.init import ensure_initialized
    import hms.config as _cfg
    ensure_initialized()

    file = Path(file)
    if not file.exists() or file.suffix != ".yaml":
        console.print("[red]Error:[/red] File must be an existing .yaml file.")
        raise typer.Exit(1)

    # Step 1: Validate the file schema in isolation
    from hms.loader import load_questions
    try:
        questions = load_questions(file)
    except ValueError as exc:
        console.print(f"[red]Validation failed:[/red] {exc}")
        raise typer.Exit(1)

    # Step 2: Copy to content dir
    import shutil
    content_dir = _cfg.HMS_HOME / "content"
    dest = content_dir / file.name
    if dest.exists():
        console.print(f"[red]Error:[/red] {file.name} already exists in content directory.")
        raise typer.Exit(1)

    shutil.copy2(file, dest)

    # Step 3: Full validation including cross-file duplicates
    from hms.validation import validate_content_dir
    result = validate_content_dir(content_dir)
    if not result.ok:
        dest.unlink()  # rollback
        for err in result.errors:
            console.print(f"  [red]X[/red] {err.file} :: {err.question_id} -- {err.message}")
        for dup in result.duplicates:
            if dup.reason == "exact_id":
                console.print(f"  [yellow]![/yellow] ID '{dup.id_a}' appears in {dup.file_a} and {dup.file_b}")
            else:
                console.print(
                    f"  [yellow]![/yellow] {dup.id_a} <-> {dup.id_b}: {dup.similarity:.0%} overlap"
                )
        raise typer.Exit(1)

    # Step 4: Sync cards to DB
    from hms.init import _sync_cards_from_yaml
    _sync_cards_from_yaml(content_dir)

    console.print(f"[green]OK[/green] Imported {len(questions)} questions from {file.name}.")


daemon_app = typer.Typer(help="Manage the background interrupt daemon.")


@daemon_app.command()
def start() -> None:
    """Launch the daemon and register it for startup."""
    from hms.daemon.controller import DaemonController
    ctrl = DaemonController()
    ctrl.start()
    console.print("[green]Daemon started.[/green] Registered for Windows startup.")


@daemon_app.command()
def stop() -> None:
    """Stop the daemon and remove it from startup."""
    from hms.daemon.controller import DaemonController
    ctrl = DaemonController()
    was_running = ctrl.stop()
    if was_running:
        console.print("[yellow]Daemon stopped.[/yellow]")
    else:
        console.print("[dim]Daemon was not running.[/dim]")


@daemon_app.command()
def status() -> None:
    """Check whether the daemon is currently running."""
    from hms.daemon.controller import DaemonController
    ctrl = DaemonController()
    state = ctrl.status()
    if state == "running":
        console.print("[green]Daemon is running.[/green]")
    else:
        console.print("[dim]Daemon is stopped.[/dim]")


app.add_typer(daemon_app, name="daemon")


if __name__ == "__main__":
    app()
