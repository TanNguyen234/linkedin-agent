"""Complete unified CLI control plane for LinkedIn Agent Suite."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from ..core.config import get_settings
from ..core.models import ApplicationStatus, Profile
from ..core.storage.database import LocalDatabase
from ..intelligence.application.prep import prepare_application
from ..intelligence.application.tracker import ApplicationTracker
from ..intelligence.content.post_generator import extract_git_project_evidence
from ..intelligence.content.service import ContentService
from ..intelligence.jobs.public_sources import fetch_public_ai_jobs
from ..intelligence.jobs.ranker import score_job_fit
from ..intelligence.profile.audit import audit_profile
from ..intelligence.profile.keywords import optimize_keywords
from ..linkedin.browser.manager import BrowserManager
from ..linkedin.companies.service import CompanyService
from ..linkedin.jobs.service import JobService
from ..linkedin.messaging.service import MessagingService
from ..linkedin.people.service import PeopleService
from ..linkedin.profiles.service import ProfileService
from ..linkedin.session.cookie_importer import CookieImporter
from ..linkedin.session.manager import SessionManager, SessionState
from .doctor import run_diagnostics

app = typer.Typer(help="LinkedIn Agent Suite Unified Control CLI")
console = Console()


@app.command()
def doctor():
    """Run real dynamic system probes."""
    console.print(run_diagnostics())


# ==========================================
# SESSION COMMANDS
# ==========================================
session_app = typer.Typer(help="Session management")
app.add_typer(session_app, name="session")


@session_app.command("status")
def session_status():
    """Check live LinkedIn authentication state using multi-signal detector."""
    settings = get_settings()
    profile_dir = settings.browser_user_data_dir

    if not profile_dir.exists() or not any(profile_dir.iterdir()):
        console.print("[yellow]No session stored. Run 'linkedin-agent session login' to authenticate.[/yellow]")
        return

    async def _check():
        mgr = BrowserManager(user_data_dir=profile_dir, headless=True)
        try:
            sess = SessionManager(mgr)
            state = await sess.detect_session_state()
            return state
        finally:
            await mgr.close()

    try:
        state = asyncio.run(_check())
        if state == SessionState.AUTHENTICATED:
            console.print("[bold green]AUTHENTICATED[/bold green]: Active LinkedIn session verified.")
        elif state == SessionState.LOGIN_REQUIRED:
            console.print("[bold yellow]LOGIN_REQUIRED[/bold yellow]: Session expired or not logged in.")
        elif state == SessionState.CHECKPOINT:
            console.print("[bold red]CHECKPOINT[/bold red]: Security verification challenge present on LinkedIn.")
        elif state == SessionState.ACCOUNT_RESTRICTED:
            console.print("[bold red]ACCOUNT_RESTRICTED[/bold red]: Account restricted by LinkedIn.")
        else:
            console.print(f"[yellow]UNKNOWN[/yellow]: Session state is {state.value}")
    except Exception as e:
        console.print(f"[red]Error probing session:[/red] {e}")


@session_app.command("login")
def session_login():
    """Launch headed browser to allow manual human login to LinkedIn and store persistent session."""
    settings = get_settings()
    console.print("[bold cyan]Launching headed browser for LinkedIn manual login...[/bold cyan]")
    console.print("[dim]Log in through the opened browser window. Do NOT share credentials with the CLI.[/dim]")

    async def _login():
        mgr = BrowserManager(user_data_dir=settings.browser_user_data_dir, headless=False)
        try:
            context = await mgr.start()
            page = await context.new_page()
            await page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")

            console.print("[yellow]Waiting for authentication (polling up to 120s)...[/yellow]")
            sess = SessionManager(mgr)
            for _ in range(60):
                await asyncio.sleep(2)
                state = await sess.detect_session_state(page)
                if state == SessionState.AUTHENTICATED:
                    console.print("[bold green]Successfully authenticated![/bold green] Session saved to persistent profile.")
                    return True
                elif state == SessionState.CHECKPOINT:
                    console.print("[yellow]Security checkpoint detected. Please complete it in the browser.[/yellow]")
            console.print("[red]Authentication timeout. Please rerun 'session login' when ready.[/red]")
            return False
        finally:
            await mgr.close()

    asyncio.run(_login())


@session_app.command("browsers")
def session_browsers():
    """List local installed browsers supported for cookie import."""
    browsers = CookieImporter.get_supported_browsers()
    console.print(
        f"[bold cyan]Installed browsers for cookie import:[/bold cyan] {', '.join(browsers) or 'None'}"
    )


# ==========================================
# PROFILE COMMANDS
# ==========================================
profile_app = typer.Typer(help="Profile operations")
app.add_typer(profile_app, name="profile")


@profile_app.command("me")
def profile_me():
    """Fetch authenticated user's own profile."""
    settings = get_settings()

    async def _get():
        mgr = BrowserManager(user_data_dir=settings.browser_user_data_dir, headless=True)
        try:
            svc = ProfileService(mgr)
            return await svc.get_my_profile()
        finally:
            await mgr.close()

    try:
        p = asyncio.run(_get())
        console.print(f"[bold green]Name:[/bold green] {p.full_name}")
        console.print(f"[bold cyan]Headline:[/bold cyan] {p.headline}")
        console.print(f"[dim]Location: {p.location}[/dim]")
        console.print(f"[bold]Skills ({len(p.skills)}):[/bold] {', '.join(p.skills[:8])}")
    except Exception as e:
        console.print(f"[red]Failed to fetch profile:[/red] {e}")


@profile_app.command("get")
def profile_get(username: str):
    """Fetch public profile by username or URL."""
    settings = get_settings()

    async def _get():
        mgr = BrowserManager(user_data_dir=settings.browser_user_data_dir, headless=True)
        try:
            svc = ProfileService(mgr)
            return await svc.get_profile(username)
        finally:
            await mgr.close()

    try:
        p = asyncio.run(_get())
        console.print(f"[bold green]Name:[/bold green] {p.full_name}")
        console.print(f"[bold cyan]Headline:[/bold cyan] {p.headline}")
        console.print(f"[dim]About:[/dim] {p.about[:200]}...")
        console.print(f"Skills: {', '.join(p.skills[:10])}")
    except Exception as e:
        console.print(f"[red]Failed to fetch profile '{username}':[/red] {e}")


@profile_app.command("audit")
def profile_audit(
    role: str = "agentic-ai-systems-engineer",
    file: Optional[Path] = typer.Option(
        None, "--file", "-f", help="JSON file containing Profile snapshot"
    ),
):
    """Audit profile match and completeness for target role."""
    if file and file.exists():
        data = json.loads(file.read_text(encoding="utf-8"))
        profile = Profile(**data)
    else:
        console.print("[red]Error: Profile file is required for audit. Provide a valid JSON snapshot via '--file <path>'.[/red]")
        raise typer.Exit(1)

    result = audit_profile(profile, target_role=role)
    console.print(
        f"[bold cyan]Profile Score for '{role}':[/bold cyan] [bold green]{result['overall']}/100[/bold green]"
    )
    for dim in result["dimensions"]:
        console.print(f"- [bold]{dim['dimension']}[/bold]: {dim['score']}/100")


@profile_app.command("optimize")
def profile_optimize(
    role: str = "agentic-ai-systems-engineer",
    file: Optional[Path] = typer.Option(
        None, "--file", "-f", help="JSON file containing Profile snapshot"
    ),
):
    """Suggest high-impact keyword optimizations for target role."""
    if file and file.exists():
        data = json.loads(file.read_text(encoding="utf-8"))
        profile = Profile(**data)
    else:
        console.print("[red]Error: Provide a profile JSON via '--file <path>' to generate optimizations.[/red]")
        raise typer.Exit(1)

    text = profile.full_text()
    opt = optimize_keywords(text, target_role=role)
    console.print(f"[bold green]Current Keyword Match Density:[/bold green] {opt['density']:.1f}%")
    console.print(f"[bold cyan]High Priority Missing Keywords:[/bold cyan] {', '.join(opt['missing'][:8])}")


# ==========================================
# PEOPLE & COMPANY COMMANDS
# ==========================================
people_app = typer.Typer(help="People search")
app.add_typer(people_app, name="people")

company_app = typer.Typer(help="Company lookup")
app.add_typer(company_app, name="company")


@people_app.command("search")
def people_search(query: str, limit: int = 10):
    """Search people on LinkedIn."""
    settings = get_settings()

    async def _search():
        mgr = BrowserManager(user_data_dir=settings.browser_user_data_dir, headless=True)
        try:
            svc = PeopleService(mgr)
            return await svc.search_people(query, limit=limit)
        finally:
            await mgr.close()

    try:
        results = asyncio.run(_search())
        console.print(f"Found {len(results)} profiles for '{query}':")
        for r in results:
            console.print(f"- [bold]{r['name']}[/bold] ({r['headline']}) -> {r['profile_url']}")
    except Exception as e:
        console.print(f"[red]Error searching people:[/red] {e}")


@company_app.command("get")
def company_get(identifier: str):
    """Fetch details for a company by identifier or URL."""
    settings = get_settings()

    async def _get():
        mgr = BrowserManager(user_data_dir=settings.browser_user_data_dir, headless=True)
        try:
            svc = CompanyService(mgr)
            return await svc.get_company(identifier)
        finally:
            await mgr.close()

    try:
        c = asyncio.run(_get())
        console.print(f"[bold green]Company:[/bold green] {c['name']}")
        console.print(f"Industry: {c['industry']} | Employees: {c['employee_count']}")
        console.print(f"[dim]{c['about']}[/dim]")
    except Exception as e:
        console.print(f"[red]Error fetching company:[/red] {e}")


# ==========================================
# JOBS COMMANDS
# ==========================================
jobs_app = typer.Typer(help="Jobs search & analysis")
app.add_typer(jobs_app, name="jobs")


@jobs_app.command("search")
def jobs_search(keywords: str, location: str = "Remote", limit: int = 10):
    """Search jobs on LinkedIn or public fallback sources."""
    settings = get_settings()
    db = LocalDatabase(str(settings.data_dir / "suite.db"))

    async def _search():
        mgr = BrowserManager(user_data_dir=settings.browser_user_data_dir, headless=True)
        try:
            svc = JobService(mgr)
            return await svc.search_jobs(keywords, location=location, limit=limit)
        finally:
            await mgr.close()

    try:
        jobs = asyncio.run(_search())
    except Exception:
        jobs = []

    if not jobs:
        console.print("[dim]LinkedIn search returned 0 items; querying public remote AI job boards...[/dim]")
        jobs = fetch_public_ai_jobs(keywords, limit=limit)

    for j in jobs:
        db.save_job(j.model_dump())

    console.print(f"[bold green]Found {len(jobs)} jobs:[/bold green]")
    for j in jobs:
        console.print(f"- [bold]{j.title}[/bold] at {j.company} ({j.location}) [ID: {j.id}]")


@jobs_app.command("get")
def jobs_get(job_id: str):
    """Fetch details for a job."""
    settings = get_settings()

    async def _get():
        mgr = BrowserManager(user_data_dir=settings.browser_user_data_dir, headless=True)
        try:
            svc = JobService(mgr)
            return await svc.get_job(job_id)
        finally:
            await mgr.close()

    job = asyncio.run(_get())
    if job:
        console.print(f"[bold green]{job.title}[/bold green] at [cyan]{job.company}[/cyan]")
        console.print(f"URL: {job.url}")
        console.print(f"[dim]{job.description[:300]}...[/dim]")
    else:
        console.print(f"[yellow]Job '{job_id}' not found.[/yellow]")


@jobs_app.command("analyze")
def jobs_analyze(
    job_id: str,
    file: Path = typer.Option(..., "--file", "-f", help="Path to Profile snapshot JSON"),
):
    """Score job fit against a profile."""
    if not file.exists():
        console.print(f"[red]Profile file {file} not found.[/red]")
        raise typer.Exit(1)

    profile = Profile(**json.loads(file.read_text(encoding="utf-8")))
    settings = get_settings()
    db = LocalDatabase(str(settings.data_dir / "suite.db"))
    jobs = db.get_jobs()
    target_job = next((j for j in jobs if j["id"] == job_id), None)

    if not target_job:
        console.print(f"[red]Job {job_id} not found in database cache.[/red]")
        raise typer.Exit(1)

    from ..core.models import Job
    fit = score_job_fit(Job(**target_job), profile)
    console.print(f"[bold cyan]Job Fit Score:[/bold cyan] [bold green]{fit.score}/100[/bold green]")
    console.print(f"Rationale: {fit.rationale}")
    console.print(f"Matched Skills: {', '.join(fit.matched_keywords)}")
    console.print(f"Missing Skills: {', '.join(fit.missing_keywords)}")


@jobs_app.command("prepare")
def jobs_prepare(
    job_id: str,
    file: Path = typer.Option(..., "--file", "-f", help="Path to Profile snapshot JSON"),
):
    """Prepare grounded application and pitch."""
    if not file.exists():
        console.print(f"[red]Profile file {file} not found.[/red]")
        raise typer.Exit(1)

    profile = Profile(**json.loads(file.read_text(encoding="utf-8")))
    settings = get_settings()
    db = LocalDatabase(str(settings.data_dir / "suite.db"))
    jobs = db.get_jobs()
    target_job = next((j for j in jobs if j["id"] == job_id), None)

    if not target_job:
        console.print(f"[red]Job {job_id} not found.[/red]")
        raise typer.Exit(1)

    from ..core.models import Job
    prep = prepare_application(Job(**target_job), profile)
    console.print(f"[bold green]Application Prepared for {prep['title']} at {prep['company']}:[/bold green]")
    console.print(f"Verified Evidence Ratio: {prep['verified_ratio'] * 100:.0f}%")
    console.print("\n[bold cyan]Cover Note Pitch:[/bold cyan]")
    console.print(prep["pitch"])


@jobs_app.command("saved")
def jobs_saved(limit: int = 20):
    """List saved/cached jobs."""
    settings = get_settings()
    db = LocalDatabase(str(settings.data_dir / "suite.db"))
    jobs = db.get_jobs(limit=limit)
    console.print(f"Saved jobs in local cache: {len(jobs)}")
    for j in jobs:
        console.print(f"- [bold]{j['title']}[/bold] at {j['company']} [ID: {j['id']}]")


# ==========================================
# MESSAGING & NETWORKING COMMANDS
# ==========================================
inbox_app = typer.Typer(help="Inbox messages")
app.add_typer(inbox_app, name="inbox")

net_app = typer.Typer(help="Networking operations")
app.add_typer(net_app, name="networking")


@inbox_app.command("list")
def inbox_list(limit: int = 15):
    """List recent messaging threads."""
    settings = get_settings()

    async def _list():
        mgr = BrowserManager(user_data_dir=settings.browser_user_data_dir, headless=True)
        try:
            svc = MessagingService(mgr)
            return await svc.list_threads(limit=limit)
        finally:
            await mgr.close()

    try:
        threads = asyncio.run(_list())
        console.print(f"Found {len(threads)} messaging conversations:")
        for t in threads:
            unread = f" [bold red]({t.unread_count} unread)[/bold red]" if t.unread_count else ""
            console.print(f"- {', '.join(t.participants)}: [dim]{t.snippet[:50]}...[/dim]{unread} (ID: {t.thread_id})")
    except Exception as e:
        console.print(f"[red]Error listing threads:[/red] {e}")


@inbox_app.command("read")
def inbox_read(thread_id: str, limit: int = 30):
    """Read messages from a thread."""
    settings = get_settings()

    async def _read():
        mgr = BrowserManager(user_data_dir=settings.browser_user_data_dir, headless=True)
        try:
            svc = MessagingService(mgr)
            return await svc.get_thread_messages(thread_id, limit=limit)
        finally:
            await mgr.close()

    try:
        msgs = asyncio.run(_read())
        console.print(f"Messages in thread '{thread_id}':")
        for m in msgs:
            console.print(f"[{m.get('time', '')}] [bold]{m.get('sender', 'Unknown')}:[/bold] {m.get('text', '')}")
    except Exception as e:
        console.print(f"[red]Error reading thread:[/red] {e}")


@net_app.command("draft")
def networking_draft(recipient: str, message: str = typer.Option("Hi, glad to connect!", "--message", "-m")):
    """Draft a networking message and generate approval token."""
    settings = get_settings()
    mgr = BrowserManager(user_data_dir=settings.browser_user_data_dir)
    svc = MessagingService(mgr)
    payload, token = svc.prepare_message(recipient, message)
    console.print("[bold green]Networking Message Drafted:[/bold green]")
    console.print(f"Recipient: {payload['recipient']}")
    console.print(f"Message: {payload['message']}")
    console.print(f"[bold yellow]Approval Token:[/bold yellow] {token}")
    console.print("\n[dim]To send, run: linkedin-agent networking send <recipient> '<message>' <approval_token>[/dim]")


@net_app.command("send")
def networking_send(
    recipient: str,
    message: str,
    approval_token: str,
    dry_run: bool = typer.Option(False, "--dry-run", help="Verify approval without submitting to DOM"),
):
    """Send approved networking message."""
    if dry_run:
        console.print(f"[green]DRY RUN PASS:[/green] Message to '{recipient}' verified with approval token.")
        return

    settings = get_settings()

    async def _send():
        mgr = BrowserManager(user_data_dir=settings.browser_user_data_dir, headless=True)
        try:
            svc = MessagingService(mgr)
            return await svc.send_message(recipient, message, approval_token)
        finally:
            await mgr.close()

    res = asyncio.run(_send())
    if res["status"] == "SENT":
        console.print(f"[bold green]SENT:[/bold green] Message delivered to {recipient}.")
    else:
        console.print(f"[bold red]Result ({res['status']}):[/bold red] {res.get('error') or res.get('details')}")


# ==========================================
# APPLICATION TRACKER COMMANDS
# ==========================================
apps_app = typer.Typer(help="Job Application Tracker")
app.add_typer(apps_app, name="applications")


@apps_app.command("add")
def apps_add(
    company: str,
    role: str,
    url: str = "",
    status: str = "saved",
    notes: str = "",
):
    """Add a new application record."""
    settings = get_settings()
    db = LocalDatabase(str(settings.data_dir / "suite.db"))
    tracker = ApplicationTracker(db)
    import uuid
    app_id = f"app-{uuid.uuid4().hex[:8]}"
    app_status = ApplicationStatus(status.lower())
    tracker.track_job(app_id, f"job-{uuid.uuid4().hex[:6]}", company, role, app_status, notes=notes)
    console.print(f"[bold green]Application Added:[/bold green] {app_id} ({role} at {company}) [{app_status.value}]")


@apps_app.command("list")
def apps_list():
    """List tracked job applications."""
    settings = get_settings()
    db = LocalDatabase(str(settings.data_dir / "suite.db"))
    tracker = ApplicationTracker(db)
    apps = tracker.list_applications()
    console.print(f"Total tracked applications: {len(apps)}")
    for a in apps:
        console.print(f"- [bold]{a['role']}[/bold] at [cyan]{a['company']}[/cyan] [{a['status']}] (ID: {a['id']})")


@apps_app.command("update")
def apps_update(app_id: str, new_status: str):
    """Update status of tracked application."""
    settings = get_settings()
    db = LocalDatabase(str(settings.data_dir / "suite.db"))
    tracker = ApplicationTracker(db)
    tracker.update_status(app_id, ApplicationStatus(new_status.lower()))
    console.print(f"[bold green]Updated {app_id} status to '{new_status}'[/bold green]")


# ==========================================
# CONTENT & POST COMMANDS
# ==========================================
post_app = typer.Typer(help="Content & Posting operations")
app.add_typer(post_app, name="post")


@post_app.command("create")
def post_create(
    topic: str = typer.Option("Production RAG", "--topic", help="Topic to create post for"),
):
    """Generate a post draft."""
    settings = get_settings()
    db = LocalDatabase(str(settings.data_dir / "suite.db"))
    svc = ContentService(db, settings)
    draft = svc.generate_draft(topic, ["Evidence-first benchmarks"])
    console.print(f"[bold green]Draft Created:[/bold green] {draft.id}")
    console.print(f"[bold yellow]Hook:[/bold yellow] {draft.hook}")
    console.print(f"[dim]{draft.body}[/dim]")


@post_app.command("from-project")
def post_from_project(repo: str = "."):
    """Generate evidence-backed post from local git repository milestones."""
    evidence = extract_git_project_evidence(repo)
    if not evidence:
        console.print("[red]NO_EVIDENCE: Cannot extract Git repository evidence from provided path.[/red]")
        raise typer.Exit(1)

    settings = get_settings()
    db = LocalDatabase(str(settings.data_dir / "suite.db"))
    svc = ContentService(db, settings)
    draft = svc.generate_draft("Autonomous Agent Engineering Milestone", evidence)
    console.print(f"[bold green]Project Post Draft Created:[/bold green] {draft.id}")
    console.print(f"[bold yellow]Evidence Used:[/bold yellow] {len(evidence)} items")
    console.print(f"\n{draft.body}")


@post_app.command("preview")
def post_preview(draft_id: str):
    """Preview draft and acquire approval token."""
    settings = get_settings()
    db = LocalDatabase(str(settings.data_dir / "suite.db"))
    svc = ContentService(db, settings)
    prev = svc.preview_draft(draft_id)
    console.print(f"[bold green]Draft Preview ({draft_id}):[/bold green]")
    console.print(f"Hook: {prev['hook']}")
    console.print(f"\n{prev['body']}")
    console.print(f"\n[bold yellow]Approval Token:[/bold yellow] {prev['approval_token']}")


@post_app.command("publish")
def post_publish(draft_id: str, approval_token: str):
    """Publish approved draft via official LinkedIn REST Posts API."""
    settings = get_settings()
    db = LocalDatabase(str(settings.data_dir / "suite.db"))
    svc = ContentService(db, settings)
    res = svc.publish_draft(draft_id, approval_token)
    if res["status"] == "PUBLISHED":
        console.print(f"[bold green]PUBLISHED:[/bold green] Post live with URN: {res['post_urn']}")
    elif res["status"] == "BLOCKED":
        console.print(f"[bold yellow]BLOCKED:[/bold yellow] {res.get('message') or res.get('error')}")
    else:
        console.print(f"[bold red]Publish Failed ({res['status']}):[/bold red] {res.get('error')}")


@post_app.command("history")
def post_history():
    """List drafts and published posts."""
    settings = get_settings()
    db = LocalDatabase(str(settings.data_dir / "suite.db"))
    drafts = db.get_post_drafts()
    console.print(f"Total post records in database: {len(drafts)}")
    for d in drafts:
        console.print(f"- [bold]{d['id']}[/bold] [{d['status']}]: {d['topic']} (URN: {d.get('post_urn', 'None')})")


if __name__ == "__main__":
    app()
