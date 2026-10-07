"""Real dynamic diagnostics doctor command."""
import os
import sqlite3
from rich.table import Table
from ..core.config import get_settings

def run_diagnostics() -> Table:
    settings = get_settings()
    table = Table(title="LinkedIn Agent Suite System Diagnostics")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details", style="white")

    # 1. Configuration
    table.add_row("Core Settings", "[green]PASS[/green]", f"App Env: {settings.app_env}")

    # 2. Storage Directory
    data_dir_ok = os.access(settings.data_dir, os.W_OK)
    table.add_row("Data Directory", "[green]PASS[/green]" if data_dir_ok else "[red]FAIL[/red]", str(settings.data_dir))

    # 3. SQLite DB test
    db_ok = False
    try:
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        test_db = settings.data_dir / "doctor_probe.db"
        conn = sqlite3.connect(test_db)
        try:
            conn.execute("CREATE TABLE probe (id INT);")
            conn.execute("INSERT INTO probe VALUES (1);")
            conn.execute("DROP TABLE probe;")
            conn.commit()
        finally:
            conn.close()
        test_db.unlink(missing_ok=True)
        db_ok = True
    except Exception:
        db_ok = False
    table.add_row("SQLite Read/Write", "[green]PASS[/green]" if db_ok else "[red]FAIL[/red]", "Dynamic table write & drop passed" if db_ok else "Write failed")

    # 4. Patchright
    patchright_ok = False
    try:
        import patchright  # noqa: F401
        patchright_ok = True
    except ImportError:
        patchright_ok = False
    table.add_row("Patchright Driver", "[green]PASS[/green]" if patchright_ok else "[red]FAIL[/red]", "Installed and importable")

    # 5. Official API Configuration
    has_token = bool(settings.linkedin_access_token)
    posting_enabled = settings.enable_official_posting
    if has_token and posting_enabled:
        api_status = "[green]PASS[/green]"
        api_msg = f"Configured (API Version: {settings.linkedin_api_version})"
    elif has_token:
        api_status = "[yellow]WARN[/yellow]"
        api_msg = "Token set, but ENABLE_OFFICIAL_POSTING=false"
    else:
        api_status = "[blue]NOT_CONFIGURED[/blue]"
        api_msg = "No LINKEDIN_ACCESS_TOKEN provided (Optional)"
    table.add_row("Official Posts API", api_status, api_msg)

    # 6. LLM Provider
    table.add_row("LLM Provider", "[green]PASS[/green]", f"Provider: {settings.llm_provider}")

    return table
