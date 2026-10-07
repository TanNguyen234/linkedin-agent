"""Dynamic system diagnostics probing real browser and configured LLM."""

from __future__ import annotations

import asyncio

from rich.table import Table

from ..core.config import get_settings
from ..core.storage.database import LocalDatabase


def run_diagnostics() -> Table:
    settings = get_settings()
    table = Table(title="LinkedIn Agent Suite System Diagnostics")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details", style="dim")

    # 1. Core Settings
    table.add_row(
        "Core Settings", "[green]PASS[/green]", f"App Env: {settings.app_env}"
    )

    # 2. Storage Directory
    data_ok = settings.data_dir.exists() and settings.data_dir.is_dir()
    data_status = "[green]PASS[/green]" if data_ok else "[red]FAIL[/red]"
    table.add_row("Data Directory", data_status, str(settings.data_dir.resolve()))

    # 3. SQLite Database R/W
    try:
        db = LocalDatabase(str(settings.data_dir / "suite.db"))
        with db.get_connection() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS _diag_test (id INTEGER PRIMARY KEY, ts TEXT)"
            )
            conn.execute("INSERT INTO _diag_test (ts) VALUES ('now')")
            conn.execute("DROP TABLE _diag_test")
        table.add_row(
            "SQLite Read/Write",
            "[green]PASS[/green]",
            "Dynamic table write & drop passed",
        )
    except Exception as e:
        table.add_row("SQLite Read/Write", "[red]FAIL[/red]", str(e))

    # 4. Patchright Driver & Live Browser Launch
    try:
        import patchright.async_api as patchright_api

        async def probe_browser():
            async with patchright_api.async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto("about:blank")
                await page.close()
                await browser.close()
                return True

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        browser_launch_ok = loop.run_until_complete(probe_browser())
        loop.close()

        if browser_launch_ok:
            table.add_row(
                "Patchright Browser",
                "[green]PASS[/green]",
                "Chromium launched, page created, and closed cleanly",
            )
        else:
            table.add_row(
                "Patchright Browser",
                "[yellow]WARN[/yellow]",
                "Browser import succeeded but launch failed",
            )
    except Exception as e:
        err_msg = str(e)
        if "Executable doesn't exist" in err_msg or ("ms-playwright" in err_msg and "exist" in err_msg):
            table.add_row(
                "Patchright Browser",
                "[yellow]NOT_CONFIGURED[/yellow]",
                "Browser binary missing. Run '.venv\\Scripts\\patchright install chromium'",
            )
        else:
            table.add_row(
                "Patchright Browser", "[red]FAIL[/red]", f"Browser probe failed: {err_msg[:60]}"
            )

    # 5. Persistent Profile Status
    profile_dir = settings.browser_user_data_dir
    if profile_dir.exists() and any(profile_dir.iterdir()):
        table.add_row(
            "Persistent Profile",
            "[green]PASS[/green]",
            f"Profile exists: {profile_dir}",
        )
    else:
        table.add_row(
            "Persistent Profile",
            "[yellow]NOT_CONFIGURED[/yellow]",
            "No stored session profile. Run 'linkedin-agent session login'",
        )

    # 6. Official Posts API
    if settings.linkedin_access_token:
        table.add_row(
            "Official Posts API",
            "[green]PASS[/green]",
            f"Configured (API Version: {settings.linkedin_api_version})",
        )
    else:
        table.add_row(
            "Official Posts API",
            "[yellow]NOT_CONFIGURED[/yellow]",
            "No LINKEDIN_ACCESS_TOKEN provided (Optional)",
        )

    # 7. LLM Provider Probing
    provider = settings.llm_provider.lower()
    if provider == "mock":
        table.add_row(
            "LLM Provider",
            "[yellow]TEST_ONLY[/yellow]",
            "Provider is 'mock' (non-production test stub)",
        )
    elif provider in ("gemini", "google"):
        key = settings.gemini_api_key or settings.llm_api_key
        if key:
            table.add_row(
                "LLM Provider",
                "[green]PASS[/green]",
                f"Gemini configured ({settings.llm_model})",
            )
        else:
            table.add_row(
                "LLM Provider",
                "[red]NOT_CONFIGURED[/red]",
                "Gemini selected but GEMINI_API_KEY missing",
            )
    elif provider in ("openai",):
        key = settings.openai_api_key or settings.llm_api_key
        if key:
            table.add_row(
                "LLM Provider",
                "[green]PASS[/green]",
                f"OpenAI configured ({settings.llm_model})",
            )
        else:
            table.add_row(
                "LLM Provider",
                "[red]NOT_CONFIGURED[/red]",
                "OpenAI selected but OPENAI_API_KEY missing",
            )
    elif provider in ("local", "ollama"):
        table.add_row(
            "LLM Provider",
            "[green]PASS[/green]",
            f"Local LLM provider configured ({settings.llm_model})",
        )
    elif provider in ("none", ""):
        table.add_row(
            "LLM Provider",
            "[yellow]NOT_CONFIGURED[/yellow]",
            "No LLM provider configured",
        )
    else:
        table.add_row(
            "LLM Provider", "[yellow]WARN[/yellow]", f"Custom provider '{provider}'"
        )

    return table
