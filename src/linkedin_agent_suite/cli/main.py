"""Complete CLI interface for LinkedIn Agent Suite."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from ..core.config import get_settings
from ..core.models import Profile
from ..core.storage.database import LocalDatabase
from ..intelligence.application.tracker import ApplicationTracker
from ..intelligence.content.service import ContentService
from ..intelligence.profile.audit import audit_profile
from ..linkedin.session.cookie_importer import CookieImporter
from .doctor import run_diagnostics

app = typer.Typer(help="LinkedIn Agent Suite Unified Control CLI")
console = Console()


@app.command()
def doctor():
    """Run real dynamic system probes."""
    console.print(run_diagnostics())


# --- SESSION COMMANDS ---
session_app = typer.Typer(help="Session management")
app.add_typer(session_app, name="session")


@session_app.command("status")
def session_status():
    settings = get_settings()
    profile_dir = settings.browser_user_data_dir
    has_files = profile_dir.exists() and any(profile_dir.iterdir())
    status_str = (
        "[green]Active[/green]" if has_files else "[yellow]No session stored[/yellow]"
    )
    console.print(f"Browser User Data Dir: {profile_dir} ({status_str})")


@session_app.command("browsers")
def session_browsers():
    browsers = CookieImporter.get_supported_browsers()
    console.print(
        f"[bold cyan]Installed browsers for cookie import:[/bold cyan] {', '.join(browsers) or 'None'}"
    )


# --- PROFILE COMMANDS ---
profile_app = typer.Typer(help="Profile operations")
app.add_typer(profile_app, name="profile")


@profile_app.command("audit")
def profile_audit(
    role: str = "agentic-ai-systems-engineer",
    file: Path | None = typer.Option(
        None, "--file", "-f", help="JSON file containing Profile snapshot"
    ),
):
    if file and file.exists():
        data = json.loads(file.read_text(encoding="utf-8"))
        profile = Profile(**data)
    else:
        profile = Profile(
            full_name="AI Systems Engineer",
            headline="Agentic Systems & Evaluation",
            about="Building dependable AI architectures.",
            skills=["Python", "RAG", "Agentic", "FastAPI"],
        )
    result = audit_profile(profile, target_role=role)
    console.print(
        f"[bold cyan]Profile Score:[/bold cyan] [bold green]{result['overall']}/100[/bold green]"
    )
    for dim in result["dimensions"]:
        console.print(f"- [bold]{dim['dimension']}[/bold]: {dim['score']}/100")


# --- POST COMMANDS ---
post_app = typer.Typer(help="Content & Posting operations")
app.add_typer(post_app, name="post")


@post_app.command("create")
def post_create(
    topic: str = typer.Option(
        "Production RAG", "--topic", help="Topic to create post for"
    ),
):
    settings = get_settings()
    db = LocalDatabase(str(settings.data_dir / "suite.db"))
    svc = ContentService(db, settings)
    draft = svc.generate_draft(topic, ["Evidence-first benchmarks"])
    console.print(f"[bold green]Draft Created:[/bold green] {draft.id}")
    console.print(f"[bold yellow]Hook:[/bold yellow] {draft.hook}")
    console.print(f"[dim]{draft.body}[/dim]")


# --- APPLICATIONS COMMANDS ---
apps_app = typer.Typer(help="Job Application Tracker")
app.add_typer(apps_app, name="applications")


@apps_app.command("list")
def apps_list():
    settings = get_settings()
    db = LocalDatabase(str(settings.data_dir / "suite.db"))
    tracker = ApplicationTracker(db)
    apps = tracker.list_applications()
    console.print(f"Total tracked applications: {len(apps)}")
    for a in apps:
        console.print(f"- {a['role']} at {a['company']} [{a['status']}]")


if __name__ == "__main__":
    app()
