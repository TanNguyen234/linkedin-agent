"""Unified CLI interface for LinkedIn Agent Suite."""
import typer
from rich.console import Console
from .doctor import run_diagnostics
from ..core.config import get_settings
from ..core.storage.database import LocalDatabase
from ..core.models import Profile
from ..intelligence.profile.audit import audit_profile
from ..intelligence.content.service import ContentService

app = typer.Typer(help="LinkedIn Agent Suite CLI")
console = Console()

@app.command()
def doctor():
    """Run real dynamic system probes."""
    console.print(run_diagnostics())

@app.command()
def session_status():
    """Inspect local browser session status."""
    settings = get_settings()
    profile_dir = settings.browser_user_data_dir
    has_files = profile_dir.exists() and any(profile_dir.iterdir())
    status_str = "[green]Profile exists[/green]" if has_files else "[yellow]No session stored[/yellow]"
    console.print(f"Browser User Data Dir: {profile_dir} ({status_str})")

@app.command()
def profile_audit(role: str = "agentic-ai-systems-engineer"):
    """Audit profile snapshot."""
    profile = Profile(
        full_name="Lead AI Engineer",
        headline="Senior AI Systems Engineer | Multi-Agent Orchestration & RAG",
        about="Building autonomous agentic workflows and production AI architectures. DM me for collaborations.",
        skills=["Python", "TypeScript", "LLM", "RAG", "Agentic", "Docker", "FastAPI"],
        custom_url="linkedin.com/in/lead-ai-engineer"
    )
    result = audit_profile(profile, target_role=role)
    console.print(f"[bold cyan]Overall Profile Score:[/bold cyan] [bold green]{result['overall']}/100[/bold green]")
    for dim in result["dimensions"]:
        console.print(f"- [bold]{dim['dimension']}[/bold]: {dim['score']}/100")

@app.command()
def post_create(topic: str = typer.Option("RAG evaluation", "--topic", help="Topic to create post for")):
    """Create a draft post for LinkedIn."""
    settings = get_settings()
    db = LocalDatabase(str(settings.data_dir / "suite.db"))
    svc = ContentService(db, settings)
    draft = svc.generate_draft(topic, ["Deterministic evaluations", "Benchmark results"])
    console.print(f"[bold green]Draft Created:[/bold green] {draft.id}")
    console.print(f"[bold yellow]Hook:[/bold yellow] {draft.hook}")
    console.print(f"[dim]{draft.body}[/dim]")

if __name__ == "__main__":
    app()
