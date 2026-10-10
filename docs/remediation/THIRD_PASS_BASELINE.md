# Third-Pass Baseline Audit & Defect Inventory

**Audit Date:** October 10, 2026  
**Auditor Role:** Principal Software Engineer, Software Architect, QA Automation Engineer, Independent Code Auditor  
**Repository:** https://github.com/TanNguyen234/linkedin-agent  
**Local Working Directory:** `D:\Download\linkedin-agent-suite`  
**Base Commit:** `afc6c63e4598c1cd953099bcd63fe6bef7840785` (`main`)  
**Remediation Branch:** `fix/third-pass-verified-remediation`  
**Environment:** Windows 11, Python 3.12 (Runtime: Python 3.14.6 in `.venv`), uv, SQLite, Patchright

---

## 1. Baseline Command Execution Results

| Command | Exit Code | Result Summary | Evidence / Failure Details |
|---|---|---|---|
| `git status` | 0 | Clean working tree on `main` at `afc6c63` | Up to date with origin/main |
| `git checkout -b fix/third-pass-verified-remediation` | 0 | Switched to new remediation branch | Working branch isolated |
| `uv sync --extra dev --system-certs --frozen` | 0 | Synchronized 11 dev dependencies | Restored pytest, ruff, mypy in venv |
| `uv run ruff check .` | 1 | **44 lint errors detected** | Blind `Exception` catches (BLE001), `try-except-pass` (S110), unused variables (RUF059), bad startswith (PIE810) |
| `uv run mypy src` | 0 | 0 type errors in 67 source files | Type annotations present across src |
| `uv run pytest tests -v` | 0 | 21 passed, 1 skipped in 1.95s | Tests pass on surface but many are superficial stubs |
| `uv build --system-certs` | 0 | Successfully built sdist & wheel | Built `dist/linkedin_agent_suite-1.0.0-py3-none-any.whl` |
| `uv run linkedin-agent --help` | 0 | CLI exposes only 5 subcommands | Missing: `people`, `company`, `jobs`, `inbox`, `networking` |
| `uv run linkedin-agent doctor` | 0 | Diagnostic table rendered | Patchright browser not installed; session not configured; access token missing; LLM provider mock |

---

## 2. Independent Defect Inventory

### P0 — Critical Functional & Security Defects

#### P0-A: Official Posting Pipeline Broken Contract & Configuration
- **Evidence:** `ContentService.publish_draft()` calls `OfficialLinkedInPublisher(..., enable_posting=self.settings.enable_official_posting, ...)` but `Settings` in `src/linkedin_agent_suite/core/config.py` does not declare `enable_official_posting` (AttributeError risk if accessed directly or silently defaulted).
- **Return Type Mismatch:** `OfficialLinkedInPublisher.publish_text_post()` returns `dict[str, Any]` (`{"status": "PUBLISHED", "post_urn": ...}`), but `ContentService.publish_draft()` executes `success, res = publisher.publish_text_post(...)` expecting a 2-tuple. Unpacking a dict yields its keys (`'status'`, `'post_urn'`), causing immediate runtime failure or bogus success.
- **Expired API Version:** Default `LINKEDIN_API_VERSION` is hardcoded as `"202401"` which is expired and returns HTTP 426 on LinkedIn REST endpoints. Active version is `202609`.
- **Fragile OIDC Identity Resolution:** Member identity assumes `/v2/userinfo` `sub` directly converts to `urn:li:person:{sub}`. Pairwise OIDC subs do not match Person IDs. Must support verified explicit `LINKEDIN_AUTHOR_URN` and documented resolution with clear `IDENTITY_UNRESOLVED` error.
- **Unconfirmed Publication / Duplicates:** No deduplication or idempotency record before HTTP POST. Network timeout causes untracked duplicate posts.

#### P0-B: Application Tracker Database Schema Conflict
- **Evidence:** Migration v2 in `core/storage/migrations.py` creates table `applications` with `(id, job_id, company, title, apply_url, status, notes, created_at, updated_at)`.
- But `intelligence/application/tracker.py` executes SQL expecting `(id, company, role, url, status, fit_score, notes, date_discovered, date_applied)`.
- Running `ApplicationTracker` methods causes SQLite `OperationalError: table applications has no column named role / date_applied`.

#### P0-C: LinkedIn Write-Action Safety & Human Consent
- **Evidence:** In `messaging/service.py` and `connections/service.py`:
  - Recipient targeting relies on generic `.msg-conversation-card` or top `Message` buttons without verifying the target profile identifier or vanity URL.
  - Send verification in `messaging/service.py` checks if the first 25 characters of the sent message exist anywhere in `.msg-s-message-list__event`, matching previous messages in the same conversation!
  - Connection request does not differentiate whether a note was allowed or silently dropped.
  - Autonomous HMAC token generation allows self-approval if an agent calls approval generation and consumption in one process without real interactive human confirmation.

#### P0-D: Session Management Integrity & Missing Commands
- **Evidence:** `session status` in CLI only checks if `browser_user_data_dir` has files on disk, returning false positive `AUTHENTICATED` even when no valid LinkedIn cookies/tokens exist.
- `linkedin-agent session login` is referenced in help text and code comments but is completely missing from the CLI commands.
- `doctor` reports `Persistent Profile: PASS` merely because a directory exists.

---

### P1 — Fragile Data Extraction & Incomplete CLI Surface

#### P1-A: Fragile Read Services & Fake Fallbacks
- Fragile selectors across `profiles/service.py`, `jobs/service.py`, `people/service.py`, `companies/service.py`, `feed/service.py`.
- Silent fallback to empty arrays `[]` when selectors fail, collapsing authentication barriers, DOM changes, and zero results into the same output.
- No structured `CompletenessStatus` or missing fields diagnostics.

#### P1-B: Missing CLI Commands
- CLI only exposes `doctor`, `session`, `profile`, `post`, `applications`.
- Missing commands from specification:
  - `people search`
  - `company get`
  - `jobs search`, `jobs get`, `jobs analyze`, `jobs prepare`, `jobs saved`
  - `inbox list`, `inbox read`, `networking draft`, `networking send`
  - `session login`, `session browsers`

---

### P2 — Intelligence, Engine & Scheduler Gaps

#### P2-A: Job Ranking Heuristics
- Years of experience inferred simply from `len(experiences)`.
- Location matching is naive substring match.
- Education matching checks degree existence rather than job requirement.

#### P2-B: Application Claim Hallucination
- `prepare_application()` claims production proficiency and architectural expertise from bare skill names.
- Lacks tiered evidence grounding (`VERIFIED_PROJECT_OR_EXPERIENCE`, `PROFILE_SKILL_ONLY`, `INFERRED`, `UNSUPPORTED`).

#### P2-C: Disconnected Post Generator & Content Pipeline
- `post_generator.py` uses hardcoded string templates instead of connecting to the configured LLM providers (`GeminiProvider`, `OpenAIProvider`, `OllamaProvider`).
- Default model is `gemini-1.5-flash` instead of current production model (`gemini-2.5-flash` or `gemini-2.0-flash`).
- No Git repository evidence extraction for `post from-project`.
- Duplicate detector is not integrated into `ContentService.generate_draft()` or publishing pipeline.

#### P2-D: Incomplete Autonomous Content Scheduler
- `ContentCalendar` only records scheduled timestamps in SQLite.
- No background runner or due-post execution engine.

---

### P3 — Misleading Tests, CI & Documentation

#### P3-A: Misleading Tests
- `tests/unit/test_messaging.py` and `tests/unit/test_connections.py` only test HMAC approval tokens, not messaging or connection logic.
- `tests/regression/test_dom_extraction.py` only tests Pydantic model serialization, not DOM extraction from HTML fixtures.
- `tests/live/test_read_only_live.py` has a `pass` body when skipped.

#### P3-B: Ruff Lint Failures & Strict Typing
- 44 Ruff lint errors across the codebase.

#### P3-C: Truncated License & Stale Docs
- `LICENSE` file contains truncated placeholder text.
- Outdated API version references, missing CLI command documentation.
