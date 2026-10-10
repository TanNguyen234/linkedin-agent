# Remaining Blockers & Next Actions

**Date:** October 10, 2026  
**Branch:** `fix/third-pass-verified-remediation`

---

## 1. External & Environmental Prerequisites

1. **LinkedIn Live Credentials:**
   - Real write actions (`publish`, `send_message`, `connect`) and live API tests require `LINKEDIN_ACCESS_TOKEN` and user consent. These remain strictly gated behind human configuration.
2. **Patchright Chromium Binary:**
   - On this machine, run `.venv\Scripts\patchright install chromium` to enable headed manual login via `session login` and live browser extraction.

## 2. In-Progress Roadmap
- Additional CLI command wrappers (`people search`, `company get`, `jobs search`, `inbox list`, `networking draft`) to expose all underlying services directly on the Typer CLI root.
- Background execution runner for the ContentCalendar SQLite scheduler.
